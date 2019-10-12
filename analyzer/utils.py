import re
import os
import subprocess
from typing import Iterable, List


__all__ = [
    'ExtractException',
    'extract',
    'int_or_zero',
    'extract_pipeline',
    'exec',
    'scandir',
]


class ExtractException(Exception):
    """Base class for extract errors in this module"""
    pass


def extract(s: str, re: 're.__Regex', **kwargs) -> 're.__Match':
    """
    :param s: source line
    :param re: compile regex
    :param kwargs: other params
    :return:
    """
    match = re.match(s, **kwargs)
    if not match:
        raise ExtractException("can't extract {} from {}".format(re, s))
    return match


def search(s: str, re: 're.__Regex', **kwargs) -> 're.__Match':
    """
    :param s: source line
    :param re: compile regex
    :param kwargs: other params
    :return:
    """
    match = re.search(s, **kwargs)
    if not match:
        raise ExtractException("can't extract {} from {}".format(re, s))
    return match


def int_or_zero(s: str) -> int:
    """
    :param s: string or int
    :return: int or zero
    """
    try:
        return int(s)
    except ValueError:
        return 0


def extract_pipeline(pipeline: Iterable, s: str, pos: int=0):
    """
    :param pipeline: list of extractors
    :param s: source string
    :param pos: start positions
    :return: token async generator
    """
    while pos < len(s):
        for step in pipeline:
            try:

                res, pos = step(s, pos)
                if not res:
                    break

                # open all generators
                q = [res, ]
                while len(q) > 0:
                    node = q.pop(0)
                    if hasattr(node, "__aiter__"):
                        for child in node:
                            q.append(child)
                    else:
                        yield node
                break
            except ExtractException as e:
                continue
        else:
            pos += 1

def exec(cmd: str, cwd: str =".") -> (str, str):

    """
    exec command
    :param cmd: command
    :param cwd: current dir
    """
    proc = subprocess.Popen(
        cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
    )

    stdout, stderr = proc.communicate()
    return stdout.decode(), stderr.decode()


def scandir(dir: str, ingore_list: List['re.__Regex'] = list()):
    files = [os.path.join(dir, f) for f in os.listdir(dir)]
    for f in files:
        if any(ignore.search(f) for ignore in ingore_list):
            continue
        if os.path.isdir(f):
            files.extend([os.path.join(f, c) for c in os.listdir(f)])
            continue
        yield f