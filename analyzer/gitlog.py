from __future__ import division
import re
from .classifier import Classifier
from .utils import extract, int_or_zero, extract_pipeline, search, exec
from typing import NamedTuple, Tuple, List, Iterator
from collections import defaultdict
import os
import io

__all__ = [
    'CommitMessageClassifier',
    'extract_commits',
    'blame',
    'parse_blame_line_author',
]


REGEX_MESSAGE = re.compile(r'\s{4}(.*)')
REGEX_NUMSTAT = re.compile(r'(\d+|-)\s+(\d+|-)\s+(.*)')
REGEX_AUTHOR = re.compile('author\s(.+)\s<(.*)>\s(\d+)\s([+\-]\d{4})')
REGEX_COMMITER = re.compile('committer\s(.+)\s<(.*)>\s(\d+)\s([+\-]\d{4})')
REGEX_COMMIT = re.compile(r'''(commit\s(?P<commit>[a-f0-9]+)\ntree\s(?P<tree>[a-f0-9]+)\n(?P<parents>(parent\ [a-f0-9]+\n)*)(?P<author>author\s+(.+)\s+<(.*)>\s+(\d+)\s+([+\-]\d{4})\n)(?P<committer>committer\s+(.+)\s+<(.*)>\s+(\d+)\s+([+\-]\d{4})\n)(gpgsig\s(.*)\n\s(\n\s[^-]+)(.*)\n)?\n(?P<message>(\s{4}[^\n]*\n)*)\n(?P<stats>(^(\d+|-)\s+(\d+|-)\s+(.*)$\n)*))''', re.MULTILINE | re.VERBOSE)


REGEX_TICKET = re.compile("#[0-9]+")
REGEX_VERSION = re.compile(r"(v|version)?((\d+\.)+\d+)\S?(\s+)?", re.IGNORECASE)
REGEX_DOCS = re.compile(r"(\w+\.(md|rst)|readme|changelog|doc(umentation)?(s)?)(?=\s|$)(?=\s|$)", re.IGNORECASE)

REGEX_FEATURE = re.compile(r"(((add|start|support)(ed|ing)?)|((creat|mak)(e|ing|ed)?)|(init(ial)?))(?=\s|$)*", re.IGNORECASE)
REGEX_CHECK_FEATURE = re.compile(r"(((add|start|support)(ed|ing)?)|((creat|mak)(e|ing|ed)?)|(init(ial)?))((?!(test|doc|readme)).)*$", re.IGNORECASE)

REGEX_REFACTOR = re.compile(r"(((refactor)(ed|ing)?)|(((re)?(mov|writ)|delet)(e|ing|ed)+)|(reinit(ial)?)|simplif(y|ied)|(clean(ed)?))(?=\s|$)", re.IGNORECASE)
REGEX_CHECK_REFACTOR = re.compile(r"(((refactor)(ed|ing)?)|(((re)?(mov|writ)|delet)(e|ing|ed)+)|(reinit(ial)?)|simplif(y|ied)|(clean(ed)?))((?!(test|doc|readme)).)*$", re.IGNORECASE)


REGEX_BUG = re.compile(r"(((fix)(ed|ing|bug)?)|(miss(ing|ed)?)|(error|bug)|(wrong|invalid|fail))(\s+)?", re.IGNORECASE)
REGEX_CHECK_BUG = re.compile(r"(((fix)(ed|ing|bug)?)|(miss(ing|ed)?)|(error|bug)|(wrong|invalid|fail))((?!(test|doc|readme)).)*$", re.IGNORECASE)

REGEX_TESTS = re.compile(r"((test(((-)?(case|suite))|s)?)|(e2e))\S?(\s+)?", re.IGNORECASE)
REGEX_WORD = re.compile("[A-z]+")
REGEX_SKIP = re.compile(r"(\s|\n|;|\{|\}|\(|\)|\[|\]|\,|\?|\!|\$|\\)+")

REGEX_BLAME = re.compile(r"^\^?\w+\s\((?P<author>.*)\s\d{4}\-\d{2}\-\d{2}\s\d{2}\:\d{2}\:\d{2}\s(\+|-)?\d{4}\s|\d{2}\)")

Stat = NamedTuple("Stat", (
    ("insert", int),
    ("delete", int),
    ("filename", str),
))


Participant = NamedTuple("Participant", (
    ("name", str),
    ("email", str),
))


