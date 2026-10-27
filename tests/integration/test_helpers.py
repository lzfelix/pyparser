import pytest

from pyparser.lexer import tokenizer
from pyparser.operations.helpers import depends_on
from pyparser.parser import ast, parser


def _parse(expr: str) -> ast.Node:
    return parser.parse(tokenizer.tokenize(expr))


@pytest.mark.parametrize(
    ('expression', 'var', 'expected'),
    [
        pytest.param('3 * 2 + 1', ast.VariableNode('x'), False, id='only-numbers'),
        pytest.param('x ^ 2', ast.VariableNode('x'), True, id='variable-in-base'),
        pytest.param('2 ^ x', ast.VariableNode('x'), True, id='variable-in-exponent'),
        pytest.param('3 * y', ast.VariableNode('x'), False, id='other-variable'),
        pytest.param('y * sin(-(z + x))', ast.VariableNode('x'), True, id='nested-in-call'),
        pytest.param('sin(y) / log(z)', ast.VariableNode('x'), False, id='calls-without-variable'),
        pytest.param('x[0] * x[1]', ast.IndexedVariableNode('x', 1), True, id='indexed-variable'),
        pytest.param('x[0] * x[1]', ast.IndexedVariableNode('x', 2), False, id='other-index'),
        pytest.param('x[0] * x[1]', ast.VariableNode('x'), False, id='indexed-is-not-plain'),
    ],
)
def test_depends_on(expression: str, var: ast.Node, expected: bool):
    assert depends_on(_parse(expression), var) is expected
