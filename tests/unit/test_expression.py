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
    ('source', 'variables', 'expected_tree'),
    [
        pytest.param('42', [], ast.NumberNode(42), id='no-variables'),
        pytest.param('x * y', ['x', 'y'], ast.BinaryNode(_X, '*', _Y), id='plain-variables'),
        pytest.param('x[0]', ['x'], ast.IndexedVariableNode('x', 0), id='indexed-variable'),
        pytest.param('x + x[1]', ['x'], ast.BinaryNode(_X, '+', ast.IndexedVariableNode('x', 1)), id='plain-and-indexed'),
        pytest.param('x', ['x', 'unused'], _X, id='unused-declaration'),
        pytest.param('sin(x)', ['x'], ast.FunctionCallNode('sin', _X), id='function-name-needs-no-declaration'),
        pytest.param('if + class', ['if', 'class'], ast.BinaryNode(ast.VariableNode('if'), '+', ast.VariableNode('class')), id='python-keywords'),
    ],
)
def test_construction(source: str, variables: list[str], expected_tree: ast.Node):
    expression = Expression(source, variables)

    assert expression.tree == expected_tree
    assert expression.variables == tuple(variables)


@pytest.mark.parametrize(
    'variables',
    [
        pytest.param(['x', 'y'], id='list'),
        pytest.param(('x', 'y'), id='tuple'),
        pytest.param(iter(['x', 'y']), id='iterator'),
        pytest.param({'x': None, 'y': None}, id='dict-keys'),
    ],
)
def test_variables_accept_any_iterable(variables):
    assert Expression('x * y', variables).variables == ('x', 'y')


def test_variables_keep_declaration_order():
    assert Expression('a + b', ['b', 'a']).variables == ('b', 'a')


@pytest.mark.parametrize(
    ('source', 'variables', 'position'),
    [
        pytest.param('x + y', ['x'], 4, id='undeclared'),
        pytest.param('z * y', ['x'], 0, id='first-undeclared-use-is-reported'),
        pytest.param('x + 2 * sin(y[3])', ['x'], 12, id='undeclared-indexed'),
        pytest.param('X', ['x'], 0, id='case-sensitive'),
    ],
)
def test_undeclared_variable_raises_with_position(source: str, variables: list[str], position: int):
    with pytest.raises(ExpressionError) as error:
        Expression(source, variables)

    assert error.value.position == position


@pytest.mark.parametrize(
    'variables',
    [
        pytest.param(['x', 'x'], id='duplicate'),
        pytest.param(['x', 'y', 'x'], id='non-adjacent-duplicate'),
        pytest.param('xy', id='string-instead-of-collection'),
        pytest.param(['x[0]'], id='indexed-declaration'),
        pytest.param(['x1'], id='invalid-name'),
        pytest.param([''], id='empty-name'),
        pytest.param(['x y'], id='two-names'),
        pytest.param(['2'], id='number'),
        pytest.param([1], id='not-a-string'),
    ],
)
def test_invalid_declaration_raises(variables):
    with pytest.raises(ExpressionError):
        Expression('1', variables)


@pytest.mark.parametrize(
    ('source', 'error'),
    [
        pytest.param('x $ 2', TokenizerError, id='tokenizer-error'),
        pytest.param('x +', ParserError, id='parser-error'),
    ],
)
def test_syntax_errors_propagate(source: str, error: type[Exception]):
    with pytest.raises(error):
        Expression(source, ['x'])


@pytest.mark.parametrize(
    ('source', 'variables', 'values', 'expected'),
    [
        pytest.param('2 * 3', [], {}, 6, id='no-variables'),
        pytest.param('2 * x + y', ['x', 'y'], {'x': 3, 'y': 2.5}, 8.5, id='plain-variables'),
        pytest.param('x[0] * x[1] + y', ['x', 'y'], {'x': [2, 3], 'y': 1}, 7, id='indexed-variables'),
        pytest.param('x', ['x', 'unused'], {'x': 1, 'unused': 5}, 1, id='unused-variable'),
        pytest.param('if * class', ['if', 'class'], {'if': 2, 'class': 3}, 6, id='python-keywords'),
    ],
)
def test_evaluate(source: str, variables: list[str], values: dict, expected: float):
    assert Expression(source, variables).evaluate(values) == expected


def test_evaluate_reuses_expression():
    expression = Expression('2 * x + y', ['x', 'y'])

    assert expression.evaluate({'x': 3, 'y': 2.5}) == 8.5
    assert expression.evaluate({'x': 1, 'y': 0}) == 2


