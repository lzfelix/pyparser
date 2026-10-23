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
