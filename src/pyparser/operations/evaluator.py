import numbers
from collections.abc import Mapping, Sequence

from pyparser import errors
from pyparser.functions import BUILTINS
from pyparser.parser import ast


type Value = int | float | Sequence[int | float]


def evaluate(root: ast.Node, variables: Mapping[str, Value] | None = None) -> int | float:
    variables = variables or {}

    def _evaluate_unary(unary: ast.UnaryNode) -> int | float:
        match unary.operator:
            case '+':
                return _evaluate(unary.expr)
            case '-':
                return -_evaluate(unary.expr)
            case _:
                raise errors.EvaluationError(f'Unsupported unary operation "{unary.operator}"', position=unary.position)

    def _lookup(name: str, position: int | None) -> Value:
        if name not in variables:
            raise errors.EvaluationError(f'Undefined variable "{name}"', position=position)
        return variables[name]

    def _evaluate_variable(variable: ast.VariableNode) -> int | float:
        value = _lookup(variable.name, variable.position)
        if not isinstance(value, numbers.Number):
            raise errors.EvaluationError(
                f'Variable "{variable.name}" holds multiple values and must be indexed',
                position=variable.position,
            )
        return value

    def _evaluate_indexed_variable(variable: ast.IndexedVariableNode) -> int | float:
        values = _lookup(variable.name, variable.position)
        if isinstance(values, numbers.Number):
            raise errors.EvaluationError(
                f'Variable "{variable.name}" holds a single value and cannot be indexed',
                position=variable.position,
            )
        # Negative indices are rejected explicitly instead of letting Python count from the end
        if not 0 <= variable.index < len(values):
            raise errors.EvaluationError(
                f'Index {variable.index} out of range for "{variable.name}" with {len(values)} values',
                position=variable.position,
            )
        return values[variable.index]

    def _evaluate_binary(binary: ast.BinaryNode) -> int | float:
        left = _evaluate(binary.left)
        right = _evaluate(binary.right)

        match binary.operator:
            case '+':
                return left + right
            case '-':
                return left - right
            case '*':
                return left * right
            case '/':
                return left / right  # Delegating division by zero to Python
            case '^':
                return left ** right
            case _:
                raise errors.EvaluationError(f'Unsupported operation "{binary.operator}"', position=binary.position)

    def _evaluate_function(fn_call: ast.FunctionCallNode) -> float:
        fn = BUILTINS.get(fn_call.name)
        if not fn:
            raise errors.EvaluationError(f'Unknown function "{fn_call.name}".', position=fn_call.position)

        fn_arg = _evaluate(fn_call.arg)
        try:
            return fn.implementation(fn_arg)
        except Exception as e:
            raise errors.EvaluationError(
                f'Failed to evaluate "{fn_call.name}({fn_arg})" with error "{e}".',
                position=fn_call.position,
            )

    def _evaluate(node: ast.Node) -> int | float:
        match node:
            case ast.UnaryNode() as unary:
                return _evaluate_unary(unary)
            case ast.NumberNode() as number:
                return number.value
            case ast.VariableNode() as variable:
                return _evaluate_variable(variable)
            case ast.IndexedVariableNode() as variable:
                return _evaluate_indexed_variable(variable)
            case ast.BinaryNode() as binary:
                return _evaluate_binary(binary)
            case ast.FunctionCallNode() as fn_call:
                return _evaluate_function(fn_call)
            case _:
                raise errors.EvaluationError(f'Unexpected AST node {node}')

    return _evaluate(root)
