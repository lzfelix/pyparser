from dataclasses import dataclass
from pyparser.lexer import tokens


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


@dataclass(frozen=True, slots=True)
class FunctionCallNode(Node):
    fn_name: tokens.StringToken
    arg: Node
