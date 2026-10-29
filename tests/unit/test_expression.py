import math

import pytest

from pyparser import Expression
from pyparser.errors import EvaluationError, ExpressionError, ParserError, TokenizerError
from pyparser.parser import ast


_X = ast.VariableNode('x')
_Y = ast.VariableNode('y')


def test_is_exported_from_package():
    import pyparser

    assert pyparser.Expression is Expression


@pytest.mark.parametrize(
    ('source', 'expected_tree', 'expected_variables'),
    [
        pytest.param('42', ast.NumberNode(42), (), id='no-variables'),
        pytest.param('x * y', ast.BinaryNode(_X, '*', _Y), ('x', 'y'), id='plain-variables'),
        pytest.param('x[0]', ast.IndexedVariableNode('x', 0), ('x',), id='indexed-variable'),
        pytest.param('sin(x)', ast.FunctionCallNode('sin', _X), ('x',), id='function-name-is-not-a-variable'),
        pytest.param('if + class', ast.BinaryNode(ast.VariableNode('if'), '+', ast.VariableNode('class')), ('class', 'if'), id='python-keywords'),
    ],
)
def test_construction(source: str, expected_tree: ast.Node, expected_variables: tuple[str, ...]):
    expression = Expression(source)

    assert expression.tree == expected_tree
    assert expression.variables == expected_variables


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        pytest.param('b + a', ('a', 'b'), id='sorted-by-name'),
        pytest.param('y * x', ('x', 'y'), id='not-in-order-of-appearance'),
        pytest.param('x * y + x ^ 2', ('x', 'y'), id='repeated-variable-listed-once'),
        pytest.param('x[1] + y + x[0]', ('x', 'y'), id='indexed-uses-listed-by-name'),
        pytest.param('2 * pi * r + e', ('r',), id='constants-are-not-variables'),
        pytest.param('PI * x', ('PI', 'x'), id='constants-are-case-sensitive'),
    ],
)
def test_variables_come_from_the_source(source: str, expected: tuple[str, ...]):
    assert Expression(source).variables == expected


@pytest.mark.parametrize(
    ('source', 'error'),
    [
        pytest.param('x $ 2', TokenizerError, id='tokenizer-error'),
        pytest.param('x +', ParserError, id='parser-error'),
    ],
)
def test_syntax_errors_propagate(source: str, error: type[Exception]):
    with pytest.raises(error):
        Expression(source)


def test_indexing_constant_raises_with_position():
    with pytest.raises(ExpressionError) as exc_info:
        Expression('2 * pi[0]')
    assert exc_info.value.position == 4


@pytest.mark.parametrize(
    ('source', 'values', 'expected'),
    [
        pytest.param('2 * 3', {}, 6, id='no-variables'),
        pytest.param('2 * x + y', {'x': 3, 'y': 2.5}, 8.5, id='plain-variables'),
        pytest.param('x[0] * x[1] + y', {'x': [2, 3], 'y': 1}, 7, id='indexed-variables'),
        pytest.param('if * class', {'if': 2, 'class': 3}, 6, id='python-keywords'),
        pytest.param('2 * pi * r', {'r': 1}, 2 * math.pi, id='constants'),
    ],
)
def test_evaluate(source: str, values: dict, expected: float):
    assert Expression(source).evaluate(values) == pytest.approx(expected)


def test_evaluate_reuses_expression():
    expression = Expression('2 * x + y')

    assert expression.evaluate({'x': 3, 'y': 2.5}) == 8.5
    assert expression.evaluate({'x': 1, 'y': 0}) == 2


@pytest.mark.parametrize(
    'values',
    [
        pytest.param({'x': 1}, id='missing-variable'),
        pytest.param({'x': 1, 'y': 2, 'z': 3}, id='unknown-variable'),
        pytest.param({'y': 2, 'z': 3}, id='missing-and-unknown'),
        pytest.param({'x': 1, 'y': 2, 'pi': 3}, id='constant'),
    ],
)
def test_evaluate_requires_exactly_the_variables(values: dict):
    with pytest.raises(ExpressionError):
        Expression('x + y').evaluate(values)


