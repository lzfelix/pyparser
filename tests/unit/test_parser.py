import pytest
from pyparser.errors import ParserError
from pyparser.parser import parser
from pyparser.lexer import tokens
from pyparser.parser import ast


def _int(i: int) -> ast.NumberNode:
    return ast.NumberNode(i)


def _float(f: float) -> ast.NumberNode:
    return ast.NumberNode(f)


def test_simple_addition_expression():
    # 3 + 2
    actual = parser.parse([
        tokens.IntToken(3, 0),
        tokens.OperatorToken('+', 1),
        tokens.IntToken(2, 2)
    ])

    expected = ast.BinaryNode(
        _int(3),
        '+',
        _int(2)
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
        _int(3),
        '+',
        ast.BinaryNode(
            _int(2),
            '*',
            _int(5),
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
        _int(7),
        '*',
        ast.BinaryNode(
            ast.BinaryNode(
                _int(5),
                '+',
                _int(10),
            ),
            '-',
            _int(3)
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
        '-',
        _float(3.13)
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
        '-',
        expr=ast.UnaryNode(
            '+',
            expr=ast.UnaryNode(
                '-',
                _float(3.13)
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
        operator='-',
        expr=ast.BinaryNode(
            _int(3),
            '+',
            _float(0.14)
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
            _int(8),
            '-',
            _int(3),
        ),
        '-',
        _int(2),
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
        _int(2),
        '*',
        ast.UnaryNode(
            '-',
            _int(3),
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
        _int(2),
        '^',
        _int(3),
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
        _int(2),
        '^',
        ast.BinaryNode(
            _int(3),
            '^',
            _int(2),
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
        _int(2),
        '*',
        ast.BinaryNode(
            _int(3),
            '^',
            _int(2),
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
        '-',
        ast.BinaryNode(
            _int(2),
            '^',
            _int(2),
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
        _int(2),
        '^',
        ast.UnaryNode(
            '-',
            _int(1),
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
            _int(2),
            '^',
            _int(3),
        ),
        '^',
        _int(2),
    )

    assert actual == expected


def test_parse_function_call():
    # sin(x + 2)
    actual = parser.parse([
        tokens.StringToken('sin', 0),
        tokens.OpenParensToken('(', 1),
        tokens.StringToken('x', 2),
        tokens.OperatorToken('+', 3),
        tokens.IntToken(2, 4),
        tokens.CloseParensToken(')', 5)
    ])

    expected = ast.FunctionCallNode(
        name='sin',
        arg=ast.BinaryNode(
            ast.VariableNode('x'),
            '+',
            _int(2)
        )
    )

    assert actual == expected


def test_parse_nested_function_call():
    # cos(tan(x))
    actual = parser.parse([
        tokens.StringToken('cos', 0),
        tokens.OpenParensToken('(', 1),
        tokens.StringToken('tan', 2),
        tokens.OpenParensToken('(', 3),
        tokens.StringToken('x', 4),
        tokens.CloseParensToken(')', 5),
        tokens.CloseParensToken(')', 6)
    ])

    expected = ast.FunctionCallNode(
        name='cos',
        arg=ast.FunctionCallNode(
            name='tan',
            arg=ast.VariableNode('x')
        )
    )

    assert actual == expected


def test_function_call_followed_by_addition():
    # sin(x) + 1 -> (sin(x)) + 1
    actual = parser.parse([
        tokens.StringToken('sin', 0),
        tokens.OpenParensToken('(', 1),
        tokens.StringToken('x', 2),
        tokens.CloseParensToken(')', 3),
        tokens.OperatorToken('+', 4),
        tokens.IntToken(1, 5),
    ])

    expected = ast.BinaryNode(
        ast.FunctionCallNode(
            name='sin',
            arg=ast.VariableNode('x'),
        ),
        '+',
        _int(1),
    )

    assert actual == expected


def test_function_call_raised_to_power():
    # sin(x) ^ 2 -> (sin(x)) ^ 2
    actual = parser.parse([
        tokens.StringToken('sin', 0),
        tokens.OpenParensToken('(', 1),
        tokens.StringToken('x', 2),
        tokens.CloseParensToken(')', 3),
        tokens.OperatorToken('^', 4),
        tokens.IntToken(2, 5),
    ])

    expected = ast.BinaryNode(
        ast.FunctionCallNode(
            name='sin',
            arg=ast.VariableNode('x'),
        ),
        '^',
        _int(2),
    )

    assert actual == expected


def test_unary_sign_applies_to_function_call():
    # -sin(x) -> -(sin(x))
    actual = parser.parse([
        tokens.OperatorToken('-', 0),
        tokens.StringToken('sin', 1),
        tokens.OpenParensToken('(', 2),
        tokens.StringToken('x', 3),
        tokens.CloseParensToken(')', 4),
    ])

    expected = ast.UnaryNode(
        '-',
        ast.FunctionCallNode(
            name='sin',
            arg=ast.VariableNode('x'),
        ),
    )

    assert actual == expected


def test_incomplete_power_expression_should_raise():
    # 2 ^
    with pytest.raises(ParserError):
        parser.parse([
            tokens.IntToken(2, 0),
            tokens.OperatorToken('^', 1),
        ])


def test_nodes_keep_source_positions():
    # 2 * -sin(x)
    actual = parser.parse([
        tokens.IntToken(2, 0),
        tokens.OperatorToken('*', 1),
        tokens.OperatorToken('-', 2),
        tokens.StringToken('sin', 3),
        tokens.OpenParensToken('(', 4),
        tokens.StringToken('x', 5),
        tokens.CloseParensToken(')', 6),
    ])

    assert actual.position == 1                     # '*'
    assert actual.left.position == 0                # 2
    assert actual.right.position == 2               # '-'
    assert actual.right.expr.position == 3          # sin
    assert actual.right.expr.arg.position == 5      # x
