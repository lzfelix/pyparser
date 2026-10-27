import pytest
from pyparser.errors import DifferentiationError
from pyparser.operations.differentiator import differentiate
from pyparser.parser import ast


_X = ast.VariableNode('x')
_Y = ast.VariableNode('y')
_X0 = ast.IndexedVariableNode('x', 0)
_X1 = ast.IndexedVariableNode('x', 1)
_ZERO = ast.NumberNode(0)
_ONE = ast.NumberNode(1)


def _int(i: int) -> ast.NumberNode:
    return ast.NumberNode(i)


def _unary(operator: str, expr: ast.Node) -> ast.UnaryNode:
    return ast.UnaryNode(operator, expr)


def _binary(left: ast.Node, operator: str, right: ast.Node) -> ast.BinaryNode:
    return ast.BinaryNode(left, operator, right)


def _call(name: str, arg: ast.Node) -> ast.FunctionCallNode:
    return ast.FunctionCallNode(name, arg)


@pytest.mark.parametrize(
    ('tree', 'var', 'expected'),
    [
        # Leaves
        pytest.param(_int(3), _X, _ZERO, id='number'),
        pytest.param(ast.NumberNode(2.5), _X, _ZERO, id='float'),
        pytest.param(_X, _X, _ONE, id='same-variable'),
        pytest.param(_Y, _X, _ZERO, id='other-variable'),
        pytest.param(_X0, _X0, _ONE, id='same-indexed-variable'),
        pytest.param(_X1, _X0, _ZERO, id='other-index'),
        pytest.param(_X0, _X, _ZERO, id='indexed-is-not-plain'),

        # Constant subtrees
        pytest.param(_binary(_int(3), '*', _Y), _X, _ZERO, id='constant-product'),
        pytest.param(_call('sin', _binary(_Y, '^', _int(2))), _X, _ZERO, id='constant-call'),
        pytest.param(_unary('-', _binary(_Y, '/', _int(2))), _X, _ZERO, id='constant-unary'),
        pytest.param(_binary(_int(2), '^', _int(3)), _X, _ZERO, id='constant-power'),

        # Signs: (±u)' = ±u'
        pytest.param(_unary('-', _X), _X, _unary('-', _ONE), id='negation'),
        pytest.param(_unary('+', _X), _X, _unary('+', _ONE), id='unary-plus'),

        # Sum and difference: (u ± v)' = u' ± v'
        pytest.param(_binary(_X, '+', _Y), _X, _binary(_ONE, '+', _ZERO), id='sum'),
        pytest.param(_binary(_int(3), '-', _X), _X, _binary(_ZERO, '-', _ONE), id='difference'),

        # Product: (u * v)' = u' * v + u * v'
        pytest.param(
            _binary(_X, '*', _Y),
            _X,
            _binary(_binary(_ONE, '*', _Y), '+', _binary(_X, '*', _ZERO)),
            id='product',
        ),
        pytest.param(
            _binary(_X0, '*', _X1),
            _X0,
            _binary(_binary(_ONE, '*', _X1), '+', _binary(_X0, '*', _ZERO)),
            id='product-of-indexed-variables',
        ),

        # Quotient: (u / v)' = (u' * v - u * v') / v ^ 2
        pytest.param(
            _binary(_X, '/', _Y),
            _X,
            _binary(
                _binary(_binary(_ONE, '*', _Y), '-', _binary(_X, '*', _ZERO)),
                '/',
                _binary(_Y, '^', _int(2)),
            ),
            id='quotient',
        ),

        # Constant exponent: (u ^ n)' = n * u ^ (n - 1) * u'
        pytest.param(
            _binary(_X, '^', _int(3)),
            _X,
            _binary(_binary(_int(3), '*', _binary(_X, '^', _binary(_int(3), '-', _ONE))), '*', _ONE),
            id='constant-exponent',
        ),

        # Constant base: (a ^ v)' = a ^ v * log(a) * v'
        pytest.param(
            _binary(_int(2), '^', _X),
            _X,
            _binary(_binary(_binary(_int(2), '^', _X), '*', _call('log', _int(2))), '*', _ONE),
            id='constant-base',
        ),

        # Both vary: (u ^ v)' = u ^ v * (v' * log(u) + v * (u' / u))
        pytest.param(
            _binary(_X, '^', _X),
            _X,
            _binary(
                _binary(_X, '^', _X),
                '*',
                _binary(
                    _binary(_ONE, '*', _call('log', _X)),
                    '+',
                    _binary(_X, '*', _binary(_ONE, '/', _X)),
                ),
            ),
            id='variable-base-and-exponent',
        ),

        # Chain rule: f(u)' = f'(u) * u'
        pytest.param(_call('sin', _X), _X, _binary(_call('cos', _X), '*', _ONE), id='function-call'),
        pytest.param(
            _call('sin', _binary(_X, '*', _int(2))),
            _X,
            _binary(
                _call('cos', _binary(_X, '*', _int(2))),
                '*',
                _binary(_binary(_ONE, '*', _int(2)), '+', _binary(_X, '*', _ZERO)),
            ),
            id='function-call-of-expression',
        ),
        pytest.param(
            _call('log', _call('cos', _X)),
            _X,
            _binary(
                _binary(_ONE, '/', _call('cos', _X)),
                '*',
                _binary(_unary('-', _call('sin', _X)), '*', _ONE),
            ),
            id='nested-function-calls',
        ),
    ],
)
def test_differentiate(tree: ast.Node, var: ast.Node, expected: ast.Node):
    assert differentiate(tree, var) == expected


