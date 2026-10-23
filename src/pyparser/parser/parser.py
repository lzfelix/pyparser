from pyparser.errors import ParserError
from pyparser.lexer import tokens
from pyparser.parser import ast
from pyparser.parser.token_container import TokenContainer

"""
    Grammar
    expr    := term (('+'| '-') term)*
    term    := unary (('*' | '/') unary)*
    unary   := ('+' | '-') unary | primary
    primary := NUMBER | VARIABLE | '(' expr ')'
"""


def _parse_primary(container: TokenContainer) -> ast.Node:
    head = container.next()

    match head:
        case tokens.IntToken() | tokens.FloatToken() | tokens.StringToken() as token:
            return ast.TerminalNode(expr=token)
        case tokens.OpenParensToken():
            expr_node = _parse_expression(container)
            closing = container.next()
            if not isinstance(closing, tokens.CloseParensToken):
                raise ParserError(f'Expected token ")" but "{closing}" found.', position=closing.position)
            return expr_node
        case _:
            raise ParserError(f'Unexpected token of type {type(head)} at position {head.position}.', position=head.position)


def _parse_unary(container: TokenContainer) -> ast.Node:
    match container.peek():
        case tokens.OperatorToken(value='+' | '-'):
            operator = container.next()
            expr = _parse_unary(container)
            return ast.UnaryNode(operator=operator, expr=expr)
        case _:
            return _parse_primary(container)


def _parse_term(container: TokenContainer) -> ast.Node:
    left = _parse_unary(container)
    while not container.is_exhausted():
        match container.peek():
            case tokens.OperatorToken(value='*' | '/'):
                operator = container.next()
                right = _parse_unary(container)
                left = ast.BinaryNode(left, operator, right)

            case _:
                break

    return left


def _parse_expression(container: TokenContainer) -> ast.Node:
    left = _parse_term(container)

    while not container.is_exhausted():
        match container.peek():
            case tokens.OperatorToken(value='+' | '-'):
                operator = container.next()
                right = _parse_term(container)
                left = ast.BinaryNode(left, operator, right)

            case _:
                break
    return left


def parse(expression: list[tokens.Token]) -> ast.Node:
    container = TokenContainer(expression)
    node = _parse_expression(container)
    if not container.is_exhausted():
        token = container.peek()
        raise ParserError(f'Unexpected token "{token}"', position=token.position)
    return node
