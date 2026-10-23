import math

import pytest
from pyparser.functions import BUILTINS
from pyparser.parser import ast


_U = ast.VariableNode('u')


def test_builtins_are_keyed_by_their_names():
    assert all(name == function.name for name, function in BUILTINS.items())


def test_builtins_cannot_be_modified():
    with pytest.raises(TypeError):
        BUILTINS['sqrt'] = BUILTINS['sin']


@pytest.mark.parametrize(
    ('name', 'implementation'),
    [
        pytest.param('sin', math.sin, id='sin'),
        pytest.param('cos', math.cos, id='cos'),
        pytest.param('tan', math.tan, id='tan'),
        pytest.param('log', math.log, id='log'),
    ],
)
def test_implementation(name: str, implementation):
    assert BUILTINS[name].implementation is implementation


@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        pytest.param('sin', ast.FunctionCallNode('cos', _U), id='sin'),
        pytest.param('cos', ast.UnaryNode('-', ast.FunctionCallNode('sin', _U)), id='cos'),
        pytest.param(
            'tan',
            ast.BinaryNode(
                ast.NumberNode(1),
                '/',
                ast.BinaryNode(ast.FunctionCallNode('cos', _U), '^', ast.NumberNode(2)),
            ),
            id='tan',
        ),
        pytest.param('log', ast.BinaryNode(ast.NumberNode(1), '/', _U), id='log'),
    ],
)
def test_derivative(name: str, expected: ast.Node):
    assert BUILTINS[name].derivative(_U) == expected


def test_derivative_keeps_the_argument_subtree():
    argument = ast.BinaryNode(ast.VariableNode('x'), '^', ast.NumberNode(2))

    assert BUILTINS['sin'].derivative(argument) == ast.FunctionCallNode('cos', argument)
