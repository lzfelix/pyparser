import pytest

from pyparser.lexer import tokenizer
from pyparser.operations import evaluator, printer
from pyparser.operations.differentiator import differentiate
from pyparser.operations.simplifier import simplify
from pyparser.parser import ast, parser


_X = ast.VariableNode('x')


def _parse(expr: str) -> ast.Node:
    return parser.parse(tokenizer.tokenize(expr))


def _derivatives(expr: str, order: int) -> list[ast.Node]:
    trees = [_parse(expr)]
    for _ in range(order):
        trees.append(differentiate(trees[-1], _X))
    return trees


_EXPRESSIONS = [
    '3 * x ^ 2 - 2 * x + 7',
    'x ^ -1',
    'x ^ 0.5',
    '-(x - 1) ^ 3',
    '(x + 1) / (x - 1)',
    '2 ^ x',
    'x ^ x',
    '(x + 1) ^ (2 * x)',
    'sin(cos(tan(x)))',
    'x * sin(x)',
    'log(x) / x',
    'sqrt(x ^ 2 + 1)',
    'e ^ (2 * x)',
    'pi * x ^ 2 + e',
    '2 * 3 - 4 / 2 + x * 0',
]


@pytest.mark.parametrize('expression', _EXPRESSIONS)
@pytest.mark.parametrize('x', [0.7, 1.5])
def test_simplified_derivatives_evaluate_the_same(expression: str, x: float):
    for tree in _derivatives(expression, 3):
        expected = evaluator.evaluate(tree, {'x': x})
        assert evaluator.evaluate(simplify(tree), {'x': x}) == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize('expression', _EXPRESSIONS)
def test_simplifying_twice_changes_nothing(expression: str):
    for tree in _derivatives(expression, 3):
        once = simplify(tree)
        assert simplify(once) == once


@pytest.mark.parametrize('expression', _EXPRESSIONS)
def test_simplified_tree_parses_back_from_its_text(expression: str):
    for tree in _derivatives(expression, 3):
        simplified = simplify(tree)
        assert _parse(printer.to_string(simplified)) == simplified


@pytest.mark.parametrize('expression', _EXPRESSIONS)
def test_simplified_tree_is_never_larger(expression: str):
    for tree in _derivatives(expression, 3):
        assert len(printer.to_string(simplify(tree))) <= len(printer.to_string(tree))


@pytest.mark.parametrize(
    ('expression', 'expected'),
    [
        pytest.param('x * y', 'y', id='product'),
        pytest.param('3 * x ^ 2 + 2 * x', '3 * (2 * x) + 2', id='polynomial'),
        pytest.param('sin(x ^ 2)', 'cos(x ^ 2) * (2 * x)', id='chain-rule'),
        pytest.param('x ^ 3', '3 * x ^ 2', id='cube'),
        pytest.param('x ^ 0.5', '0.5 * x ^ -0.5', id='negative-exponent'),
        pytest.param('1 / x', '-1 / x ^ 2', id='reciprocal'),
        pytest.param('-x', '-1', id='negation'),
        pytest.param('e ^ x', 'e ^ x * log(e)', id='exponential'),
        pytest.param('2 * pi', '0', id='constant'),
    ],
)
def test_printed_simplified_derivative(expression: str, expected: str):
    assert printer.to_string(simplify(differentiate(_parse(expression), _X))) == expected
