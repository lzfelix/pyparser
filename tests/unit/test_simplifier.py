import pytest
from pyparser.operations.simplifier import simplify
from pyparser.parser import ast


_X = ast.VariableNode('x')
_Y = ast.VariableNode('y')


def _int(i: int) -> ast.NumberNode:
    return ast.NumberNode(i)


def _neg(expr: ast.Node) -> ast.UnaryNode:
    return ast.UnaryNode('-', expr)


def _binary(left: ast.Node, operator: str, right: ast.Node) -> ast.BinaryNode:
    return ast.BinaryNode(left, operator, right)


def _call(name: str, arg: ast.Node) -> ast.FunctionCallNode:
    return ast.FunctionCallNode(name, arg)


@pytest.mark.parametrize(
    ('tree', 'expected'),
    [
        # Leaves
        pytest.param(_int(3), _int(3), id='number'),
        pytest.param(_X, _X, id='variable'),
        pytest.param(ast.IndexedVariableNode('x', 1), ast.IndexedVariableNode('x', 1), id='indexed-variable'),
        pytest.param(ast.VariableNode('pi'), ast.VariableNode('pi'), id='constant'),

        # Folding
        pytest.param(_binary(_int(2), '+', _int(3)), _int(5), id='sum'),
        pytest.param(_binary(_int(2), '-', _int(3)), _neg(_int(1)), id='negative-difference'),
        pytest.param(_binary(_int(2), '*', ast.NumberNode(1.5)), ast.NumberNode(3.0), id='product'),
        pytest.param(_binary(_int(2), '^', _int(10)), _int(1024), id='power'),
        pytest.param(_binary(_int(2), '^', _neg(_int(1))), ast.NumberNode(0.5), id='negative-exponent'),
        pytest.param(
            _binary(_binary(_int(1), '+', _int(2)), '*', _binary(_int(4), '-', _int(1))),
            _int(9),
            id='nested',
        ),
        pytest.param(_binary(_X, '^', _binary(_int(3), '-', _int(1))), _binary(_X, '^', _int(2)), id='inside-tree'),
        pytest.param(_call('sin', _binary(_int(1), '+', _int(1))), _call('sin', _int(2)), id='inside-call'),

        # Signs
        pytest.param(_neg(_int(3)), _neg(_int(3)), id='negated-number-is-kept'),
        pytest.param(_neg(_neg(_int(3))), _int(3), id='double-negation-of-number'),
        pytest.param(ast.UnaryNode('+', _int(3)), _int(3), id='unary-plus-of-number'),
        pytest.param(_neg(_binary(_int(1), '+', _int(2))), _neg(_int(3)), id='negated-sum'),
        pytest.param(_neg(_binary(_int(1), '-', _int(1))), _int(0), id='negated-zero'),
        pytest.param(ast.NumberNode(-2), _neg(_int(2)), id='negative-number-node'),
        pytest.param(ast.NumberNode(-0.0), ast.NumberNode(0.0), id='negative-zero'),
        pytest.param(_binary(_neg(_int(2)), '*', _int(3)), _neg(_int(6)), id='negative-operand'),

        # Identities
        pytest.param(_binary(_int(0), '+', _X), _X, id='zero-plus'),
        pytest.param(_binary(_X, '+', _int(0)), _X, id='plus-zero'),
        pytest.param(_binary(_X, '-', _int(0)), _X, id='minus-zero'),
        pytest.param(_binary(_int(0), '-', _X), _neg(_X), id='zero-minus'),
        pytest.param(_binary(_int(0), '-', _neg(_X)), _X, id='zero-minus-negation'),
        pytest.param(_binary(_int(0), '*', _X), _int(0), id='zero-times'),
        pytest.param(_binary(_X, '*', ast.NumberNode(0.0)), _int(0), id='times-float-zero'),
        pytest.param(_binary(_int(1), '*', _X), _X, id='one-times'),
        pytest.param(_binary(_X, '*', ast.NumberNode(1.0)), _X, id='times-float-one'),
        pytest.param(_binary(_X, '/', _int(1)), _X, id='divided-by-one'),
        pytest.param(_binary(_int(0), '/', _X), _int(0), id='zero-divided'),
        pytest.param(_binary(_int(0), '/', _int(0)), _binary(_int(0), '/', _int(0)), id='zero-divided-by-zero'),
        pytest.param(_binary(_X, '/', _int(0)), _binary(_X, '/', _int(0)), id='divided-by-zero'),
        pytest.param(_binary(_X, '^', _int(0)), _int(1), id='to-the-zero'),
        pytest.param(_binary(_int(1), '^', _X), _int(1), id='one-to-the'),
        pytest.param(_binary(_X, '^', _int(1)), _X, id='to-the-one'),
        pytest.param(ast.UnaryNode('+', _X), _X, id='unary-plus'),
        pytest.param(_neg(_neg(_X)), _X, id='double-negation'),
        pytest.param(_neg(_neg(_neg(_X))), _neg(_X), id='triple-negation'),
        pytest.param(_neg(_X), _neg(_X), id='negation-is-kept'),
        pytest.param(
            _binary(_binary(_int(0), '*', _X), '+', _binary(_int(3), '*', _binary(_int(1), '*', _X))),
            _binary(_int(3), '*', _X),
            id='cascading',
        ),
        pytest.param(
            _binary(_binary(_int(1), '*', _Y), '+', _binary(_X, '*', _int(0))),
            _Y,
            id='derivative-of-product',
        ),
        pytest.param(
            _binary(_binary(_int(2), '*', _binary(_X, '^', _binary(_int(2), '-', _int(1)))), '*', _int(1)),
            _binary(_int(2), '*', _X),
            id='derivative-of-square',
        ),

        # Left symbolic
        pytest.param(_binary(_int(1), '/', _int(3)), _binary(_int(1), '/', _int(3)), id='division'),
        pytest.param(_call('log', _int(2)), _call('log', _int(2)), id='function-of-number'),
        pytest.param(
            _binary(_int(2), '*', ast.VariableNode('pi')),
            _binary(_int(2), '*', ast.VariableNode('pi')),
            id='constant-coefficient',
        ),
        pytest.param(_binary(_X, '+', _Y), _binary(_X, '+', _Y), id='variables'),
        pytest.param(_binary(_X, '-', _X), _binary(_X, '-', _X), id='like-terms'),
        pytest.param(
            _binary(_int(2), '*', _binary(_int(3), '*', _X)),
            _binary(_int(2), '*', _binary(_int(3), '*', _X)),
            id='nested-coefficients',
        ),
        pytest.param(_binary(_X, '+', _int(1)), _binary(_X, '+', _int(1)), id='number-plus-variable'),
    ],
)
def test_simplify(tree: ast.Node, expected: ast.Node):
    assert simplify(tree) == expected


