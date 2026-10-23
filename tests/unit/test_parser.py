import pytest
from pyparser.errors import ParserError
from pyparser.parser import parser
from pyparser.lexer import tokens
from pyparser.parser import ast


def _int(i: int, position: int) -> ast.TerminalNode:
    return ast.TerminalNode(
        expr=tokens.IntToken(i, position)
    )


def _float(f: float, position: int) -> ast.TerminalNode:
    return ast.TerminalNode(
        expr=tokens.FloatToken(f, position)
    )


def test_simple_addition_expression():
    # 3 + 2
    actual = parser.parse([
        tokens.IntToken(3, 0),
        tokens.OperatorToken('+', 1),
        tokens.IntToken(2, 2)
    ])

    expected = ast.BinaryNode(
        _int(3, 0),
        tokens.OperatorToken('+', 1),
        _int(2, 2)
    )

    assert actual == expected


def test_multiplication_takes_precedence_over_addition():
    # 3 + 2 * 5
    actual = parser.parse([
        tokens.IntToken(3, 0),
        tokens.OperatorToken('+', 1),
        tokens.IntToken(2, 2),
        tokens.OperatorToken('*', 3),
        tokens.IntToken(5, 4)
    ])

    expected = ast.BinaryNode(
        _int(3, 0),
        tokens.OperatorToken('+', 1),
        ast.BinaryNode(
            _int(2, 2),
            tokens.OperatorToken('*', 3),
            _int(5, 4),
        )
    )

    assert actual == expected


def test_parens_expression():
    # 7 * ((5 + 10) - 3)
    actual = parser.parse([
        tokens.IntToken(7, 0),
        tokens.OperatorToken('*', 1),
        tokens.OpenParensToken('(', 2),
        tokens.OpenParensToken('(', 3),
        tokens.IntToken(5, 4),
        tokens.OperatorToken('+', 5),
        tokens.IntToken(10, 6),
        tokens.CloseParensToken(')', 7),
        tokens.OperatorToken('-', 8),
        tokens.IntToken(3, 9),
        tokens.CloseParensToken(')', 9)
    ])

    expected = ast.BinaryNode(
        _int(7, 0),
        tokens.OperatorToken('*', 1),
        ast.BinaryNode(
            ast.BinaryNode(
                _int(5, 4),
                tokens.OperatorToken('+', 5),
                _int(10, 6),
            ),
            tokens.OperatorToken('-', 8),
            _int(3, 9)
        )
    )

    assert actual == expected


def test_unary_operator():
    # -3.13
    actual = parser.parse([
        tokens.OperatorToken('-', 0),
        tokens.FloatToken(3.13, 1)
    ])

    expected = ast.UnaryNode(
        tokens.OperatorToken('-', 0),
        _float(3.13, 1)
    )

    assert actual == expected


def test_successive_unary_operators():
    # -+-3
    actual = parser.parse([
        tokens.OperatorToken('-', 0),
        tokens.OperatorToken('+', 1),
        tokens.OperatorToken('-', 2),
        tokens.FloatToken(3.13, 3)
    ])

    expected = ast.UnaryNode(
        tokens.OperatorToken('-', 0),
        expr=ast.UnaryNode(
            tokens.OperatorToken('+', 1),
            expr=ast.UnaryNode(
                tokens.OperatorToken('-', 2),
                _float(3.13, 3)
            )
        )
    )

    assert actual == expected


def test_unary_with_parens():
    actual = parser.parse([
        tokens.OperatorToken('-', 0),
        tokens.OpenParensToken('(', 1),
        tokens.IntToken(3, 2),
        tokens.OperatorToken('+', 3),
        tokens.FloatToken(0.14, 4),
        tokens.CloseParensToken(')', 5)
    ])

    expected = ast.UnaryNode(
        operator=tokens.OperatorToken('-', 0),
        expr=ast.BinaryNode(
            _int(3, 2),
            tokens.OperatorToken('+', 3),
            _float(0.14, 4)
        )
    )

    assert actual == expected


def test_subtraction_is_left_associative():
    # 8 - 3 - 2 -> (8 - 3) - 2
    actual = parser.parse([
        tokens.IntToken(8, 0),
        tokens.OperatorToken('-', 1),
        tokens.IntToken(3, 2),
        tokens.OperatorToken('-', 3),
        tokens.IntToken(2, 4),
    ])

    expected = ast.BinaryNode(
        ast.BinaryNode(
            _int(8, 0),
            tokens.OperatorToken('-', 1),
            _int(3, 2),
        ),
        tokens.OperatorToken('-', 3),
        _int(2, 4),
    )

    assert actual == expected