@pytest.mark.parametrize(
    'values',
    [
        pytest.param({'x': 1}, id='missing-variable'),
        pytest.param({'x': 1, 'y': 2, 'z': 3}, id='unknown-variable'),
        pytest.param({'y': 2, 'z': 3}, id='missing-and-unknown'),
    ],
)
def test_evaluate_requires_exactly_the_declared_variables(values: dict):
    with pytest.raises(ExpressionError):
        Expression('x + y', ['x', 'y']).evaluate(values)


def test_evaluate_requires_unused_variables():
    with pytest.raises(ExpressionError):
        Expression('x', ['x', 'y']).evaluate({'x': 1})


def test_evaluation_errors_propagate():
    with pytest.raises(EvaluationError):
        Expression('log(x)', ['x']).evaluate({'x': 0})


def test_differentiate_returns_new_expression():
    expression = Expression('x * y', ['x', 'y'])

    derivative = expression.differentiate('x')

    assert isinstance(derivative, Expression)
    assert derivative is not expression
    assert derivative.variables == ('x', 'y')
    assert derivative.tree == ast.BinaryNode(
        ast.BinaryNode(ast.NumberNode(1), '*', _Y), '+', ast.BinaryNode(_X, '*', ast.NumberNode(0)))
    assert expression.tree == ast.BinaryNode(_X, '*', _Y)


@pytest.mark.parametrize(
    ('var', 'expected'),
    [
        pytest.param('x', '1 * y + x * 0', id='plain'),
        pytest.param('y', '0 * y + x * 1', id='other-plain'),
        pytest.param('x[0]', '0', id='indexed-is-a-different-variable'),
    ],
)
def test_differentiate_plain_variables(var: str, expected: str):
    expression = Expression('x * y', ['x', 'y'])

    assert str(expression.differentiate(var)) == expected


@pytest.mark.parametrize(
    ('var', 'expected'),
    [
        pytest.param('x[0]', '1 * x[1] + x[0] * 0', id='first-index'),
        pytest.param('x[1]', '0 * x[1] + x[0] * 1', id='second-index'),
        pytest.param(' x [ 1 ] ', '0 * x[1] + x[0] * 1', id='whitespace'),
        pytest.param('x[2]', '0', id='absent-index'),
        pytest.param('x', '0', id='plain-is-a-different-variable'),
    ],
)
def test_differentiate_indexed_variables(var: str, expected: str):
    expression = Expression('x[0] * x[1]', ['x'])

    assert str(expression.differentiate(var)) == expected


def test_differentiate_unused_variable_is_zero():
    assert str(Expression('x', ['x', 'y']).differentiate('y')) == '0'


def test_differentiate_order_zero_returns_same_object():
    expression = Expression('x ^ 2', ['x'])

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
    expression = Expression('2 * x ^ 3', ['x'])

    assert expression.differentiate('x', order).evaluate({'x': 2}) == pytest.approx(expected)


def test_differentiate_order_matches_repeated_differentiation():
    expression = Expression('x ^ 3 * sin(x)', ['x'])

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
        Expression('x', ['x']).differentiate('x', order)


@pytest.mark.parametrize(
    'var',
    [
        pytest.param('z', id='undeclared'),
        pytest.param('z[0]', id='undeclared-indexed'),
        pytest.param('', id='empty'),
        pytest.param('x +', id='syntax-error'),
        pytest.param('x $', id='invalid-character'),
        pytest.param('2 * x', id='expression'),
        pytest.param('-x', id='negated'),
        pytest.param('sin(x)', id='function-call'),
        pytest.param('x[y]', id='variable-index'),
        pytest.param(_X, id='node-instead-of-string'),
    ],
)
def test_differentiate_invalid_variable_raises(var):
    with pytest.raises(ExpressionError):
        Expression('x * y', ['x', 'y']).differentiate(var)


def test_differentiate_validates_variable_for_order_zero():
    with pytest.raises(ExpressionError):
        Expression('x', ['x']).differentiate('z', order=0)


def test_gradient_defaults_to_declared_variables():
    expression = Expression('x * y ^ 2', ['y', 'x'])

    assert expression.gradient() == (expression.differentiate('y'), expression.differentiate('x'))


def test_gradient_with_explicit_variables():
    expression = Expression('x[0] * x[1] + y', ['x', 'y'])

    assert expression.gradient(['x[1]', 'y']) == (expression.differentiate('x[1]'), expression.differentiate('y'))


def test_gradient_of_no_variables_is_empty():
    assert Expression('3', []).gradient() == ()


