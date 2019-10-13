from __future__ import division
import argparse
from collections import defaultdict
import json
from .polyglot import Polyglot
from .gitlog import CommitMessageClassifier
from .utils import scandir
import logging
from deps import *

logging.basicConfig(level = logging.DEBUG)


CONFIG = {
    'ignore': [
        r'\.venv',
        r'\.idea',
        r'__pycache__',
        r'polyglot-samples'
    ],
}



def train_polyglot_db(samples_dir: str, dst: str):
    classifier = Polyglot.from_samples(samples_dir)
    data = classifier.dumps(indent=4)
    with open(dst, "w") as f:
        f.write(data)


def polyglot_detect_file(db: str, filepath: str):
    with open(db, "r") as f:
        data = f.read()
    classifier = Polyglot.loads(data)
    with open(filepath, "r") as f:
        r = classifier.classify(f.read())
    print(r[0][0])


def dump_gitlog_db(samples_dir: str, dst: str):
    classifier = CommitMessageClassifier.from_samples(samples_dir)
    print(classifier.classify("ignore babel config"))
    data = classifier.dumps(indent=4)
    with open(dst, "w") as f:
        f.write(data)


def gitlog_analyze_commit(db: str):
    with open(db, "r") as f:
        data = f.read()
    classifier = Polyglot.loads(data)


def analyze_file(file: str):
    pass


def analyze_repo(args):

    result = {
        "languages": {},
        "authors": [],
        "deps": [],
    }

    polyglot = Polyglot.load(args.polyglot_db)
    gitlog = CommitMessageClassifier.load(args.gitlog_db)

    lang_to_deps = {
        "js": get_js_deps,
        "python": get_python_deps,
        "golang": get_go_deps,
    }

    MAX_READ_SIZE = 2 ** 17

    def clssify(filepath):
        logging.info("open {}".format(filepath))
        with open(filepath, "r") as f:
            s = f.read(MAX_READ_SIZE)
        lang = polyglot.classify(s)
        logging.info(lang)
        get_deps = lang_to_deps.get(lang)
        deps = set()
        if get_deps is not None:
            try:
                logging.info("start get deps for {} ({})".format(filepath, lang))
                deps = get_deps(s)
            except:
                pass
        return filepath, lang, deps

    futures = []
    for f in scandir(args.repo, []):
        futures.append(clssify(f))

    lang_count = 0.0
    lang = defaultdict(lambda: 0.0)
    deps = defaultdict(lambda: 0)


    for future in futures:
        f, cls, d = future
        lang[cls] += 1
        lang_count += 1
        for dep in d:
            deps[dep] += 1


    result["languages"] = {
        l: round(c/lang_count, 2)
        for l, c in lang.items()
    }
    result["deps"] = deps
    authors, features = gitlog.analyze(args.repo)
    result["authors"] = [{
        "name": author.name,
        "percent": percent,
        "feaures": {
            cls: percent
            if a == author else 0
            for (a, cls), percent in features.items()
        }
    } for author, percent in authors.items()]
    print(json.dumps(result, indent=4, sort_keys=True ))


def main():
    parser = argparse.ArgumentParser(description='Analyze repo')
    # parser.add_argument('--file', type=str, required=False, help='analyze file')

    subparsers = parser.add_subparsers(help='sub commands', dest='cmd')

    # polyglot
    polyglot_parser = subparsers.add_parser('polyglot', help='polyglot - detect language')

    # train
    train_polyglot_subparsers = polyglot_parser.add_subparsers(dest='polyglot_cmd', help='train polyglot')
    train_polyglot_parser = train_polyglot_subparsers.add_parser('train', help='train classifier on samples')
    train_polyglot_parser.add_argument('--out', dest="file", type=str, help='destination file', default='polyglot-classifier.json')
    train_polyglot_parser.add_argument('--samples', dest="samples", type=str, help='samples dir', default='polyglot-samples')

    # detect
    detect_polyglot_parser = train_polyglot_subparsers.add_parser('detect', help='train classifier on samples')
    detect_polyglot_parser.add_argument('file', type=str, help='file for detection')
    parser.add_argument('--db', dest='polyglot_db',
                                        help='polyglot samples database',
                                        default='polyglot-classifier.json')

    # gitlog
    gitlog_parser = subparsers.add_parser('gitlog', help='store classifiers to file')

    # train
    train_gitlog_subparsers = gitlog_parser.add_subparsers(dest='gitlog_cmd', help='train polyglot')
    train_gitlog_parser = train_gitlog_subparsers.add_parser('train', help='train classifier on samples')
    parser.add_argument('--out', dest="gitlog_db", type=str, help='destination file',
                                       default='classifier-gitlog.json')
    train_gitlog_parser.add_argument('--samples', dest="gitlog_db", type=str, help='samples dir',
                                       default='gitlog-samples')

    # detect
    detect_gitlog_parser = train_gitlog_subparsers.add_parser('check', help='train classifier on samples')
    detect_gitlog_parser.add_argument('--db', dest='gitlog_db',
                                        help='gitlog samples database',
                                        default='classifier-gitlog.json')

    # analyze
    analyze_parser = subparsers.add_parser('analyze', help='analyze repo')
    parser.add_argument('--repo', dest='repo', type=str, default='.', help='analyze repo')

    start = None
    args = parser.parse_args()
    if args.cmd == 'polyglot':

        if args.polyglot_cmd == 'train':
            start = train_polyglot_db(args.samples, args.file)
        if args.polyglot_cmd == 'detect':
            start = polyglot_detect_file(args.polyglot_db, args.file)

    if args.cmd == 'gitlog':

        if args.gitlog_cmd == 'train':
            start = dump_gitlog_db(args.gitlog_samples, args.gitlog_file)
        if args.gitlog_cmd == 'check':
            start = gitlog_analyze_commit(args.gitlog_db)
    if not start:
        start = analyze_repo(args)


if __name__ == '__main__':
    main()