Commit = NamedTuple("Commit", (
    ("commit", str),
    ("tree", str),
    ("parents", Tuple[str, ...]),
    ("author", Participant),
    ("committer", Participant),
    ("message", str),
    ("stats", List[Stat]),
))

def extract_message(s: str) -> str:
    return extract(s, REGEX_MESSAGE).group().strip().lower()


def extract_stat(s: str) -> Stat:
    insert, delete, filename = extract(s, REGEX_NUMSTAT).groups()
    return Stat(int_or_zero(insert), int_or_zero(delete), filename)


def extract_author(s: str) -> Participant:
    name, email, _, _ = extract(s, REGEX_AUTHOR).groups()
    return Participant(name, email)


def extract_committer(s: str) -> Participant:
    name, email, _, _ = extract(s, REGEX_COMMITER).groups()
    return Participant(name, email)


def _prepare_commit(**kwargs) -> Commit:
    kwargs["stats"] = [extract_stat(stat) for stat in kwargs["stats"].splitlines()]
    kwargs["author"] = extract_author(kwargs["author"])
    kwargs["committer"] = extract_committer(kwargs["committer"])
    kwargs["message"] = extract_message(kwargs["message"])
    return Commit(**kwargs)


def extract_commit(s: str) -> Commit:
    kwargs = extract(s, REGEX_COMMIT).groupdict()
    return _prepare_commit(**kwargs)


def extract_commits(s: str) -> Iterator[Commit]:
    for match in REGEX_COMMIT.finditer(s):
        kwargs = match.groupdict()
        yield _prepare_commit(**kwargs)


def extract_ticket(s: str, pos: int):
    match = extract(s, REGEX_TICKET, pos=pos)
    return "#!TICKET", match.end()


def extract_version(s: str, pos: int):
    match = extract(s, REGEX_VERSION, pos=pos)
    return "#!VERSION", match.end()


def extract_docs(s: str, pos: int):
    match = extract(s, REGEX_DOCS, pos=pos)
    return "#!DOCS", match.end()


def extract_feature(s: str, pos: int):
    match = extract(s, REGEX_FEATURE, pos=pos)
    return "#!FEATURE", match.end()


def extract_refactor(s: str, pos: int):
    match = extract(s, REGEX_REFACTOR, pos=pos)
    return "#!REFACTOR", match.end()


def extract_bug(s: str, pos: int):
    match = extract(s, REGEX_BUG, pos=pos)
    return "#!BUG", match.end()


def extract_test(s: str, pos: int):
    match = extract(s, REGEX_TESTS, pos=pos)
    return "#!TEST", match.end()


def search_version(s: str, pos: int):
    match = search(s, REGEX_VERSION, pos=pos)
    return "#!VERSION", match.end()


def search_docs(s: str, pos: int):
    match = search(s, REGEX_DOCS, pos=pos)
    return "#!DOCS", match.end()


def search_feature(s: str, pos: int):
    match = extract(s, REGEX_CHECK_FEATURE, pos=pos)
    return "#!FEATURE", match.end()


def search_refactor(s: str, pos: int):
    match = search(s, REGEX_CHECK_REFACTOR, pos=pos)
    return "#!REFACTOR", match.end()


def search_bug(s: str, pos: int):
    match = extract(s, REGEX_CHECK_BUG, pos=pos)
    return "#!BUG", match.end()


def search_test(s: str, pos: int):
    match = search(s, REGEX_TESTS, pos=pos)
    return "#!TEST", match.end()


def extract_word(s: str, pos: int):
    match = extract(s, REGEX_WORD, pos=pos)
    return match.group(), match.end()


def skip(s, pos):
    match = extract(s, REGEX_SKIP, pos=pos)
    return None, match.end()


def parse_blame_line_author(line: str) -> str:
    return extract(line, REGEX_BLAME).groupdict().get('author').strip()


def blame(fp: str):
    result, _ = exec('git blame -c {}'.format(fp), cwd=os.path.dirname(fp))
    buf = io.StringIO(result)
    result = defaultdict(lambda: 0.0)
    while True:
        line = buf.readline().strip()
        if not line:
            break
        result[parse_blame_line_author(line)] += 1
    return result


GITLOG_PIPELINE = (
    skip,
    extract_docs,
    extract_test,
    #extract_bug,
    #extract_feature,
    #extract_refactor,
    extract_version,
    extract_word,
)


class CommitMessageClassifier(Classifier):

    @staticmethod
    def extract(s: str):
        return extract_pipeline(GITLOG_PIPELINE, s, pos=0)
