import pytest
from pyparser.operations import printer
from pyparser.parser import ast


def _int(i: int) -> ast.NumberNode:
    return ast.NumberNode(i)


def _var(name: str) -> ast.VariableNode:
    return ast.VariableNode(name)


def _unary(operator: str, expr: ast.Node) -> ast.UnaryNode:
    return ast.UnaryNode(operator, expr)


def _binary(left: ast.Node, operator: str, right: ast.Node) -> ast.BinaryNode:
    return ast.BinaryNode(left, operator, right)


@pytest.mark.parametrize(
    ('tree', 'expected'),
    [
        # Leaves
        pytest.param(_int(3), '3', id='int'),
        pytest.param(ast.NumberNode(2.5), '2.5', id='float'),
        pytest.param(_var('x'), 'x', id='variable'),
        pytest.param(ast.IndexedVariableNode('x', 2), 'x[2]', id='indexed-variable'),
        pytest.param(ast.FunctionCallNode('sin', _var('x')), 'sin(x)', id='function-call'),

        # Precedence
        pytest.param(_binary(_binary(_int(1), '+', _int(2)), '*', _int(3)), '(1 + 2) * 3', id='weaker-left-child'),
        pytest.param(_binary(_int(1), '+', _binary(_int(2), '*', _int(3))), '1 + 2 * 3', id='stronger-right-child'),
        pytest.param(_binary(_binary(_var('a'), '+', _var('b')), '/', _var('c')), '(a + b) / c', id='weaker-left-child-of-division'),

        # Left-associative operators: stricter on the right
        pytest.param(_binary(_binary(_int(1), '-', _int(2)), '-', _int(3)), '1 - 2 - 3', id='minus-tie-on-left'),
        pytest.param(_binary(_int(1), '-', _binary(_int(2), '-', _int(3))), '1 - (2 - 3)', id='minus-tie-on-right'),
        pytest.param(_binary(_int(1), '+', _binary(_int(2), '+', _int(3))), '1 + (2 + 3)', id='plus-tie-on-right-keeps-parens'),
        pytest.param(_binary(_binary(_var('a'), '+', _var('b')), '-', _var('c')), 'a + b - c', id='plus-under-minus-on-left'),
        pytest.param(_binary(_binary(_var('a'), '-', _var('b')), '+', _var('c')), 'a - b + c', id='minus-under-plus-on-left'),
        pytest.param(_binary(_binary(_var('a'), '*', _var('b')), '*', _var('c')), 'a * b * c', id='times-tie-on-left'),
        pytest.param(_binary(_binary(_var('a'), '/', _var('b')), '*', _var('c')), 'a / b * c', id='division-under-times-on-left'),
        pytest.param(_binary(_var('a'), '-', _binary(_var('b'), '*', _var('c'))), 'a - b * c', id='stronger-child-on-right-of-minus'),
        pytest.param(_binary(_var('a'), '*', _binary(_var('b'), '^', _var('c'))), 'a * b ^ c', id='power-on-right-of-times'),
        pytest.param(_binary(_var('a'), '/', _binary(_var('b'), '*', _var('c'))), 'a / (b * c)', id='division-tie-on-right'),

        # Power is right-associative: stricter on the left
        pytest.param(_binary(_int(2), '^', _binary(_int(3), '^', _int(2))), '2 ^ 3 ^ 2', id='power-tie-on-right'),
        pytest.param(_binary(_binary(_int(2), '^', _int(3)), '^', _int(2)), '(2 ^ 3) ^ 2', id='power-tie-on-left'),
        pytest.param(_binary(_int(2), '^', _binary(_int(3), '*', _int(4))), '2 ^ (3 * 4)', id='product-as-exponent'),

        # Unary signs
        pytest.param(_unary('-', _binary(_int(2), '^', _int(2))), '-2 ^ 2', id='sign-over-power'),
        pytest.param(_binary(_unary('-', _int(2)), '^', _int(2)), '(-2) ^ 2', id='signed-base'),
        pytest.param(_binary(_int(2), '^', _unary('-', _int(1))), '2 ^ -1', id='signed-exponent'),
        pytest.param(_unary('-', _binary(_var('a'), '+', _var('b'))), '-(a + b)', id='sign-over-sum'),
        pytest.param(_unary('-', _binary(_int(2), '*', _int(3))), '-(2 * 3)', id='sign-over-product'),
        pytest.param(_binary(_int(2), '*', _unary('-', _int(3))), '2 * -3', id='signed-right-operand'),
        pytest.param(_binary(_var('a'), '/', _unary('-', _var('b'))), 'a / -b', id='signed-divisor'),
        pytest.param(_unary('-', _unary('-', _var('x'))), '--x', id='nested-signs'),

        # Calls and indexing are always atomic
        pytest.param(ast.FunctionCallNode('sin', _binary(_var('x'), '+', _int(1))), 'sin(x + 1)', id='call-argument-needs-no-extra-parens'),
        pytest.param(_binary(ast.FunctionCallNode('sin', _var('x')), '^', _int(2)), 'sin(x) ^ 2', id='call-as-base'),
        pytest.param(_binary(ast.IndexedVariableNode('x', 0), '^', _int(2)), 'x[0] ^ 2', id='indexed-variable-as-base'),

        # Negative numbers only come from transformations, and behave like a signed number
        pytest.param(ast.NumberNode(-1), '-1', id='negative-number'),
        pytest.param(_binary(ast.NumberNode(-2), '^', _int(2)), '(-2) ^ 2', id='negative-number-as-base'),
        pytest.param(_binary(_var('x'), '^', ast.NumberNode(-1)), 'x ^ -1', id='negative-number-as-exponent'),
        pytest.param(_binary(_var('x'), '-', ast.NumberNode(-1)), 'x - -1', id='negative-number-after-minus'),
    ],
)
def test_to_string(tree: ast.Node, expected: str):
    assert printer.to_string(tree) == expected


def test_unsupported_operator_raises():
    with pytest.raises(ValueError):
        printer.to_string(_binary(_int(1), '?', _int(2)))


def test_unknown_node_raises():
    with pytest.raises(ValueError):
        printer.to_string(ast.Node())
