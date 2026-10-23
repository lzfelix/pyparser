import pytest
from pyparser.errors import EvaluationError
from pyparser.evaluators import evaluator
from pyparser.parser import ast


def _int(i: int) -> ast.NumberNode:
    return ast.NumberNode(i)


def _float(f: float) -> ast.NumberNode:
    return ast.NumberNode(f)


def _var(name: str, position: int | None = None) -> ast.VariableNode:
    return ast.VariableNode(name, position=position)


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
