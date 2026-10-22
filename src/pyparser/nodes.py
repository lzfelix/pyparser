from dataclasses import dataclass
from pyparser import tokens


class Node:
    pass


@dataclass(frozen=True, slots=True)
class UnaryNode(Node):
    operator: tokens.OperatorToken
    expr: Node


@dataclass(frozen=True, slots=True)
class BinaryNode(Node):
    l_expr: Node
    operator: tokens.OperatorToken
    r_expr: Node


@dataclass(frozen=True, slots=True)
class TerminalNode(Node):
    expr: tokens.FloatToken | tokens.IntToken | tokens.StringToken
