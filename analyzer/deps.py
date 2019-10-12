from .utils import exec
from json import loads
import ast
import esprima
from typing import Set
import os


__all__ = [
    'get_python_deps',
    'get_js_deps',
    'get_go_deps',
]


class AstParseVisitor(ast.NodeVisitor):
    """
    find all python imports at string
    """

    def __init__(self):
        self.imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])

    def visit_ImportFrom(self, node):

        for alias in node.names:
            fullname = '%s.%s' % (node.module, alias.name) if node.module else alias.name
            self.imports.add(fullname.split('.')[0])

    @classmethod
    def get_imports(cls, s: str) -> Set[str]:
        visitor = cls()
        visitor.visit(ast.parse(s))
        return visitor.imports


def get_python_deps(s: str) -> Set[str]:
    visitor = AstParseVisitor()
    visitor.visit(ast.parse(s))
    return visitor.imports


def get_js_deps(s: str) -> Set[str]:
    script = esprima.parseModule(s)
    r = set()
    for token in script.body:
        if token.type == 'ImportDeclaration':
            if str(token.source.value).startswith("."):
                continue
            r.add(token.source.value)
            continue
        if token.type == 'CallExpression':
            if token.callee.name != "require":
                continue
            print(token.arguments[0].value)
            if str(token.arguments[0].value).startswith("."):
                continue
            r.add(token.arguments[0].value)
    return r


def get_go_deps(file: str) -> Set[str]:
    """
    run go list and parse stdout
    :param repo: path to repos
    :return: async genexp
    """
    data, _ = exec('go list --json {}'.format(os.path.basename(file)), cwd=os.path.dirname(file))
    result = loads(data)
    return set(result.get('Imports', []))


