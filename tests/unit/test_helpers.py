import pytest
from pyparser.operations.helpers import depends_on
from pyparser.parser import ast


_X = ast.VariableNode('x')
_Y = ast.VariableNode('y')
_X0 = ast.IndexedVariableNode('x', 0)
_X1 = ast.IndexedVariableNode('x', 1)


def _int(i: int) -> ast.NumberNode:
    return ast.NumberNode(i)


def _binary(left: ast.Node, operator: str, right: ast.Node) -> ast.BinaryNode:
    return ast.BinaryNode(left, operator, right)


@pytest.mark.parametrize(
    ('tree', 'var', 'expected'),
    [
        # Leaves
        pytest.param(_int(3), _X, False, id='number'),
        pytest.param(_X, _X, True, id='same-variable'),
        pytest.param(_Y, _X, False, id='other-variable'),
        pytest.param(_X0, _X0, True, id='same-indexed-variable'),
        pytest.param(_X1, _X0, False, id='other-index'),
        pytest.param(_X0, _X, False, id='indexed-variable-is-not-plain-variable'),
        pytest.param(_X, _X0, False, id='plain-variable-is-not-indexed-variable'),

        pytest.param(ast.VariableNode('x', position=7), ast.VariableNode('x', position=0), True, id='ignores-positions'),

        # Inner nodes
        pytest.param(ast.UnaryNode('-', _X), _X, True, id='unary-with-variable'),
        pytest.param(ast.UnaryNode('-', _Y), _X, False, id='unary-without-variable'),
        pytest.param(_binary(_X, '+', _int(1)), _X, True, id='binary-variable-on-left'),
        pytest.param(_binary(_int(1), '*', _X), _X, True, id='binary-variable-on-right'),
        pytest.param(_binary(_Y, '^', _int(2)), _X, False, id='binary-without-variable'),
        pytest.param(ast.FunctionCallNode('sin', _X), _X, True, id='call-with-variable'),
        pytest.param(ast.FunctionCallNode('sin', _Y), _X, False, id='call-without-variable'),

        pytest.param(ast.FunctionCallNode('sin', _Y), ast.VariableNode('sin'), False, id='function-name-is-not-a-variable'),

        pytest.param(
            _binary(_int(2), '*', ast.FunctionCallNode('cos', _binary(_Y, '-', ast.UnaryNode('-', _X)))),
            _X,
            True,
            id='deeply-nested-variable',
        ),
        pytest.param(
            _binary(_int(2), '*', ast.FunctionCallNode('cos', _binary(_Y, '-', ast.UnaryNode('-', _X0)))),
            _X,
            False,
            id='deeply-nested-without-variable',
        ),
    ],
)
def test_depends_on(tree: ast.Node, var: ast.Node, expected: bool):
    assert depends_on(tree, var) is expected


def test_unknown_node_raises():
    with pytest.raises(ValueError):
        depends_on(ast.Node(), _X)
