from pyparser.errors import ParserError
from pyparser.lexer import tokens
from pyparser.parser import ast
from pyparser.parser.token_container import TokenContainer

"""
    Grammar
    expr    := term (('+'| '-') term)*
    term    := unary (('*' | '/') unary)*
    unary   := ('+' | '-') unary | power
    power   := primary ('^' unary)?
    primary := NUMBER | VARIABLE | VARIABLE '[' INT ']' | FUN_NAME '(' expr ')' | '(' expr ')'
"""


def _parse_parenthesized(container: TokenContainer) -> ast.Node:
    # Parses `expr ')'`, the opening parens must have already been consumed
    expr_node = _parse_expression(container)
    closing = container.next()
    if not isinstance(closing, tokens.CloseParensToken):
        raise ParserError(f'Expected token ")" but "{closing}" found.', position=closing.position)
    return expr_node


def _parse_indexed_variable(name: tokens.StringToken, container: TokenContainer) -> ast.Node:
    # Parses `INT ']'`, the opening bracket must have already been consumed
    index = container.next()
    if not isinstance(index, tokens.IntToken):
        raise ParserError(f'Expected an integer index but "{index}" found.', position=index.position)

    closing = container.next()
    if not isinstance(closing, tokens.CloseBracketToken):
        raise ParserError(f'Expected token "]" but "{closing}" found.', position=closing.position)

    return ast.IndexedVariableNode(name=name.value, index=index.value, position=name.position)


def _parse_primary(container: TokenContainer) -> ast.Node:
    head = container.next()

    match head:
        case tokens.IntToken() | tokens.FloatToken() as token:
            return ast.NumberNode(value=token.value, position=token.position)
        case tokens.StringToken() as token:
            if container.is_exhausted():
                return ast.VariableNode(name=token.value, position=token.position)

            match container.peek():
                case tokens.OpenParensToken():
                    container.next()  # Consume open parens
                    arg = _parse_parenthesized(container)
                    return ast.FunctionCallNode(name=token.value, arg=arg, position=token.position)
                case tokens.OpenBracketToken():
                    container.next()  # Consume open bracket
                    return _parse_indexed_variable(token, container)
                case _:
                    return ast.VariableNode(name=token.value, position=token.position)
        case tokens.OpenParensToken():
            return _parse_parenthesized(container)
        case _:
            raise ParserError(f'Unexpected token of type {type(head)} at position {head.position}.', position=head.position)


def _parse_power(container: TokenContainer) -> ast.Node:
    lhs = _parse_primary(container)
    if container.is_exhausted():
        return lhs

    match container.peek():
        case tokens.OperatorToken(value='^'):
            operator = container.next()
            rhs = _parse_unary(container)
            return ast.BinaryNode(lhs, operator.value, rhs, position=operator.position)
        case _:
            return lhs


def _parse_unary(container: TokenContainer) -> ast.Node:
    match container.peek():
        case tokens.OperatorToken(value='+' | '-'):
            operator = container.next()
            expr = _parse_unary(container)
            return ast.UnaryNode(operator=operator.value, expr=expr, position=operator.position)
        case _:
            return _parse_power(container)


def _parse_term(container: TokenContainer) -> ast.Node:
    left = _parse_unary(container)
    while not container.is_exhausted():
        match container.peek():
            case tokens.OperatorToken(value='*' | '/'):
                operator = container.next()
                right = _parse_unary(container)
                left = ast.BinaryNode(left, operator.value, right, position=operator.position)

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
                left = ast.BinaryNode(left, operator.value, right, position=operator.position)

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
