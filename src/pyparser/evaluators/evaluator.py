import math
from collections.abc import Mapping

from pyparser import errors
from pyparser.lexer import tokens
from pyparser.parser import ast


_FUNCTIONS = {
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log
}


def evaluate(root: ast.Node, variables: Mapping[str, int | float] | None = None) -> int | float:
    variables = variables or {}

    def _evaluate_unary(unary: ast.UnaryNode) -> int | float:
        match unary.operator.value:
            case '+':
                return _evaluate(unary.expr)
            case '-':
                return -_evaluate(unary.expr)
            case _:
                raise errors.EvaluationError(f'Unsupported unary operation "{unary.operator.value}"')

    def _evaluate_terminal(terminal: ast.TerminalNode) -> int | float:
        match terminal.expr:
            case tokens.StringToken(value=name, position=position):
                if name not in variables:
                    raise errors.EvaluationError(f'Undefined variable "{name}"', position=position)
                return variables[name]
            case token:
                return token.value

    def _evaluate_binary(binary: ast.BinaryNode) -> int | float:
        left = _evaluate(binary.l_expr)
        right = _evaluate(binary.r_expr)

        match binary.operator.value:
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
                raise errors.EvaluationError(f'Unsupported operation "{binary.operator.value}"')

    def _evaluate_function(fn_call: ast.FunctionCallNode):
        fn = _FUNCTIONS.get(fn_call.fn_name.value)
        if not fn:
            raise errors.EvaluationError(f'Unknown function "{fn_call.fn_name}".')

        fn_arg = _evaluate(fn_call.arg)
        try:
            return fn(fn_arg)
        except Exception as e:
            fn_name = fn_call.fn_name.value
            raise errors.EvaluationError(f'Failed to evaluate "{fn_name}({fn_arg})" with error "{e}".')

    def _evaluate(node: ast.Node) -> int | float:
        match node:
            case ast.UnaryNode() as unary:
                return _evaluate_unary(unary)
            case ast.TerminalNode() as terminal:
                return _evaluate_terminal(terminal)
            case ast.BinaryNode() as binary:
                return _evaluate_binary(binary)
            case ast.FunctionCallNode() as fn_call:
                return _evaluate_function(fn_call)
            case _:
                raise errors.EvaluationError(f'Unexpected AST node {node}')

    return _evaluate(root)
