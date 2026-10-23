import math

import pytest

from pyparser.errors import EvaluationError
from pyparser.lexer import tokenizer
from pyparser.parser import parser
from pyparser.evaluators import evaluator


def _eval(expr: str, variables: dict[str, int | float] | None = None):
    tokens = tokenizer.tokenize(expr)
    ast = parser.parse(tokens)
    return evaluator.evaluate(ast, variables)


def test_simple_expression():
    assert _eval('3') == 3


def test_simple_negative_number():
    assert _eval('-3') == -3


def test_multiple_unary_signs():
    assert _eval('-+--+-3') == 3


def test_parens_expression():
    assert _eval('2*(-7+5)') == -4


def test_float_multiplication():
    assert _eval('3.14 * 2') == pytest.approx(6.28)


def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        _eval('2/(4-2*2)')


def test_expression_with_variables():
    assert _eval('2 * x + y', {'x': 3, 'y': 2.5}) == 8.5


def test_variables_respect_precedence():
    assert _eval('a + b * c', {'a': 1, 'b': 2, 'c': 3}) == 7


def test_variables_inside_parens_with_unary_sign():
    assert _eval('-(x - y)', {'x': 2, 'y': 5}) == 3


def test_long_variable_names():
    assert _eval('long_z_name / 2', {'long_z_name': 9}) == 4.5


def test_same_expression_with_different_bindings():
    tree = parser.parse(tokenizer.tokenize('x * x'))

    assert evaluator.evaluate(tree, {'x': 2}) == 4
    assert evaluator.evaluate(tree, {'x': 3}) == 9


def test_division_by_zero_through_variable():
    with pytest.raises(ZeroDivisionError):
        _eval('1 / x', {'x': 0})


def test_undefined_variable_reports_its_position():
    with pytest.raises(EvaluationError) as exc_info:
        _eval('2 * x + y', {'x': 3})
    assert exc_info.value.position == 8


@pytest.mark.parametrize(
    ('expression', 'expected'),
    [
        pytest.param('2 ^ 3', 8, id='simple'),
        pytest.param('2 ^ 3 ^ 2', 512, id='right-associative'),
        pytest.param('(2 ^ 3) ^ 2', 64, id='parens-override-associativity'),
        pytest.param('2 ^ 3 + 1', 9, id='binds-tighter-than-addition'),
        pytest.param('2 * 3 ^ 2', 18, id='binds-tighter-than-multiplication'),
        pytest.param('-2 ^ 2', -4, id='unary-sign-applies-after-power'),
        pytest.param('(-2) ^ 2', 4, id='parenthesized-negative-base'),
        pytest.param('2 ^ -1', 0.5, id='negative-exponent'),
        pytest.param('4 ^ 0.5', 2.0, id='fractional-exponent'),
        pytest.param('2 ^ (1 + 2)', 8, id='expression-exponent'),
        pytest.param('sin(0)', 0, id='simple-function-call'),
        pytest.param('sin(0) + 1', 1, id='simple-function-call-with-addition'),
        pytest.param('2 * cos(0) + 1', 3, id='call-inside-expression'),
        pytest.param('cos(0) * 2', 2, id='call-followed-by-multiplication'),
        pytest.param('log(1) - 5', -5, id='call-followed-by-subtraction'),
        pytest.param('cos(sin(0))', 1.0, id='nested-function-call'),
        pytest.param('sin(1.21)^2 + cos(1.21)^2', 1, id='call-raised-to-power')
    ],
)
def test_power(expression: str, expected: int | float):
    assert _eval(expression) == pytest.approx(expected)


def test_power_with_variables():
    assert _eval('x ^ 2 + y ^ 2', {'x': 3, 'y': 4}) == 25


def test_nested_fn_call_with_variable():
    assert _eval('cos(sin(x))', {'x': 0}) == 1.0


def test_call_function_with_undefined_args():
    with pytest.raises(EvaluationError):
        _eval('log(0)', {'x': math.pi/2})


def test_call_undefined_function():
    with pytest.raises(EvaluationError):
        _eval('sin(etan(x))')
