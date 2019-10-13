from argparse import ArgumentParser
from .config import Config, Module
from .utils import scandir, exec
from .polyglot import Polyglot
from .deps import get_python_deps, get_js_deps
from dataclasses import dataclass
from .gitlog import CommitMessageClassifier, extract_commits
from collections import defaultdict
import logging
import os
from typing import Set
import pathlib
import json
import sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

# TODO: fooo
BASE_DIR = ""


@dataclass
class File:
    path: str
    lang: str
    deps: Set[str]
    updates: float = 0


MAX_READ_SIZE = 2 ** 16
DEFAULT_CONFIG_PATH = ".kd-config.json"

polyglot = Polyglot.load(os.path.join(os.path.abspath(os.path.dirname(__file__)), "polyglot-classifier.json"))

gitlog = CommitMessageClassifier.load(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "classifier-gitlog.json"))


def init(repo: str):
    with open(os.path.join(repo, DEFAULT_CONFIG_PATH), "w") as f:
        f.write(Config.generate(repo).to_json())


def analyze_module(module: Module, config: Config):
    path = (module.path != "." and os.path.join(BASE_DIR, module.path)) or BASE_DIR
    authors_aliases = {}
    for author in config.authors:
        authors_aliases[author.name] = author.name
        for alias in author.aliases:
            authors_aliases[alias] = author.name
    if not os.path.isdir(path):
        raise Exception("module should be dir")
    files = scandir(path, config.ignore_list)
    results = {}
    for file in files:
        logging.info("analyze {}".format(file))
        with open(file, "r", encoding="utf-8") as f:
            try:
                s = f.read(MAX_READ_SIZE)
            except:
                results[file] = File(file, "UNKNOWN", set())
                continue
        ext = pathlib.Path(file).suffix
        lang = polyglot.classify(s, ext)
        deps = set()
        if lang == "python":
            try:
                deps = get_python_deps(s)
            except Exception as e:
                logging.error("parse {} error {}".format(file, e))
        if lang == 'js':
            try:
                deps = get_js_deps(s)
            except Exception as e:
                logging.error("parse {} error {}".format(file, e))
        results[file] = File(file, lang, deps)
    stdout, _ = exec('git log --numstat --pretty=raw -- {}'.format(path), cwd=path)

    features = defaultdict(lambda: 0.0)
    authors = defaultdict(lambda: 0.0)
    author_feature = defaultdict(lambda: 0.0)
    updates = 0.0

    for commit in extract_commits(stdout):

        feature = gitlog.classify(commit.message)
        features[feature] += 1
        author = authors_aliases.get(commit.author.name, commit.author.name)

        for (insert, delete, filename) in commit.stats:
            fl = results.get(os.path.join(BASE_DIR, filename))
            if not fl:
                continue
            __updates = insert + delete
            fl.updates += __updates
            updates += __updates
            authors[author] += __updates
            author_feature[(author, feature)] += __updates

    langs = defaultdict(lambda: 0.0)
    deps = defaultdict(lambda: 0.0)
    for name, v in results.items():
        langs[v.lang] += v.updates

        _deps = set()
        if v.lang == 'python':
            for d in v.deps:
                local = os.path.join(os.path.dirname(name), d) + '.py'
                glob = os.path.join(BASE_DIR, d) + '.py'
                if results.get(local) or results.get(glob):
                    continue
                _deps.add(d)
        else:
            _deps = v.deps
        # TODO: JS DEPS invalid percents
        for d in _deps:
            deps[d] += v.updates / len(_deps)
    if not updates:
        return {
            "name": module.name,
            "dependencies": [],
            "authors": [],
            "languages": [],
            "features": [],
        }
    return {
        "name": module.name,
        "dependencies": [{
            "name": d,
            "percent": round(v / updates, 2)
        } for d, v in deps.items()
        ],
        "authors": list(filter(lambda x: x.get("percent") > 0, [{
            "name": a,
            "percent": round(v / updates, 4)
        } for a, v in authors.items()
        ])),
        "languages": list(filter(lambda x: x.get("percent") > 0, [{
            "name": l,
            "percent": round(v / updates, 2)
        } for l, v in langs.items()
        ])),
        "features": list(filter(lambda x: x.get("percent") > 0, [{
            "author": author,
            "name": feature,
            "percent": round(value / updates, 2)
        } for (author, feature), value in author_feature.items()
        ]))
    }


def analyze(repo):
    # I don't want the global variable, but...
    # TODO: fix this
    global BASE_DIR

    BASE_DIR = os.path.abspath(repo)
    config = Config.from_file(os.path.join(BASE_DIR, DEFAULT_CONFIG_PATH))
    modules = (
        m
        if m.path != "." else Module("main", BASE_DIR)
        for m in config.modules
    )
    r = {
        "name": config.name,
        "repository": config.repo,
        "modules": [],
    }
    for module in modules:
        r["modules"].append(analyze_module(module, config))
    print(json.dumps(r, indent=4, ensure_ascii=False))


def main():
    parser = ArgumentParser(description="Help me, I don't know what i'm doing")
    parser.add_argument('--repo', default=".", dest="repo", help="Repository")
    # list of commands
    subparsers = parser.add_subparsers(dest="cmd", help='List of commands')

    # initial
    init_parser = subparsers.add_parser('init', help='Init config')

    args = parser.parse_args()
    if args.cmd == "init":
        init(args.repo)

    if not args.cmd:
        analyze(args.repo)
