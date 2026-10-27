import math

import pytest
from pyparser.errors import EvaluationError
from pyparser.operations import evaluator
from pyparser.parser import ast


def _int(i: int) -> ast.NumberNode:
    return ast.NumberNode(i)


def _float(f: float) -> ast.NumberNode:
    return ast.NumberNode(f)


def _var(name: str, position: int | None = None) -> ast.VariableNode:
    return ast.VariableNode(name, position=position)


def _indexed(name: str, index: int, position: int | None = None) -> ast.IndexedVariableNode:
    return ast.IndexedVariableNode(name, index, position=position)


def _unary(operator: str, expr: ast.Node) -> ast.UnaryNode:
    return ast.UnaryNode(operator, expr)


def _binary(left: ast.Node, operator: str, right: ast.Node) -> ast.BinaryNode:
    return ast.BinaryNode(left, operator, right)


def test_int_number_evaluates_to_its_value():
    assert evaluator.evaluate(_int(3)) == 3


def test_float_number_evaluates_to_its_value():
    assert evaluator.evaluate(_float(3.14)) == 3.14


def test_unary_plus_keeps_value():
    assert evaluator.evaluate(_unary('+', _int(3))) == 3


def test_unary_minus_negates_value():
    assert evaluator.evaluate(_unary('-', _int(3))) == -3


def test_nested_unary_minus_cancels_out():
    # --3
    assert evaluator.evaluate(_unary('-', _unary('-', _int(3)))) == 3


def test_addition():
    assert evaluator.evaluate(_binary(_int(3), '+', _int(2))) == 5


def test_subtraction():
    assert evaluator.evaluate(_binary(_int(3), '-', _int(5))) == -2


def test_multiplication():
    assert evaluator.evaluate(_binary(_int(3), '*', _int(4))) == 12


def test_division():
    assert evaluator.evaluate(_binary(_int(7), '/', _int(2))) == 3.5


def test_division_of_ints_returns_float():
    result = evaluator.evaluate(_binary(_int(6), '/', _int(3)))

    assert result == 2
    assert isinstance(result, float)


def test_mixed_int_and_float_operands():
    assert evaluator.evaluate(_binary(_float(1.5), '*', _int(2))) == 3.0


def test_nested_binary_follows_tree_structure():
    # (3 - 2) - 1, as the parser builds left-associative trees
    left_assoc = _binary(_binary(_int(3), '-', _int(2)), '-', _int(1))
    # 3 - (2 - 1)
    right_assoc = _binary(_int(3), '-', _binary(_int(2), '-', _int(1)))

    assert evaluator.evaluate(left_assoc) == 0
    assert evaluator.evaluate(right_assoc) == 2


def test_unary_applied_to_binary_expression():
    # -(3 + 2)
    assert evaluator.evaluate(_unary('-', _binary(_int(3), '+', _int(2)))) == -5


def test_division_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        evaluator.evaluate(_binary(_int(2), '/', _int(0)))


def test_unknown_node_raises():
    with pytest.raises(EvaluationError):
        evaluator.evaluate(ast.Node())


def test_unsupported_binary_operator_raises():
    with pytest.raises(EvaluationError):
        evaluator.evaluate(_binary(_int(2), '?', _int(3)))


def test_unsupported_unary_operator_raises():
    with pytest.raises(EvaluationError):
        evaluator.evaluate(_unary('*', _int(3)))


def test_variable_evaluates_to_its_value():
    assert evaluator.evaluate(_var('x'), {'x': 3}) == 3


def test_variable_can_hold_float():
    assert evaluator.evaluate(_var('x'), {'x': 2.5}) == 2.5


def test_variables_inside_binary_expression():
    # x * y
    assert evaluator.evaluate(_binary(_var('x'), '*', _var('y')), {'x': 3, 'y': 4}) == 12


def test_variable_used_multiple_times():
    # x * x
    assert evaluator.evaluate(_binary(_var('x'), '*', _var('x')), {'x': 5}) == 25


def test_unary_applied_to_variable():
    # -x
    assert evaluator.evaluate(_unary('-', _var('x')), {'x': 3}) == -3


def test_unused_variables_are_ignored():
    assert evaluator.evaluate(_int(3), {'x': 1}) == 3


def test_undefined_variable_raises():
    with pytest.raises(EvaluationError):
        evaluator.evaluate(_var('x'), {'y': 1})


def test_variable_without_bindings_raises():
    with pytest.raises(EvaluationError):
        evaluator.evaluate(_var('x'))


def test_undefined_variable_error_has_position():
    with pytest.raises(EvaluationError) as exc_info:
        evaluator.evaluate(_binary(_int(2), '+', _var('x', position=2)), {})
    assert exc_info.value.position == 2