def test_evaluation_errors_propagate():
    with pytest.raises(EvaluationError):
        Expression('log(x)').evaluate({'x': 0})


def test_differentiate_returns_new_expression():
    expression = Expression('x * y')

    derivative = expression.differentiate('x')

    assert isinstance(derivative, Expression)
    assert derivative is not expression
    assert derivative.tree == _Y
    assert expression.tree == ast.BinaryNode(_X, '*', _Y)


def test_derivative_keeps_the_variables_of_the_original():
    derivative = Expression('x + y').differentiate('x')

    assert str(derivative) == '1'
    assert derivative.variables == ('x', 'y')
    assert derivative.evaluate({'x': 2, 'y': 3}) == 1
    assert str(derivative.differentiate('y')) == '0'


@pytest.mark.parametrize(
    ('var', 'expected'),
    [
        pytest.param('x', 'y', id='plain'),
        pytest.param('y', 'x', id='other-plain'),
    ],
)
def test_differentiate_plain_variables(var: str, expected: str):
    assert str(Expression('x * y').differentiate(var)) == expected


@pytest.mark.parametrize(
    ('var', 'expected'),
    [
        pytest.param('x[0]', 'x[1]', id='first-index'),
        pytest.param('x[1]', 'x[0]', id='second-index'),
        pytest.param(' x [ 1 ] ', 'x[0]', id='whitespace'),
    ],
)
def test_differentiate_indexed_variables(var: str, expected: str):
    assert str(Expression('x[0] * x[1]').differentiate(var)) == expected


def test_differentiate_order_zero_returns_same_object():
    expression = Expression('x ^ 2')

    assert expression.differentiate('x', order=0) is expression


@pytest.mark.parametrize(
    ('order', 'expected'),
    [
        pytest.param(1, 24, id='first'),
        pytest.param(2, 24, id='second'),
        pytest.param(3, 12, id='third'),
        pytest.param(4, 0, id='fourth'),
    ],
)
def test_differentiate_order(order: int, expected: float):
    assert Expression('2 * x ^ 3').differentiate('x', order).evaluate({'x': 2}) == pytest.approx(expected)


def test_differentiate_order_matches_repeated_differentiation():
    expression = Expression('x ^ 3 * sin(x)')

    assert expression.differentiate('x', 3) == expression.differentiate('x').differentiate('x').differentiate('x')


@pytest.mark.parametrize(
    'order',
    [
        pytest.param(-1, id='negative'),
        pytest.param(1.0, id='float'),
        pytest.param('2', id='string'),
        pytest.param(True, id='bool'),
        pytest.param(None, id='none'),
    ],
)
def test_differentiate_invalid_order_raises(order):
    with pytest.raises(ExpressionError):
        Expression('x').differentiate('x', order)


@pytest.mark.parametrize(
    'var',
    [
        pytest.param('z', id='not-a-variable'),
        pytest.param('X', id='case-sensitive'),
        pytest.param('x[0]', id='indexed-when-only-plain-is-used'),
        pytest.param('', id='empty'),
        pytest.param('x +', id='syntax-error'),
        pytest.param('x $', id='invalid-character'),
        pytest.param('2 * x', id='expression'),
        pytest.param('-x', id='negated'),
        pytest.param('sin(x)', id='function-call'),
        pytest.param('sin', id='function-name'),
        pytest.param('x[y]', id='variable-index'),
        pytest.param(_X, id='node-instead-of-string'),
    ],
)
def test_differentiate_with_respect_to_non_variable_raises(var):
    with pytest.raises(ExpressionError):
        Expression('x * sin(y)').differentiate(var)


@pytest.mark.parametrize(
    'var',
    [
        pytest.param('x', id='plain-when-only-indexed-is-used'),
        pytest.param('x[2]', id='absent-index'),
    ],
)
def test_differentiate_requires_the_exact_indexed_variable(var: str):
    with pytest.raises(ExpressionError):
        Expression('x[0] * x[1]').differentiate(var)


def test_differentiate_validates_variable_for_order_zero():
    with pytest.raises(ExpressionError):
        Expression('x').differentiate('z', order=0)


