from __future__ import division
import re
from .classifier import Classifier
from .utils import extract, int_or_zero, extract_pipeline, search, exec
from typing import NamedTuple, Tuple, List, Iterator
from collections import defaultdict
from catboost import CatBoostClassifier
import pandas as pd

__all__ = [
    'CommitMessageClassifier',
    'extract_commits'
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

    def classify_by_model(self, s: str):
        return predict_commit(s)


    def analyze(self, path: str):
        stdout, _ = exec('git log --numstat --pretty=raw -- {}'.format(path), cwd=path)
        all_commits = 0
        commit_classes = defaultdict(lambda: 0.0)
        authors = defaultdict(lambda: 0.0)
        author_clasess = defaultdict(lambda: 0.0)
        for c in extract_commits(stdout):
            cls = (self.classify(c.message))
            commit_classes[cls] += 1.0
            authors[c.author] += 1.0
            author_clasess[(c.author, cls)] += 1.0
            all_commits += 1
        for author, commits in authors.items():
            authors[author] = round(commits/all_commits, 2)
        for (author, cls), commits in author_clasess.items():
            author_clasess[(author, cls)] = round(commits/commit_classes[cls], 2)
        return authors, author_clasess

# if __name__ == '__main__':
#     import subprocess, os
#     import asyncio
#     from shutil import rmtree
#
#
#
# #     lines = 0.0
# #     # authors = defaultdict(lambda: 0.0)
# #     # for c in extract_commits(raw_git_log.stdout.read().decode('utf-8', 'ignore')):
# #     #     print(c.message)
# #     #     for stat in c.stats:
# #     #         r = stat.insert + stat.delete
# #     #         lines += r
# #     #         authors[c.author.email] += r
# #     #     print("=============")
# #     # for key, value in authors.items():
# #     #     print("{} {}".format(key, round(100 * (value/lines), 1)))
# #
# #     word = {
# #         'f': 'features',
# #         'b': 'bug',
# #         't': 'tests',
# #         'd': 'deploy',
# #         'r': 'refactoring',
# #         'u': 'update',
# #     }
# #
# #     FEATURE = (
# #         'add', 'added', 'adding', 'init', 'finish', 'finished', 'start', 'started', 'init',
# #         'create', 'make', 'making', 'support', 'logic', 'feature', 'initial', 'implementation', 'implement'
# #     )
# #
# #     REFACTOR = (
# #         'refactor', 'refactoring', 'move', 'remove', 'moved', 'removed', 'removing', 'moving',
# #         'clean', 'update', 'cleanup', 'simplify', 'rewrite', 'optimize',
# #     )
# #
# #     BUG = (
# #         'fix', 'fixing', 'fixed', 'bug', '#!TICKET', 'incorrect',
# #         'issue', 'wrong', 'error', 'errors', 'bugs', 'typo', 'typos', 'bugfix'
# #     )
# #
# #     BUMP = (
# #         'version', 'bump', 'bumped'
# #     )
# #
# #     UPDATE = (
# #         "#!VERSION",
# #     )
# #
# #     TESTS = (
# #         "test", "tests", "testing",
# #     )
# #
# #     DOCS = (
# #         "document", "docs", "doc", "readme", "documentation", 'license', 'changelog',
# #     )
#
#     sort_pipeline = (
#         (search_docs, 'docs'),
#         (search_test, 'tests'),
#         (search_bug, 'bugs'),
#         (search_feature, 'features'),
#         (search_refactor, 'refactoring'),
#         (search_version, 'version'),
#     )
#
#     async def start(repos):
#
#         repo = "".join("".join(repos.split("/")[-2:]).split(".")[:-1])
#
#
#         try:
#             clone = subprocess.Popen(
#                 ["git", "clone", repos, repo],
#                 cwd="/tmp/"
#             )
#             clone.wait()
#         except Exception as e:
#             print(e)
#             #
#
#
#         command = ['git', 'log', '--numstat', '--pretty=raw']
#         raw_git_log = subprocess.Popen(
#             command,
#             stdout=subprocess.PIPE,
#             cwd=os.path.join("/tmp", repo)
#         )
#
#         samples = {}
#         for c in extract_commits(raw_git_log.stdout.read().decode('utf-8', 'ignore')):
#             print(c.message)
#             s = c.message
#             for (step, cls) in sort_pipeline:
#                 try:
#                     res, _ = await step(s, 0)
#                     if not cls:
#                         break
#                     if not os.path.exists(os.path.join("gitlog-samples", cls)):
#                         os.mkdir(os.path.join("gitlog-samples", cls))
#                     with open(os.path.join("gitlog-samples", cls, c.commit), "w") as f:
#                         f.write(c.message)
#                     print(res)
#                     break
#                 except ExtractException as e:
#                     continue
#
#
#
#             classes = set()
#             #async for token in CommitMessageClassifier.extract(c.message):
#                 # if token in FEATURE:
#                 #     classes.add("f")
#                 # if token in REFACTOR:
#                 #     classes.add("r")
#                 # if token in BUG:
#                 #     classes.add("b")
#                 # if token in BUMP:
#                 #     classes.add("version")
#                 # if token in UPDATE:
#                 #     classes.add("u")
#                 # if token in TESTS:
#                 #     classes.add("t")
#                 # if token in DOCS:
#                 #     classes.add("docs")
#             # res = await classifier.classify(c.message)
#
#             # classes = [res[0][0]]
#             # for cls in classes:
#             #     cls = word.get(cls, cls)
#             #     if not os.path.exists(os.path.join("gitlog-samples", cls)):
#             #         os.mkdir(os.path.join("gitlog-samples", cls))
#             #     if not samples.get(cls):
#             #        samples[cls] = open(os.path.join("gitlog-samples", cls, repo), "a")
#             #     samples[cls].write(c.message + '\n')
#         for _, v in samples.items():
#             v.close()
#
#         rmtree(os.path.join("/tmp", repo))
# #
# #
#
#     async def check():
#         for repo in [
#             'https://github.com/facebook/react.git',
#             'https://github.com/facebook/react-native-website.git',
#             'https://github.com/facebook/flipper.git',
#             'https://github.com/facebook/create-react-app.git',
#             'https://github.com/pallets/flask.git',
#             'https://github.com/encode/django-rest-framework.git',
#             'https://github.com/moby/moby.git',
#             'https://github.com/docker/docker-ce.git',
#             'https://github.com/go-redis/redis.git',
#             'https://github.com/antirez/redis.git',
#             'https://github.com/phpredis/phpredis.git',
#             'https://github.com/laravel/laravel.git',
#             'https://github.com/laravel/framework.git',
#             'https://github.com/laravel/socialite.git',
#             'https://github.com/laravel/echo.git',
#             'https://github.com/babel/babel.git',
#             'https://github.com/axios/axios.git',
#             'https://github.com/aio-libs/aiohttp.git',
#             'https://github.com/aio-libs/aiohttp-session.git',
#             'https://github.com/aio-libs/aiohttp-security.git',
#             'https://github.com/mattrobenolt/jinja2-cli.git',
#             'https://github.com/aio-libs/aiohttp-jinja2.git',
#             'https://github.com/pallets/jinja.git',
#             'https://github.com/pallets/werkzeug.git',
#             'https://github.com/pallets/itsdangerous.git',
#             'https://github.com/facebook/react-native.git',
#             'https://github.com/ReactTraining/react-router.git',
#             'https://github.com/zeit/next.js.git',
#             'https://github.com/ui-router/react.git',
#             'https://github.com/ui-router/angular.git',
#             'https://github.com/ui-router/core.git',
#             'https://github.com/reduxjs/redux.git',
#             'https://github.com/reduxjs/react-redux.git',
#             'https://github.com/redux-saga/redux-saga.git',
#             'https://github.com/reduxjs/redux-thunk.git',
#         ]:
#             await start(repo)
#             time.sleep(15)
#
#     ioloop = asyncio.get_event_loop()
#     ioloop.run_until_complete(check())
#     ioloop.stop()
#     ioloop.close()

import os
import random

cat_model = CatBoostClassifier().load_model(os.path.join(os.path.abspath(os.path.dirname(__file__)), "cat_model"))
X_train = pd.read_json(os.path.join(os.path.abspath(os.path.dirname(__file__)), "X_train.json"))


def predict_commit(new_commit):

    freq = pd.Series(''.join(new_commit).split()).value_counts()
    dic1 = pd.DataFrame(freq)

    dic1['repo'] = 'new'
    dic1['guess'] = 'new'
    dic1['lemma'] = dic1.index
    dic1['id'] = random.randint(5, 15)
    dic1['author'] = 'new'
    dic1.rename(columns = {0 : 'count'}, inplace = True)

    dic1.index = dic1['id']
    dic1.index.name = 'index'

    pd.pivot_table(dic1, index = 'id',
                            columns = 'lemma',
                            values='guess',
                            aggfunc=len)
    dic1.index.name = 'lemme'
    dic1.index = dic1['lemma']


    X_train_new = X_train.T
    X_train_new.index.name = 'lemma'


    X_train_new = X_train_new.join(dic1['count'],on = 'lemma').fillna(0)
    #X_train_new.rename(columns = {'count' : random.randint(1, 95)},inplace = True)

    predict = cat_model.predict(X_train_new[['count','ad380da3-971e-45fe-8305-f5395c4063b4']].T)[0]

    predict_proba = cat_model.predict_proba(X_train_new[['count','ad380da3-971e-45fe-8305-f5395c4063b4']].T)[0]

    predict = predict[0]
    predict = int(predict)

    map_predict = {
        0: 'bugs',
        1: 'docs',
        2: 'features',
        3: 'refactoring',
        4: 'tests',
        5: 'version'
    }
    print(map_predict.get(predict, 'UNKNOWN'), new_commit)
    return map_predict.get(predict, 'UNKNOWN')
