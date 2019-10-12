from marshmallow_dataclass import dataclass
from typing import List
from dataclasses import field
from .utils import exec
import re
import os
import json


__all__ = [
    'Author',
    'Module',
    'Config',
    'default_config'
]

@dataclass
class Service:
    name: str


@dataclass
class Author:
    name: str
    aliases: List[str] = field(default_factory=list)


@dataclass
class Module:
    name: str
    path: str


@dataclass
class Config:
    name: str
    repo: str
    ignore: List[str] = field(default_factory=list)
    description: str = ""
    modules: List[Module] = field(default_factory=list)
    authors: List[Author] = field(default_factory=list)
    services: List[Service] = field(default_factory=list)

    @classmethod
    def default_config(cls, repo, cwd):

        ignore_list = [
            "\\.git"
        ]

        try:
            with open(os.path.join(cwd, ".gitignore")) as f:
                ignore_list.extend(filter(None, [
                    line.strip().replace(".", "\.").replace("*", ".*").replace("/", "\\/")
                    for line in f.readlines()
                ]))
                print(ignore_list)
        except Exception as e:
            print(e)
            pass

        return cls(
            name=os.path.basename(repo).split(".")[0],
            repo=repo,
            description="",
            modules=[
                Module(
                    name="main",
                    path=".",
                )
            ],
            authors=[],
            ignore=list(set(ignore_list)),
        )

    @classmethod
    def from_json(cls, s: str):
        return Config.Schema().load(json.loads(s))

    @classmethod
    def from_file(cls, fp: str):
        if not os.path.exists(fp):
            return cls.generate(os.path.dirname(fp))
        with open(fp, "r") as f:
            return cls.from_json(f.read())


    def to_json(self):
        return json.dumps(Config.Schema().dump(self), indent=4)

    @classmethod
    def generate(cls, path="."):
        stdout, _ = exec('git remote get-url origin', cwd=path)
        return cls.default_config(stdout.strip(), path)

    @property
    def ignore_list(self) -> List['re.__Regex']:
        if hasattr(self, "__ignore_list"):
            return self.__ignore_list
        self.__ignore_list = [
            re.compile(i, re.IGNORECASE)
            for i in self.ignore
        ]
        return self.__ignore_list
