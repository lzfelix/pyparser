from pyparser import parser
from pyparser import tokens
from pyparser import nodes


def _int(i: int, position: int) -> nodes.TerminalNode:
    return nodes.TerminalNode(
        expr=tokens.IntToken(i, position)
    )


def _float(f: float, position: int) -> nodes.TerminalNode:
    return nodes.TerminalNode(
        expr=tokens.FloatToken(f, position)
    )


def test_simple_addition_expression():
    # 3 + 2
    actual = parser.parse([
        tokens.IntToken(3, 0),
        tokens.OperatorToken('+', 1),
        tokens.IntToken(2, 2)
    ])

    expected = nodes.BinaryNode(
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

    expected = nodes.BinaryNode(
        _int(3, 0),
        tokens.OperatorToken('+', 1),
        nodes.BinaryNode(
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

    expected = nodes.BinaryNode(
        _int(7, 0),
        tokens.OperatorToken('*', 1),
        nodes.BinaryNode(
            nodes.BinaryNode(
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

    expected = nodes.UnaryNode(
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

    expected = nodes.UnaryNode(
        tokens.OperatorToken('-', 0),
        expr=nodes.UnaryNode(
            tokens.OperatorToken('+', 1),
            expr=nodes.UnaryNode(
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

    expected = nodes.UnaryNode(
        operator=tokens.OperatorToken('-', 0),
        expr=nodes.BinaryNode(
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

    expected = nodes.BinaryNode(
        nodes.BinaryNode(
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

    expected = nodes.BinaryNode(
        _int(2, 0),
        tokens.OperatorToken('*', 1),
        nodes.UnaryNode(
            tokens.OperatorToken('-', 2),
            _int(3, 3),
        ),
    )

    assert actual == expected
