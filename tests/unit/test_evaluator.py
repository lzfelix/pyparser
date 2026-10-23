import pytest
from pyparser.errors import EvaluationError
from pyparser.evaluators import evaluator
from pyparser.lexer import tokens
from pyparser.parser import ast


def _int(i: int) -> ast.TerminalNode:
    return ast.TerminalNode(tokens.IntToken(i, 0))


def _float(f: float) -> ast.TerminalNode:
    return ast.TerminalNode(tokens.FloatToken(f, 0))


def _unary(operator: str, expr: ast.Node) -> ast.UnaryNode:
    return ast.UnaryNode(tokens.OperatorToken(operator, 0), expr)


def _binary(left: ast.Node, operator: str, right: ast.Node) -> ast.BinaryNode:
    return ast.BinaryNode(left, tokens.OperatorToken(operator, 0), right)


def test_int_terminal_evaluates_to_its_value():
    assert evaluator.evaluate(_int(3)) == 3


def test_float_terminal_evaluates_to_its_value():
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