@pytest.mark.parametrize(
    'variables',
    [
        pytest.param('x', id='string-instead-of-collection'),
        pytest.param(['z'], id='undeclared'),
    ],
)
def test_gradient_invalid_variables_raise(variables):
    with pytest.raises(ExpressionError):
        Expression('x', ['x']).gradient(variables)


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        pytest.param('((1-2))-(3-4)', '1 - 2 - (3 - 4)', id='normalizes-parentheses'),
        pytest.param('2*x+y', '2 * x + y', id='normalizes-spacing'),
        pytest.param('x[0]^2', 'x[0] ^ 2', id='indexed'),
    ],
)
def test_str_prints_tree(source: str, expected: str):
    assert str(Expression(source, ['x', 'y'])) == expected


@pytest.mark.parametrize(
    ('expression', 'expected'),
    [
        pytest.param(Expression('x*y', ['x', 'y']), "Expression('x * y', variables=('x', 'y'))", id='several-variables'),
        pytest.param(Expression('x', ['x']), "Expression('x', variables=('x',))", id='one-variable'),
        pytest.param(Expression('1', []), "Expression('1', variables=())", id='no-variables'),
    ],
)
def test_repr(expression: Expression, expected: str):
    assert repr(expression) == expected


def test_repr_round_trips():
    expression = Expression('x * (y + 1)', ['x', 'y'])

    assert eval(repr(expression), {'Expression': Expression}) == expression


@pytest.mark.parametrize(
    ('left', 'right', 'expected'),
    [
        pytest.param(Expression('x+y', ['x', 'y']), Expression('(x) + y', ['x', 'y']), True, id='same-tree-and-variables'),
        pytest.param(Expression('x+y', ['x', 'y']), Expression('y+x', ['x', 'y']), False, id='different-tree'),
        pytest.param(Expression('x+y', ['x', 'y']), Expression('x+y', ['y', 'x']), False, id='different-variable-order'),
        pytest.param(Expression('x', ['x']), Expression('x', ['x', 'y']), False, id='different-variables'),
    ],
)
def test_equality(left: Expression, right: Expression, expected: bool):
    assert (left == right) is expected


def test_equal_expressions_hash_equally():
    assert len({Expression('x+1', ['x']), Expression('x + 1', ['x']), Expression('x + 2', ['x'])}) == 2


def test_not_equal_to_other_types():
    assert Expression('x', ['x']) != 'x'
    assert Expression('x', ['x']) != ast.VariableNode('x')


@pytest.mark.parametrize(
    'attribute',
    [
        pytest.param('variables', id='variables-property'),
        pytest.param('tree', id='tree-property'),
        pytest.param('_tree', id='private-tree'),
        pytest.param('_variables', id='private-variables'),
        pytest.param('new_attribute', id='new-attribute'),
    ],
)
def test_is_immutable(attribute: str):
    expression = Expression('x', ['x'])

    with pytest.raises(AttributeError):
        setattr(expression, attribute, None)
    with pytest.raises(AttributeError):
        delattr(expression, attribute)

    assert expression.tree == _X
    assert expression.variables == ('x',)


@pytest.mark.parametrize(
    ('source', 'variables', 'values', 'expected'),
    [
        pytest.param('pi', [], {}, math.pi, id='pi'),
        pytest.param('2 * pi * r', ['r'], {'r': 1}, 2 * math.pi, id='constant-with-variable'),
        pytest.param('log(e)', [], {}, 1.0, id='e'),
        pytest.param('PI * x', ['PI', 'x'], {'PI': 2, 'x': 3}, 6, id='constants-are-case-sensitive'),
    ],
)
def test_constants_need_no_declaration(source: str, variables: list[str], values: dict, expected: float):
    assert Expression(source, variables).evaluate(values) == pytest.approx(expected)


@pytest.mark.parametrize(
    'variables',
    [
        pytest.param(['x', 'pi'], id='pi'),
        pytest.param(['e'], id='e'),
    ],
)
def test_declaring_constant_raises(variables: list[str]):
    with pytest.raises(ExpressionError):
        Expression('x + 1', variables)


def test_indexing_constant_raises_with_position():
    with pytest.raises(ExpressionError) as exc_info:
        Expression('2 * pi[0]', [])
    assert exc_info.value.position == 4


@pytest.mark.parametrize('var', ['e', 'pi', 'pi[0]'])
def test_differentiate_with_respect_to_constant_raises(var: str):
    with pytest.raises(ExpressionError):
        Expression('e ^ x * pi', ['x']).differentiate(var)


def test_differentiate_treats_constants_as_constants():
    derivative = Expression('pi * x', ['x']).differentiate('x')

    assert derivative.evaluate({'x': 5}) == pytest.approx(math.pi)
