import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from pyparser.parser import ast


@dataclass(frozen=True, slots=True)
class Function:
    name: str
    implementation: Callable[[float], float]
    # Builds f'(u) as a tree, given the argument u. Multiplying by u' (chain rule)
    # is left to the differentiator, so each entry only knows its own derivative
    derivative: Callable[[ast.Node], ast.Node]


def _sin_derivative(u: ast.Node) -> ast.Node:
    # sin'(u) = cos(u)
    return ast.FunctionCallNode('cos', u)


def _cos_derivative(u: ast.Node) -> ast.Node:
    # cos'(u) = -sin(u)
    return ast.UnaryNode('-', ast.FunctionCallNode('sin', u))


def _tan_derivative(u: ast.Node) -> ast.Node:
    # tan'(u) = 1 / cos(u) ^ 2
    return ast.BinaryNode(
        ast.NumberNode(1),
        '/',
        ast.BinaryNode(ast.FunctionCallNode('cos', u), '^', ast.NumberNode(2)),
    )


def _log_derivative(u: ast.Node) -> ast.Node:
    # log'(u) = 1 / u
    return ast.BinaryNode(ast.NumberNode(1), '/', u)


def _sqrt_derivative(u: ast.Node) -> ast.Node:
    # sqrt'(u) = 1 / (2 * sqrt(u))
    return ast.BinaryNode(
        ast.NumberNode(1),
        '/',
        ast.BinaryNode(ast.NumberNode(2), '*', ast.FunctionCallNode('sqrt', u)),
    )


BUILTINS: Mapping[str, Function] = MappingProxyType({
    function.name: function for function in [
        Function('sin', math.sin, _sin_derivative),
        Function('cos', math.cos, _cos_derivative),
        Function('tan', math.tan, _tan_derivative),
        Function('log', math.log, _log_derivative),
        Function('sqrt', math.sqrt, _sqrt_derivative),
    ]
})
