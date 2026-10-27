import math

import pytest

from pyparser import Expression


@pytest.mark.parametrize(
    ('order', 'expected'),
    [
        pytest.param(0, 1.5 ** 4, id='zeroth'),
        pytest.param(1, 4 * 1.5 ** 3, id='first'),
        pytest.param(2, 12 * 1.5 ** 2, id='second'),
        pytest.param(3, 24 * 1.5, id='third'),
        pytest.param(4, 24, id='fourth'),
        pytest.param(5, 0, id='fifth'),
    ],
)
def test_nth_derivative_of_power(order: int, expected: float):
    derivative = Expression('x ^ 4', ['x']).differentiate('x', order)

    assert derivative.evaluate({'x': 1.5}) == pytest.approx(expected)


@pytest.mark.parametrize(
    ('order', 'expected'),
    [
        pytest.param(1, math.cos, id='first-is-cos'),
        pytest.param(2, lambda x: -math.sin(x), id='second-is-minus-sin'),
        pytest.param(3, lambda x: -math.cos(x), id='third-is-minus-cos'),
        pytest.param(4, math.sin, id='fourth-is-sin'),
        pytest.param(8, math.sin, id='eighth-is-sin'),
    ],
)
@pytest.mark.parametrize('point', [-2.0, 0.0, 0.4, 3.0])
def test_nth_derivative_of_sin(order: int, expected, point: float):
    derivative = Expression('sin(x)', ['x']).differentiate('x', order)

    assert derivative.evaluate({'x': point}) == pytest.approx(expected(point))


@pytest.mark.parametrize(
    ('first', 'second'),
    [
        pytest.param('x', 'y', id='x-then-y'),
        pytest.param('y', 'x', id='y-then-x'),
    ],
)
@pytest.mark.parametrize(('x', 'y'), [(1.0, 1.0), (2.0, -1.5), (-0.5, 3.0)])
def test_mixed_partial_derivatives(first: str, second: str, x: float, y: float):
    mixed = Expression('x ^ 2 * y ^ 3', ['x', 'y']).differentiate(first).differentiate(second)

    assert mixed.evaluate({'x': x, 'y': y}) == pytest.approx(6 * x * y ** 2)


def test_mixed_partial_derivatives_of_indexed_variables():
    mixed = Expression('x[0] ^ 3 * sin(x[1])', ['x']).differentiate('x[0]', 2).differentiate('x[1]')

    assert mixed.evaluate({'x': [2.0, 0.5]}) == pytest.approx(6 * 2.0 * math.cos(0.5))


def test_derivative_keeps_variables_it_no_longer_uses():
    derivative = Expression('x + y', ['x', 'y']).differentiate('x')

    assert derivative.variables == ('x', 'y')
    assert derivative.evaluate({'x': 5, 'y': 7}) == 1


def test_derivative_prints_and_round_trips():
    derivative = Expression('x * sin(x)', ['x']).differentiate('x')

    assert str(derivative) == '1 * sin(x) + x * (cos(x) * 1)'
    assert Expression(str(derivative), derivative.variables) == derivative


def test_gradient_at_points():
    gradient = Expression('x * y ^ 2 + sin(x)', ['x', 'y']).gradient()

    assert [partial.evaluate({'x': 1, 'y': 2}) for partial in gradient] == pytest.approx([4 + math.cos(1), 4])
    assert [partial.evaluate({'x': 0, 'y': -1}) for partial in gradient] == pytest.approx([2, 0])


def test_gradient_descent_converges():
    function = Expression('(x - 3) ^ 2 + 2 * (y + 1) ^ 2', ['x', 'y'])
    gradient = function.gradient()
    point = {'x': 0.0, 'y': 0.0}

    for _ in range(100):
        slopes = [partial.evaluate(point) for partial in gradient]
        point = {name: point[name] - 0.1 * slope for name, slope in zip(function.variables, slopes)}

    assert point == pytest.approx({'x': 3, 'y': -1})
    assert function.evaluate(point) == pytest.approx(0)


def test_gradient_descent_over_indexed_variable():
    function = Expression('(w[0] - 1) ^ 2 + (w[1] + 2) ^ 2 + (w[2] - 0.5) ^ 2', ['w'])
    names = [f'w[{i}]' for i in range(3)]
    gradient = function.gradient(names)
    weights = [0.0, 0.0, 0.0]

    for _ in range(100):
        slopes = [partial.evaluate({'w': weights}) for partial in gradient]
        weights = [weight - 0.1 * slope for weight, slope in zip(weights, slopes)]

    assert weights == pytest.approx([1, -2, 0.5])


@pytest.mark.parametrize('order', [1, 2, 3, 4])
@pytest.mark.parametrize('point', [-1.0, 0.0, 0.5, 2.0])
def test_every_derivative_of_exp_is_itself(order: int, point: float):
    derivative = Expression('e ^ x', ['x']).differentiate('x', order)

    assert derivative.evaluate({'x': point}) == pytest.approx(math.exp(point))


def test_derivative_of_sin_with_pi():
    derivative = Expression('sin(pi * x)', ['x']).differentiate('x')

    assert derivative.evaluate({'x': 0.25}) == pytest.approx(math.pi * math.cos(math.pi / 4))