@pytest.mark.parametrize('var', ['e', 'pi', 'pi[0]'])
def test_differentiate_with_respect_to_constant_raises(var: str):
    with pytest.raises(ExpressionError):
        Expression('e ^ x * pi').differentiate(var)


def test_differentiate_treats_constants_as_constants():
    assert Expression('pi * x').differentiate('x').evaluate({'x': 5}) == pytest.approx(math.pi)


def test_gradient_covers_every_variable_sorted_by_name_then_index():
    expression = Expression('y * x[10] + x[2] + w')

    assert expression.gradient() == (
        expression.differentiate('w'),
        expression.differentiate('x[2]'),
        expression.differentiate('x[10]'),
        expression.differentiate('y'),
    )


def test_gradient_matches_variables_order():
    expression = Expression('y ^ 2 + 3 * x')

    assert expression.variables == ('x', 'y')
    assert [partial.evaluate({'x': 1, 'y': 5}) for partial in expression.gradient()] == [3, 10]


def test_gradient_of_no_variables_is_empty():
    assert Expression('3').gradient() == ()


def test_gradient_is_simplified():
    assert [str(partial) for partial in Expression('x * y + 3 * x').gradient()] == ['y + 3', 'x']


def test_higher_order_derivatives_are_simplified_at_every_order():
    assert str(Expression('x * sin(x)').differentiate('x', 3)) == '-sin(x) + (-sin(x) + (-sin(x) + x * -cos(x)))'


def test_source_is_not_simplified():
    assert str(Expression('x * 1 + 0')) == 'x * 1 + 0'


def test_simplify():
    expression = Expression('2 * 3 * x ^ 1 + 0 * y')

    simplified = expression.simplify()

    assert str(simplified) == '6 * x'
    assert str(expression) == '2 * 3 * x ^ 1 + 0 * y'


def test_simplify_keeps_the_variables_of_the_original():
    simplified = Expression('x + 0 * y').simplify()

    assert simplified.variables == ('x', 'y')
    assert simplified.evaluate({'x': 2, 'y': 3}) == 2
    assert simplified != Expression('x')


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        pytest.param('((1-2))-(3-4)', '1 - 2 - (3 - 4)', id='normalizes-parentheses'),
        pytest.param('2*x+y', '2 * x + y', id='normalizes-spacing'),
        pytest.param('x[0]^2', 'x[0] ^ 2', id='indexed'),
    ],
)
def test_str_prints_tree(source: str, expected: str):
    assert str(Expression(source)) == expected


def test_repr():
    assert repr(Expression('x*y')) == "Expression('x * y')"


def test_repr_round_trips():
    expression = Expression('x * (y + 1)')

    assert eval(repr(expression), {'Expression': Expression}) == expression


@pytest.mark.parametrize(
    ('left', 'right', 'expected'),
    [
        pytest.param(Expression('x+y'), Expression('(x) + y'), True, id='same-tree'),
        pytest.param(Expression('x+y'), Expression('y+x'), False, id='different-tree'),
        pytest.param(Expression('x + y').differentiate('x'), Expression('1 + 0'), False, id='different-variables'),
    ],
)
def test_equality(left: Expression, right: Expression, expected: bool):
    assert (left == right) is expected


def test_equal_expressions_hash_equally():
    assert len({Expression('x+1'), Expression('x + 1'), Expression('x + 2')}) == 2


def test_not_equal_to_other_types():
    assert Expression('x') != 'x'
    assert Expression('x') != ast.VariableNode('x')


@pytest.mark.parametrize(
    'attribute',
    [
        pytest.param('variables', id='variables-property'),
        pytest.param('tree', id='tree-property'),
        pytest.param('_tree', id='private-tree'),
        pytest.param('_uses', id='private-uses'),
        pytest.param('new_attribute', id='new-attribute'),
    ],
)
def test_is_immutable(attribute: str):
    expression = Expression('x')

    with pytest.raises(AttributeError):
        setattr(expression, attribute, None)
    with pytest.raises(AttributeError):
        delattr(expression, attribute)

    assert expression.tree == _X
    assert expression.variables == ('x',)
