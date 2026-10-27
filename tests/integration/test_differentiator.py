import copy

import pytest

from pyparser.errors import DifferentiationError
from pyparser.lexer import tokenizer
from pyparser.operations import evaluator, printer
from pyparser.operations.differentiator import differentiate
from pyparser.parser import ast, parser


def _parse(expr: str) -> ast.Node:
    return parser.parse(tokenizer.tokenize(expr))


def _shifted(variables: dict, var: ast.Node, delta: float) -> dict:
    shifted = copy.deepcopy(variables)
    match var:
        case ast.VariableNode(name=name):
            shifted[name] += delta
        case ast.IndexedVariableNode(name=name, index=index):
            shifted[name][index] += delta
    return shifted


def _numerical_derivative(tree: ast.Node, var: ast.Node, variables: dict, h: float = 1e-6) -> float:
    forward = evaluator.evaluate(tree, _shifted(variables, var, h))
    backward = evaluator.evaluate(tree, _shifted(variables, var, -h))
    return (forward - backward) / (2 * h)


_X = ast.VariableNode('x')
_Y = ast.VariableNode('y')


@pytest.mark.parametrize(
    ('expression', 'var', 'variables'),
    [
        # Polynomials
        pytest.param('3 * x ^ 2 - 2 * x + 7', _X, {'x': 1.5}, id='polynomial'),
        pytest.param('x ^ 2', _X, {'x': -1.5}, id='square-at-negative-point'),
        pytest.param('x ^ -1', _X, {'x': 1.5}, id='negative-exponent'),
        pytest.param('x ^ 0', _X, {'x': 0.0}, id='zero-exponent-at-zero'),
        pytest.param('(x - 2) ^ 0', _X, {'x': 2.0}, id='zero-exponent-of-expression-at-its-root'),
        pytest.param('x ^ 0.5', _X, {'x': 2.0}, id='fractional-exponent'),
        pytest.param('-(x - 1) ^ 3', _X, {'x': 0.5}, id='negated-cube'),

        # Products and quotients
        pytest.param('x * x * x', _X, {'x': 1.5}, id='repeated-product'),
        pytest.param('(x + 1) / (x - 1)', _X, {'x': 3.0}, id='quotient'),
        pytest.param('1 / (x ^ 2 + 1)', _X, {'x': 0.7}, id='reciprocal'),

        # Exponentials
        pytest.param('2 ^ x', _X, {'x': 1.5}, id='constant-base'),
        pytest.param('x ^ x', _X, {'x': 1.5}, id='variable-base-and-exponent'),
        pytest.param('x ^ 2 ^ x', _X, {'x': 1.2}, id='power-tower'),
        pytest.param('(x + 1) ^ (2 * x)', _X, {'x': 0.5}, id='expressions-in-base-and-exponent'),

        # Functions and the chain rule
        pytest.param('sin(x)', _X, {'x': 0.7}, id='sin'),
        pytest.param('cos(x)', _X, {'x': 0.7}, id='cos'),
        pytest.param('tan(x)', _X, {'x': 0.7}, id='tan'),
        pytest.param('log(x)', _X, {'x': 0.7}, id='log'),
        pytest.param('sin(x ^ 2)', _X, {'x': 0.7}, id='chain-rule'),
        pytest.param('sin(cos(tan(x)))', _X, {'x': 0.7}, id='nested-chain-rule'),
        pytest.param('x * sin(x)', _X, {'x': 0.7}, id='product-with-function'),
        pytest.param('log(x) / x', _X, {'x': 2.0}, id='quotient-with-function'),
        pytest.param('x ^ sin(x)', _X, {'x': 0.7}, id='function-in-exponent'),
        pytest.param('log(cos(x) ^ 2 + 1)', _X, {'x': 0.7}, id='log-of-expression'),

        # Partial derivatives
        pytest.param('x * y ^ 2', _X, {'x': 2.0, 'y': 3.0}, id='partial-wrt-x'),
        pytest.param('x * y ^ 2', _Y, {'x': 2.0, 'y': 3.0}, id='partial-wrt-y'),
        pytest.param('sin(x * y) + y', _Y, {'x': 0.5, 'y': 1.5}, id='partial-wrt-y-in-function'),
        pytest.param('x[0] * x[1] ^ 2', ast.IndexedVariableNode('x', 1), {'x': [2.0, 3.0]}, id='partial-wrt-indexed-variable'),
    ],
)
def test_derivative_matches_numerical_derivative(expression: str, var: ast.Node, variables: dict):
    tree = _parse(expression)
    derivative = differentiate(tree, var)

    expected = _numerical_derivative(tree, var, variables)
    assert evaluator.evaluate(derivative, variables) == pytest.approx(expected, rel=1e-5, abs=1e-8)


@pytest.mark.parametrize(
    ('expression', 'expected'),
    [
        pytest.param('3 * y', '0', id='constant'),
        pytest.param('x ^ 2', '2 * x ^ (2 - 1) * 1', id='constant-exponent'),
        pytest.param('2 ^ x', '2 ^ x * log(2) * 1', id='constant-base'),
        pytest.param('sin(x ^ 2)', 'cos(x ^ 2) * (2 * x ^ (2 - 1) * 1)', id='chain-rule'),
        pytest.param('3 * x', '0 * x + 3 * 1', id='unsimplified-product'),
    ],
)
def test_printed_derivative(expression: str, expected: str):
    assert printer.to_string(differentiate(_parse(expression), _X)) == expected


def test_derivative_can_be_differentiated_again():
    second = differentiate(differentiate(_parse('x ^ 3'), _X), _X)

    assert evaluator.evaluate(second, {'x': 2.0}) == pytest.approx(12.0)


def test_unknown_function_reports_position():
    with pytest.raises(DifferentiationError) as exc_info:
        differentiate(_parse('2 * etan(x)'), _X)
    assert exc_info.value.position == 4
