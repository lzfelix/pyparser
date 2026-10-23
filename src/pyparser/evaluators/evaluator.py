from pyparser.parser import ast
from pyparser import errors


def _evaluate_unary(unary: ast.UnaryNode) -> int | float:
    match unary.operator.value:
        case '+':
            return evaluate(unary.expr)
        case '-':
            return -evaluate(unary.expr)


def _evaluate_terminal(terminal: ast.TerminalNode) -> int | float:
    # TODO: take care of variables
    return terminal.expr.value


def _evaluate_binary(binary: ast.BinaryNode) -> int | float:
    left = evaluate(binary.l_expr)
    right = evaluate(binary.r_expr)

    match binary.operator.value:
        case '+':
            return left + right
        case '-':
            return left - right
        case '*':
            return left * right
        case '/':
            return left / right  # Delegating division by zero to Python


def evaluate(root: ast.Node) -> int | float:
    match root:
        case ast.UnaryNode() as unary:
            return _evaluate_unary(unary)
        case ast.TerminalNode() as terminal:
            return _evaluate_terminal(terminal)
        case ast.BinaryNode() as binary:
            return _evaluate_binary(binary)
        case _:
            raise errors.EvaluationError(f'Unexpected AST node {root}')