def test_variable_names_are_case_sensitive():
    with pytest.raises(EvaluationError):
        evaluator.evaluate(_var('X'), {'x': 1})


def test_power():
    assert evaluator.evaluate(_binary(_int(2), '^', _int(3))) == 8


def test_power_of_zero_exponent_is_one():
    assert evaluator.evaluate(_binary(_int(5), '^', _int(0))) == 1


def test_power_with_negative_exponent():
    assert evaluator.evaluate(_binary(_int(2), '^', _unary('-', _int(1)))) == 0.5


def test_power_with_fractional_exponent():
    assert evaluator.evaluate(_binary(_int(9), '^', _float(0.5))) == 3.0


def test_nested_power_follows_tree_structure():
    # 2 ^ (3 ^ 2)
    right_assoc = _binary(_int(2), '^', _binary(_int(3), '^', _int(2)))
    # (2 ^ 3) ^ 2
    left_assoc = _binary(_binary(_int(2), '^', _int(3)), '^', _int(2))

    assert evaluator.evaluate(right_assoc) == 512
    assert evaluator.evaluate(left_assoc) == 64


def test_power_with_variables():
    # x ^ n
    assert evaluator.evaluate(_binary(_var('x'), '^', _var('n')), {'x': 3, 'n': 2}) == 9


def test_indexed_variable_evaluates_to_its_item():
    assert evaluator.evaluate(_indexed('x', 1), {'x': [10, 20, 30]}) == 20


def test_indexed_variable_accepts_tuples():
    assert evaluator.evaluate(_indexed('x', 0), {'x': (1.5, 2.5)}) == 1.5


def test_indexed_variables_inside_binary_expression():
    # x[0] * x[2]
    assert evaluator.evaluate(_binary(_indexed('x', 0), '*', _indexed('x', 2)), {'x': [2, 0, 5]}) == 10


def test_undefined_indexed_variable_raises():
    with pytest.raises(EvaluationError):
        evaluator.evaluate(_indexed('x', 0), {})


def test_index_out_of_range_raises():
    with pytest.raises(EvaluationError) as exc_info:
        evaluator.evaluate(_indexed('x', 3, position=4), {'x': [1, 2, 3]})
    assert exc_info.value.position == 4


def test_negative_index_raises():
    # The parser can't produce a negative index, but the evaluator must not
    # fall back to Python's "count from the end" semantics either
    with pytest.raises(EvaluationError):
        evaluator.evaluate(_indexed('x', -1), {'x': [1, 2, 3]})


def test_indexing_single_value_raises():
    with pytest.raises(EvaluationError):
        evaluator.evaluate(_indexed('y', 0), {'y': 2.0})


def test_multiple_values_without_index_raises():
    with pytest.raises(EvaluationError) as exc_info:
        evaluator.evaluate(_binary(_var('x', position=0), '+', _int(1)), {'x': [1, 2, 3]})
    assert exc_info.value.position == 0


@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        pytest.param('e', math.e, id='e'),
        pytest.param('pi', math.pi, id='pi'),
    ],
)
def test_constant_evaluates_to_its_value(name: str, expected: float):
    assert evaluator.evaluate(_var(name)) == expected


def test_constant_inside_binary_expression():
    # 2 * pi
    assert evaluator.evaluate(_binary(_int(2), '*', _var('pi'))) == 2 * math.pi


def test_constant_alongside_variables():
    # x * e
    assert evaluator.evaluate(_binary(_var('x'), '*', _var('e')), {'x': 2}) == 2 * math.e


@pytest.mark.parametrize(
    'variables',
    [
        pytest.param({'pi': 3}, id='pi'),
        pytest.param({'e': 2.7}, id='e'),
        pytest.param({'x': 1, 'e': [1, 2]}, id='sequence-among-other-variables'),
    ],
)
def test_binding_constant_raises(variables: dict):
    with pytest.raises(EvaluationError):
        evaluator.evaluate(_var('pi'), variables)


def test_binding_constant_raises_even_when_unused():
    with pytest.raises(EvaluationError):
        evaluator.evaluate(_int(3), {'e': 1})


def test_binding_constants_error_lists_names():
    with pytest.raises(EvaluationError) as exc_info:
        evaluator.evaluate(_var('x'), {'pi': 3, 'x': 1, 'e': 2})
    assert '"pi"' in exc_info.value.message
    assert '"e"' in exc_info.value.message
    assert '"x"' not in exc_info.value.message


@pytest.mark.parametrize('name', ['E', 'PI', 'Pi'])
def test_constant_names_are_case_sensitive(name: str):
    assert evaluator.evaluate(_var(name), {name: 5}) == 5


def test_indexing_constant_raises():
    with pytest.raises(EvaluationError) as exc_info:
        evaluator.evaluate(_indexed('pi', 0, position=3))
    assert exc_info.value.position == 3
