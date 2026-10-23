import pytest

from pyparser.lexer import tokenizer
from pyparser.parser import parser
from pyparser.evaluators import evaluator


def _eval(expr: str):
    tokens = tokenizer.tokenize(expr)
    ast = parser.parse(tokens)
    return evaluator.evaluate(ast)


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
