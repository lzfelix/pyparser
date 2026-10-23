from pyparser.errors import ParserError
from pyparser.lexer import tokens
from pyparser.parser import ast

"""
    Grammar
    expr    := term (('+'| '-') term)*
    term    := unary (('*' | '/') unary)*
    unary   := ('+' | '-') unary | primary
    primary := NUMBER | VARIABLE | '(' expr ')'
"""

def _expect_more_tokens(expression: list[tokens.Token], idx: int) -> None:
    if idx >= len(expression):
        raise ParserError('Unexpected end of expression.')


def _parse_primary(expression: list[tokens.Token], idx: int) -> tuple[ast.Node, int]:
    _expect_more_tokens(expression, idx)
    head = expression[idx]

    match head:
        case tokens.IntToken() | tokens.FloatToken() | tokens.StringToken() as token:
            return ast.TerminalNode(expr=token), idx + 1
        case tokens.OpenParensToken():
            expr_node, idx = _parse_expression(expression, idx + 1)
            _expect_more_tokens(expression, idx)
            if not isinstance(expression[idx], tokens.CloseParensToken):
                raise ParserError(f'Expected token ")" but "{expression[idx]}" found.', position=expression[idx].position)
            return expr_node, idx+1
        case _:
            raise ParserError(f'Unexpected token of type {type(head)} at position {head.position}.', position=head.position)


def _parse_unary(expression: list[tokens.Token], idx: int) -> tuple[ast.Node, int]:
    _expect_more_tokens(expression, idx)
    match expression[idx]:
        case tokens.OperatorToken(value='+' | '-'):
            operator = expression[idx]
            expr, idx = _parse_unary(expression, idx + 1)
            return ast.UnaryNode(operator=operator, expr=expr), idx
        case _:
            return _parse_primary(expression, idx)


def _parse_term(expression: list[tokens.Token], idx: int) -> tuple[ast.Node, int]:
    left, idx = _parse_unary(expression, idx)
    while idx < len(expression):
        match expression[idx]:
            case tokens.OperatorToken(value='*' | '/'):
                operator = expression[idx]

                idx += 1
                right, idx = _parse_unary(expression, idx)
                left = ast.BinaryNode(left, operator, right)

            case _:
                break

    return left, idx


def _parse_expression(expression: list[tokens.Token], idx: int) -> tuple[ast.Node, int]:
    left, idx = _parse_term(expression, idx)

    while idx < len(expression):
        match expression[idx]:
            case tokens.OperatorToken(value='+' | '-'):
                operator = expression[idx]

                idx += 1
                right, idx = _parse_term(expression, idx)
                left = ast.BinaryNode(left, operator, right)

            case _:
                break
    return left, idx


def parse(expression: list[tokens.Token]) -> ast.Node:
    node, idx = _parse_expression(expression, idx=0)
    if idx != len(expression):
        raise ParserError(f'Unexpected token "{expression[idx]}"', position=expression[idx].position)
    return node