@pytest.mark.parametrize(
    'tree',
    [
        pytest.param(_binary(_int(0), '^', _neg(_int(1))), id='zero-to-negative-power'),
        pytest.param(_binary(_neg(_int(8)), '^', ast.NumberNode(0.5)), id='complex-result'),
        pytest.param(_binary(ast.NumberNode(1e300), '^', _int(2)), id='overflow'),
        pytest.param(_binary(ast.NumberNode(1e300), '*', ast.NumberNode(1e300)), id='infinite-result'),
        pytest.param(_binary(_int(9), '^', _int(65)), id='exponent-over-limit'),
        pytest.param(_binary(_X, '%', _int(2)), id='unknown-operator'),
    ],
)
def test_unfoldable_operations_are_kept(tree: ast.Node):
    assert simplify(tree) == tree


def test_keeps_positions():
    tree = ast.BinaryNode(_X, '+', ast.BinaryNode(_int(1), '+', _int(2), position=6), position=2)

    simplified = simplify(tree)

    assert simplified.position == 2
    assert simplified.right.position == 6


def test_does_not_modify_input():
    tree = _binary(_int(1), '+', _int(2))

    simplify(tree)

    assert tree == _binary(_int(1), '+', _int(2))


def test_unknown_node_raises():
    with pytest.raises(ValueError):
        simplify(ast.Node())
