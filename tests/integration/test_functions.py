import pytest

from pyparser.functions import BUILTINS
from pyparser.operations import evaluator
from pyparser.parser import ast


def _numerical_derivative(f, x: float, h: float = 1e-6) -> float:
    return (f(x + h) - f(x - h)) / (2 * h)


@pytest.mark.parametrize(
    ('name', 'points'),
    [
        pytest.param('sin', [-2.0, 0.0, 0.5, 3.0], id='sin'),
        pytest.param('cos', [-2.0, 0.0, 0.5, 3.0], id='cos'),
        pytest.param('tan', [-1.0, 0.0, 0.5, 1.2], id='tan'),
        pytest.param('log', [0.1, 1.0, 2.5, 10.0], id='log'),
        pytest.param('sqrt', [0.1, 1.0, 2.5, 10.0], id='sqrt'),
    ],
)
def test_derivative_matches_numerical_derivative(name: str, points: list[float]):
    function = BUILTINS[name]
    derivative = function.derivative(ast.VariableNode('u'))

    for point in points:
        expected = _numerical_derivative(function.implementation, point)
        assert evaluator.evaluate(derivative, {'u': point}) == pytest.approx(expected, rel=1e-6)