@pytest.mark.parametrize(
    'exponent',
    [
        pytest.param(_int(0), id='int'),
        pytest.param(ast.NumberNode(0.0), id='float'),
    ],
)
def test_zero_exponent_gives_zero(exponent: ast.Node):
    assert differentiate(_binary(_X, '^', exponent), _X) == _ZERO


def test_zero_exponent_of_expression_gives_zero():
    assert differentiate(_binary(_call('sin', _X), '^', _int(0)), _X) == _ZERO


def test_constant_exponent_does_not_introduce_log():
    derivative = differentiate(_binary(_X, '^', _int(2)), _X)

    assert 'log' not in repr(derivative)


def test_unknown_function_raises():
    with pytest.raises(DifferentiationError) as exc_info:
        differentiate(ast.FunctionCallNode('etan', _X, position=4), _X)
    assert exc_info.value.position == 4


def test_unknown_function_without_var_is_constant():
    assert differentiate(_call('etan', _Y), _X) == _ZERO


def test_unsupported_operator_raises():
    with pytest.raises(DifferentiationError):
        differentiate(_binary(_X, '?', _int(1)), _X)


def test_unsupported_operator_without_var_is_constant():
    assert differentiate(_binary(_Y, '?', _int(1)), _X) == _ZERO


@pytest.mark.parametrize(
    'var',
    [
        pytest.param(ast.VariableNode('e'), id='e'),
        pytest.param(ast.VariableNode('pi'), id='pi'),
        pytest.param(ast.IndexedVariableNode('pi', 0), id='indexed-constant'),
    ],
)
def test_differentiating_wrt_constant_raises(var: ast.Node):
    with pytest.raises(DifferentiationError):
        differentiate(_binary(var, '*', _X), var)


@pytest.mark.parametrize('name', ['e', 'pi'])
def test_constant_differentiates_to_zero(name: str):
    assert differentiate(ast.VariableNode(name), _X) == _ZERO


def test_uppercase_constant_name_is_a_variable():
    E = ast.VariableNode('E')

    assert differentiate(E, E) == _ONE


def test_power_of_e_uses_constant_base_rule():
    # e ^ x  ->  e ^ x * log(e) * 1
    e = ast.VariableNode('e')
    power = _binary(e, '^', _X)

    assert differentiate(power, _X) == _binary(_binary(power, '*', _call('log', e)), '*', _ONE)