def test_unary_operator_as_multiplication_operand():
    # 2 * -3 -> 2 * (-3)
    actual = parser.parse([
        tokens.IntToken(2, 0),
        tokens.OperatorToken('*', 1),
        tokens.OperatorToken('-', 2),
        tokens.IntToken(3, 3),
    ])

    expected = ast.BinaryNode(
        _int(2, 0),
        tokens.OperatorToken('*', 1),
        ast.UnaryNode(
            tokens.OperatorToken('-', 2),
            _int(3, 3),
        ),
    )

    assert actual == expected


def test_incomplete_binary_expression_should_raise():
    # 3 +
    with pytest.raises(ParserError):
        parser.parse([
            tokens.IntToken(3, 0),
            tokens.OperatorToken('+', 1),
        ])


def test_unclosed_parens_should_raise():
    # (3
    with pytest.raises(ParserError):
        parser.parse([
            tokens.OpenParensToken('(', 0),
            tokens.IntToken(3, 1),
        ])


def test_unexpected_close_parens_should_raise():
    # 3)
    with pytest.raises(ParserError) as exc_info:
        parser.parse([
            tokens.IntToken(3, 0),
            tokens.CloseParensToken(')', 1),
        ])
    assert exc_info.value.position == 1


def test_power_expression():
    # 2 ^ 3
    actual = parser.parse([
        tokens.IntToken(2, 0),
        tokens.OperatorToken('^', 1),
        tokens.IntToken(3, 2),
    ])

    expected = ast.BinaryNode(
        _int(2, 0),
        tokens.OperatorToken('^', 1),
        _int(3, 2),
    )

    assert actual == expected


def test_power_is_right_associative():
    # 2 ^ 3 ^ 2 -> 2 ^ (3 ^ 2)
    actual = parser.parse([
        tokens.IntToken(2, 0),
        tokens.OperatorToken('^', 1),
        tokens.IntToken(3, 2),
        tokens.OperatorToken('^', 3),
        tokens.IntToken(2, 4),
    ])

    expected = ast.BinaryNode(
        _int(2, 0),
        tokens.OperatorToken('^', 1),
        ast.BinaryNode(
            _int(3, 2),
            tokens.OperatorToken('^', 3),
            _int(2, 4),
        ),
    )

    assert actual == expected


def test_power_takes_precedence_over_multiplication():
    # 2 * 3 ^ 2 -> 2 * (3 ^ 2)
    actual = parser.parse([
        tokens.IntToken(2, 0),
        tokens.OperatorToken('*', 1),
        tokens.IntToken(3, 2),
        tokens.OperatorToken('^', 3),
        tokens.IntToken(2, 4),
    ])

    expected = ast.BinaryNode(
        _int(2, 0),
        tokens.OperatorToken('*', 1),
        ast.BinaryNode(
            _int(3, 2),
            tokens.OperatorToken('^', 3),
            _int(2, 4),
        ),
    )

    assert actual == expected


def test_unary_sign_applies_after_power():
    # -2 ^ 2 -> -(2 ^ 2)
    actual = parser.parse([
        tokens.OperatorToken('-', 0),
        tokens.IntToken(2, 1),
        tokens.OperatorToken('^', 2),
        tokens.IntToken(2, 3),
    ])

    expected = ast.UnaryNode(
        tokens.OperatorToken('-', 0),
        ast.BinaryNode(
            _int(2, 1),
            tokens.OperatorToken('^', 2),
            _int(2, 3),
        ),
    )

    assert actual == expected


def test_unary_sign_in_exponent():
    # 2 ^ -1 -> 2 ^ (-1)
    actual = parser.parse([
        tokens.IntToken(2, 0),
        tokens.OperatorToken('^', 1),
        tokens.OperatorToken('-', 2),
        tokens.IntToken(1, 3),
    ])

    expected = ast.BinaryNode(
        _int(2, 0),
        tokens.OperatorToken('^', 1),
        ast.UnaryNode(
            tokens.OperatorToken('-', 2),
            _int(1, 3),
        ),
    )

    assert actual == expected


def test_parens_override_power_associativity():
    # (2 ^ 3) ^ 2
    actual = parser.parse([
        tokens.OpenParensToken('(', 0),
        tokens.IntToken(2, 1),
        tokens.OperatorToken('^', 2),
        tokens.IntToken(3, 3),
        tokens.CloseParensToken(')', 4),
        tokens.OperatorToken('^', 5),
        tokens.IntToken(2, 6),
    ])

    expected = ast.BinaryNode(
        ast.BinaryNode(
            _int(2, 1),
            tokens.OperatorToken('^', 2),
            _int(3, 3),
        ),
        tokens.OperatorToken('^', 5),
        _int(2, 6),
    )

    assert actual == expected


def test_incomplete_power_expression_should_raise():
    # 2 ^
    with pytest.raises(ParserError):
        parser.parse([
            tokens.IntToken(2, 0),
            tokens.OperatorToken('^', 1),
        ])
