from typing import Tuple, NewType, Awaitable, Callable, AsyncGenerator
from re import compile
from utils import extract, search, ExtractException, extract_pipeline
from classifier import Classifier
import re


__all__ = (
    'Polyglot',
)


MatchPosition = NewType("MatchPosition", Awaitable[Tuple])


MAX_READ_SIZE = 2 ** 16


MULTI_LINE_COMMENTS = (
    (compile(r'/\*'), compile(r'\*/')),
    (compile(r'<!--'), compile(r'-->')),
    (compile(r'{-'), compile(r'-}')),
    (compile(r'"""'), compile(r'"""')),
    (compile(r"'''"), compile(r"'''")),
)


REGEX_START_SINGLE_LINE_COMMENT = compile(r'\s*//|\s*\#|\s*%')
REGEX_SHEBANG = compile(r'^#!.+')
REGEX_BOL = compile(r'\n|\Z')
REGEX_DOUBLE_QUOTE = compile(r'"')
REGEX_SINGLE_QUOTE = compile(r"'")
REGEX_PRIME_QUOTE = compile(r"`")
REGEX_DOUBLE_END_QUOTE = compile(r'[^\\]?"')
REGEX_SINGLE_END_QUOTE = compile(r"[^\\]?'")
REGEX_PRIME_END_QUOTE = compile(r"[^\\]`")
REGEX_NUMBER_LITERALS = compile(r'(0x)?\d(\d|\.)*')
REGEX_SGML = compile(r'<[^\s<>][^<>]*>')
REGEX_COMMON_PUNCTUATION = compile(r';|\{|\}|\(|\)|\[|\]|\,|\?|\!|\$|\\')
REGEX_REGULAR_TOKEN = compile(r'[\w\.@#\/\*]+')
REGEX_COMMON_OPERATORS = compile(r'<<?|\+|\-|\*|\/|%|&&?|\|\|?|\=|\:\=|\:|\>|\^\=|\^|\!\=\=|\=\=|\!\=')
REGEX_EMIT_START_TOKEN = compile(r'<\/?[^\s>]+')
REGEX_EMIT_TRAILING = compile(r'\w+=')
REGEX_EMIT_WORD = compile(r'\w+')
REGEX_EMIT_END_TAG = compile('>')
REGEX_SPACE = compile('\s+')
REGEX_SHEBANG_FULL = compile(r'^#!\s*\S+')
REGEX_SHEBANG_WHITESPACE = compile(r'\s+')
REGEX_SHEBANG_NON_WHITESPACE = compile(r'\S+')
REGEX_SGML_WORD = compile(r'(\w+)=(\S+)')


def parse_shebang(s: str) -> str:
    """repos
    extract token from shebang like `#!/bin/sh`
    https://en.wikipedia.org/wiki/Shebang_(Unix)
    :param s: shebang
    :return: shebang token
    """
    script = s
    try:
        match = extract(s, REGEX_SHEBANG_FULL)
        script = match.group().split('/')[-1]
        pos = match.end()
        match = extract(s, REGEX_SHEBANG_WHITESPACE, pos=pos)
        pos = match.end()
        match = extract(s, REGEX_SHEBANG_NON_WHITESPACE, pos=pos)
        return extract(match.group(), compile(r'[^\d]+')).group(0)
    except ExtractException as e:
        return script


def extract_sgml_tokens(s: str) -> AsyncGenerator:
    """
    extract data from tags like <a href="">
    :param s: string data
    :return: list of clean tokens
    """
    return extract_pipeline(SGML_PIPELINE, s)


async def _extract_sgml_tag(s: str) -> AsyncGenerator:
    async for a in extract_pipeline(SGML_TAG_PIPELINE, s):
        yield a


async def extract_sgml_start(s: str, pos: int) -> MatchPosition:
    match = extract(s, REGEX_EMIT_START_TOKEN, pos=pos)
    return "{}>".format(match.group()), match.end()


async def extract_shebang(s: str, pos: int) -> MatchPosition:
    match = extract(s, REGEX_SHEBANG, pos=pos)
    return 'SHEBANG#!{}'.format(parse_shebang(match.group())), match.end()


async def extract_sgml(s: str, pos: int) -> MatchPosition:
    match = extract(s, REGEX_SGML, pos=pos)
    return extract_sgml_tokens(match.group()), match.end()


async def extract_sgml_tag(s: str, pos: int) -> MatchPosition:
    match = extract(s, REGEX_SGML_WORD, pos=pos)
    return _extract_sgml_tag(match.group()), match.end()


def _extract_and_add(r: 're.__Regex') -> Callable[[str, int], MatchPosition]:
    async def _extract(s: str, pos: int) -> MatchPosition:
        match = extract(s, r, pos=pos)
        return match.group(), match.end()
    return _extract


def _extract_and_skip(r: 're.__Regex') -> Callable[[str, int], MatchPosition]:
    async def _skip(s, pos) -> MatchPosition:
        match = extract(s, r, pos=pos)
        return None, match.end()
    return _skip


def _extract_and_skip_quote(start: 're.__Regex', end: 're.__Regex') -> Callable[[str, int], MatchPosition]:
    async def _skip(s: str, pos: int) -> MatchPosition:
        match = extract(s, start, pos=pos)
        match = search(s, end, pos=match.end())
        return "", match.end()
    return _skip


BASE_PIPELINE = (
    *(_extract_and_skip(r) for r in (REGEX_SPACE, REGEX_NUMBER_LITERALS)),
    extract_shebang,
    *(_extract_and_skip_quote(start, end) for (start, end) in (
        (REGEX_START_SINGLE_LINE_COMMENT, REGEX_BOL),
        *MULTI_LINE_COMMENTS,
        (REGEX_SINGLE_QUOTE, REGEX_SINGLE_END_QUOTE),
        (REGEX_DOUBLE_QUOTE, REGEX_DOUBLE_END_QUOTE),
        (REGEX_PRIME_QUOTE, REGEX_PRIME_END_QUOTE),
    )),
    extract_sgml,
    *(_extract_and_add(r) for r in (REGEX_COMMON_PUNCTUATION, REGEX_REGULAR_TOKEN, REGEX_COMMON_OPERATORS))
)

SGML_PIPELINE = (
    _extract_and_skip(REGEX_SPACE),
    extract_sgml_start,
    extract_sgml_tag,
    _extract_and_add(REGEX_EMIT_WORD),
)

SGML_TAG_PIPELINE = (
    _extract_and_add(REGEX_EMIT_TRAILING),
    *(
        _extract_and_skip_quote(start, end) for (start, end) in (
            (REGEX_SINGLE_QUOTE, REGEX_SINGLE_END_QUOTE),
            (REGEX_DOUBLE_QUOTE, REGEX_DOUBLE_END_QUOTE),
        )
    ),
    _extract_and_add(REGEX_EMIT_WORD),
)


class Polyglot(Classifier):

    MAX_READ_SIZE = 1048576

    @staticmethod
    def extract(s: str) -> AsyncGenerator:
        s = s.strip()
        return extract_pipeline(BASE_PIPELINE, s)


    async def classify_file(self, filepath):
        with open(filepath, "r") as f:
            s = f.read(MAX_READ_SIZE)
        return await self.classify(s)