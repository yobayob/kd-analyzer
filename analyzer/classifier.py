from __future__ import division
from collections import defaultdict
from math import log
from typing import NewType, Dict, List, Tuple, Iterable
from dataclasses import dataclass
from json import dumps, loads, load
import os


__all__ = [
    'train',
    'classify'
]


LOG_MIN = 10 ** (-7)
GUESSING_COEFICIENT = 1.5 # TODO: learn it
UNKNOWN = "UNKNOWN"

Sample = NewType("Sample", Tuple[Iterable, str])
Samples = NewType("Samples", List[Sample])


@dataclass(frozen=True)
class Classifier:

    classes: Dict[str, int]
    freq: Dict[str, int]

    @classmethod
    def train(cls, samples) -> 'Classifier':
        """
        :param samples: train set for create classifier
        :return: Classifier
        """
        classes, freq = defaultdict(lambda: 0), defaultdict(lambda: 0)
        counter = 0
        for feats, label in samples:
            classes[label] += 1
            counter +=1
            for feat in cls.extract(feats):
                freq[label, feat] += 1

        for label, feat in freq:
            freq[label, feat] /= classes[label]
        for c in classes:
            classes[c] /= counter
        return cls(classes, freq)


    def classify(self, s: str, guess_class: str = "") ->  str:
        results = []
        feats =  [token for token in self.extract(s)]
        for cls in self.classes.keys():
            r = -log(self.classes[cls]) + \
                sum(-log(self.freq.get((cls,feat), LOG_MIN)) for feat in feats)  # TODO: add guess coef
            results.append((cls, r))
        if not results:
            return UNKNOWN
        return sorted(results, key=lambda cls: cls[1])[0][0]

    @classmethod
    def build_samples(cls, samples_dir: str, class_name: str = ""):
        """
        recursive scan dir with samples to build a training set
        :param samples_dir: direcrory with samples
        :param cls: class name
        :return: train set
        """
        queue = [os.path.join(samples_dir, file) for file in os.listdir(samples_dir)]
        while len(queue) > 0:
            fp = queue.pop()
            if os.path.isdir(fp):
                queue.extend(
                    os.path.join(fp, file)
                    for file in os.listdir(fp)
                )
                continue
            with open(fp, "r") as f:
                yield (f.read(), os.path.basename(os.path.dirname(fp)))

    @classmethod
    def from_samples(cls, samples_dir: str) -> 'Classifier':
        return cls.train(cls.build_samples(samples_dir))

    @staticmethod
    def extract(s: str):
        raise NotImplementedError

    @classmethod
    def loads(cls, s: str):
        kwargs = loads(s)
        freq = {
            (item.get("class"), item.get("token")): item.get("value")
            for item in kwargs.pop("freq")
        }
        return cls(**kwargs, freq=freq)

    @classmethod
    def load(cls, db: str):
        with open(db, "r") as f:
            kwargs = load(f)
        freq = {
            (item.get("class"), item.get("token")): item.get("value")
            for item in kwargs.pop("freq")
        }
        return cls(**kwargs, freq=freq)

    def dumps(self, **kwargs):
        return dumps({
            "classes": self.classes,
            "freq": [{
                "class": cls,
                "token": token,
                "value": value
            } for (cls, token), value  in self.freq.items()],
        }, **kwargs)
