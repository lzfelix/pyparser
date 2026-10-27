import math

import pytest

from pyparser.errors import EvaluationError
from pyparser.lexer import tokenizer
from pyparser.parser import parser
from pyparser.operations import evaluator


def _eval(expr: str, variables: dict[str, int | float] | None = None):
    tokens = tokenizer.tokenize(expr)
    ast = parser.parse(tokens)
    return evaluator.evaluate(ast, variables)


@pytest.mark.parametrize(
    ('expression', 'variables', 'expected'),
    [
        # Numbers and unary signs
        pytest.param('3', {}, 3, id='single-number'),
        pytest.param('-3', {}, -3, id='negative-number'),
        pytest.param('-+--+-3', {}, 3, id='multiple-unary-signs'),
        pytest.param('3.14 * 2', {}, 6.28, id='float-multiplication'),
        pytest.param('2*(-7+5)', {}, -4, id='parens'),

        # Variables
        pytest.param('2 * x + y', {'x': 3, 'y': 2.5}, 8.5, id='variables'),
        pytest.param('a + b * c', {'a': 1, 'b': 2, 'c': 3}, 7, id='variables-respect-precedence'),
        pytest.param('-(x - y)', {'x': 2, 'y': 5}, 3, id='variables-inside-parens-with-unary-sign'),
        pytest.param('long_z_name / 2', {'long_z_name': 9}, 4.5, id='long-variable-name'),

        # Power
        pytest.param('2 ^ 3', {}, 8, id='power'),
        pytest.param('2 ^ 3 ^ 2', {}, 512, id='power-is-right-associative'),
        pytest.param('(2 ^ 3) ^ 2', {}, 64, id='parens-override-power-associativity'),
        pytest.param('2 ^ 3 + 1', {}, 9, id='power-binds-tighter-than-addition'),
        pytest.param('2 * 3 ^ 2', {}, 18, id='power-binds-tighter-than-multiplication'),
        pytest.param('-2 ^ 2', {}, -4, id='unary-sign-applies-after-power'),
        pytest.param('(-2) ^ 2', {}, 4, id='parenthesized-negative-base'),
        pytest.param('2 ^ -1', {}, 0.5, id='negative-exponent'),
        pytest.param('4 ^ 0.5', {}, 2.0, id='fractional-exponent'),
        pytest.param('2 ^ (1 + 2)', {}, 8, id='expression-exponent'),
        pytest.param('x ^ 2 + y ^ 2', {'x': 3, 'y': 4}, 25, id='power-with-variables'),

        # Function calls
        pytest.param('sin(0)', {}, 0, id='function-call'),
        pytest.param('sin(0) + 1', {}, 1, id='call-followed-by-addition'),
        pytest.param('2 * cos(0) + 1', {}, 3, id='call-inside-expression'),
        pytest.param('cos(0) * 2', {}, 2, id='call-followed-by-multiplication'),
        pytest.param('log(1) - 5', {}, -5, id='call-followed-by-subtraction'),
        pytest.param('cos(sin(0))', {}, 1.0, id='nested-function-call'),
        pytest.param('sin(1.21)^2 + cos(1.21)^2', {}, 1, id='call-raised-to-power'),
        pytest.param('cos(sin(x))', {'x': 0}, 1.0, id='nested-call-with-variable'),

        # Indexed variables
        pytest.param('x[0] + x[1]', {'x': [1, 2]}, 3, id='indexed-variables'),
        pytest.param('x[0] + y', {'x': [1, 2], 'y': 10}, 11, id='indexed-and-plain-variables'),
        pytest.param('x[0] * x[1] ^ 2', {'x': [2, 3]}, 18, id='indexed-variables-respect-precedence'),
        pytest.param('-x[1]', {'x': [1, 2]}, -2, id='unary-sign-on-indexed-variable'),
        pytest.param('sin(x[0])^2 + cos(x[0])^2', {'x': [0.7]}, 1, id='indexed-variable-as-function-argument'),

        # Constants
        pytest.param('pi', {}, math.pi, id='pi'),
        pytest.param('e', {}, math.e, id='e'),
        pytest.param('2 * pi', {}, 2 * math.pi, id='constant-in-product'),
        pytest.param('log(e)', {}, 1, id='log-of-e'),
        pytest.param('cos(pi)', {}, -1, id='cos-of-pi'),
        pytest.param('e ^ 2', {}, math.e ** 2, id='power-of-e'),
        pytest.param('pi * r ^ 2', {'r': 2}, 4 * math.pi, id='constant-with-variable'),
        pytest.param('PI + E', {'PI': 1, 'E': 2}, 3, id='uppercase-names-are-variables'),
    ],
)
def test_evaluate(expression: str, variables: dict[str, int | float], expected: int | float):
    assert _eval(expression, variables) == pytest.approx(expected)


@pytest.mark.parametrize(
    ('expression', 'variables', 'expected_error'),
    [
        pytest.param('2/(4-2*2)', {}, ZeroDivisionError, id='division-by-zero'),
        pytest.param('1 / x', {'x': 0}, ZeroDivisionError, id='division-by-zero-through-variable'),
        pytest.param('2 * x + y', {'x': 3}, EvaluationError, id='undefined-variable'),
        pytest.param('log(0)', {}, EvaluationError, id='function-outside-its-domain'),
        pytest.param('x[2]', {'x': [1, 2]}, EvaluationError, id='index-out-of-range'),
        pytest.param('y[0]', {'y': 3}, EvaluationError, id='indexing-single-value'),
        pytest.param('x + 1', {'x': [1, 2]}, EvaluationError, id='multiple-values-without-index'),
        pytest.param('sin(etan(x))', {'x': 0}, EvaluationError, id='undefined-function'),
        pytest.param('2 * x - y', {'x': 3}, EvaluationError, id='undefined-variable'),
        pytest.param('2 * pi', {'pi': 3}, EvaluationError, id='binding-pi'),
        pytest.param('e ^ x', {'x': 1, 'e': 2}, EvaluationError, id='binding-e'),
        pytest.param('x + 1', {'x': 1, 'pi': 3}, EvaluationError, id='binding-unused-constant'),
        pytest.param('PI', {}, EvaluationError, id='uppercase-name-is-undefined-variable'),
        pytest.param('e(2)', {}, EvaluationError, id='calling-constant'),
    ],
)
def test_evaluate_should_raise(expression: str, variables: dict[str, int | float], expected_error: type[Exception]):
    with pytest.raises(expected_error):
        _eval(expression, variables)


def test_same_expression_with_different_bindings():
    tree = parser.parse(tokenizer.tokenize('x * x'))

    assert evaluator.evaluate(tree, {'x': 2}) == 4
    assert evaluator.evaluate(tree, {'x': 3}) == 9


def test_indexing_constant_reports_position():
    with pytest.raises(EvaluationError) as exc_info:
        _eval('2 * pi[0]')
    assert exc_info.value.position == 4
