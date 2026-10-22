from pyparser import tokens
from pyparser import nodes

"""
    Grammar
    expr    := term (('+'| '-') term)*
    term    := unary (('*' | '/') unary)*
    unary   := ('+' | '-') unary | primary
    primary := NUMBER | VARIABLE | '(' expr ')'
"""

def _parse_primary(expression: list[tokens.Token], idx: int) -> tuple[nodes.Node, int]:
    head = expression[idx]

    match head:
        case tokens.IntToken() | tokens.FloatToken() | tokens.StringToken() as token:
            return nodes.TerminalNode(expr=token), idx + 1
        case tokens.OpenParensToken():
            expr_node, idx = _parse_expression(expression, idx + 1)
            if not isinstance(expression[idx], tokens.CloseParensToken):
                raise ValueError(f'Expected token ")" but "{expression[idx]}" found.')
            return expr_node, idx+1
        case _:
            raise ValueError(f'Unexpected token of type {type(head)} at position {head.position}.')


def _parse_unary(expression: list[tokens.Token], idx: int) -> tuple[nodes.Node, int]:
    match expression[idx]:
        case tokens.OperatorToken(value='+' | '-'):
            operator = expression[idx]
            expr, idx = _parse_unary(expression, idx + 1)
            return nodes.UnaryNode(operator=operator, expr=expr), idx
        case _:
            return _parse_primary(expression, idx)


def _parse_term(expression: list[tokens.Token], idx: int) -> tuple[nodes.Node, int]:
    left, idx = _parse_unary(expression, idx)
    while idx < len(expression):
        match expression[idx]:
            case tokens.OperatorToken(value='*' | '/'):
                operator = expression[idx]

                idx += 1
                right, idx = _parse_unary(expression, idx)
                left = nodes.BinaryNode(left, operator, right)

            case _:
                break

    return left, idx


def _parse_expression(expression: list[tokens.Token], idx: int) -> tuple[nodes.Node, int]:
    left, idx = _parse_term(expression, idx)

    while idx < len(expression):
        match expression[idx]:
            case tokens.OperatorToken(value='+' | '-'):
                operator = expression[idx]

                idx += 1
                right, idx = _parse_term(expression, idx)
                left = nodes.BinaryNode(left, operator, right)

            case _:
                break
    return left, idx


def parse(expression: list[tokens.Token]) -> nodes.Node:
    node, idx = _parse_expression(expression, idx=0)
    if idx != len(expression):
        raise SyntaxError(f'Unexpected token "{expression[idx]}"')
    return node
