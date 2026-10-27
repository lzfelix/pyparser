from pyparser import errors
from pyparser.constants import CONSTANTS
from pyparser.functions import BUILTINS
from pyparser.operations.helpers import depends_on
from pyparser.parser import ast


def differentiate(root: ast.Node, var: ast.VariableNode | ast.IndexedVariableNode) -> ast.Node:
    """Builds the derivative of `root` with respect to `var`, as a new tree.

    Variables other than `var` are treated as constants, so this computes partial
    derivatives. The result is not simplified: `d/dx (3 * x)` gives `0 * x + 3 * 1`.
    """
    if var.name in CONSTANTS:
        raise errors.DifferentiationError(f'Cannot differentiate with respect to constant "{var.name}"')

    def _differentiate(node: ast.Node) -> ast.Node:
        if not depends_on(node, var):
            return ast.NumberNode(0)

        match node:
            # Only reached when the leaf is var itself
            case ast.VariableNode() | ast.IndexedVariableNode():
                return ast.NumberNode(1)

            case ast.UnaryNode(operator='+' | '-' as sign, expr=u):
                # (±u)' = -u'
                du = _differentiate(u)
                return ast.UnaryNode(sign, du)

            case ast.BinaryNode(left=u, operator='+' | '-' as operator, right=v):
                # (u ± v)' = u' ± v'
                du = _differentiate(u)
                dv = _differentiate(v)
                return ast.BinaryNode(du, operator, dv)

            case ast.BinaryNode(left=u, operator='*', right=v):
                # (u * v)' = u' * v + u * v'
                du = _differentiate(u)
                dv = _differentiate(v)
                return ast.BinaryNode(
                    ast.BinaryNode(du, '*', v),
                    '+',
                    ast.BinaryNode(u, '*', dv))

            case ast.BinaryNode(left=u, operator='/', right=v):
                # (u / v)' = (u' * v - u * v') / v ^ 2
                du = _differentiate(u)
                dv = _differentiate(v)

                product_left = ast.BinaryNode(du, '*', v)
                product_right = ast.BinaryNode(u, '*', dv)

                numerator = ast.BinaryNode(product_left, '-', product_right)
                denominator = ast.BinaryNode(v, '^', ast.NumberNode(2))
                return ast.BinaryNode(numerator, '/', denominator)

            case ast.BinaryNode(left=u, operator='^', right=v):
                # `node` is u ^ v itself; nodes are immutable, so it can be reused in the result
                u_varies = depends_on(u, var)
                v_varies = depends_on(v, var)

                if u_varies and v_varies:
                    # (u ^ v)' = u ^ v * (v' * log(u) + v * (u' / u))
                    log_term = ast.BinaryNode(_differentiate(v), '*', ast.FunctionCallNode('log', u))
                    ratio_term = ast.BinaryNode(v, '*', ast.BinaryNode(_differentiate(u), '/', u))
                    return ast.BinaryNode(node, '*', ast.BinaryNode(log_term, '+', ratio_term))

                if u_varies:
                    # u ^ 0 is the constant 1. The general rule below would build u ^ -1,
                    # which fails to evaluate at u = 0 even though the derivative is 0 there
                    if v == ast.NumberNode(0):
                        return ast.NumberNode(0)

                    # Constant exponent: (u ^ n)' = n * u ^ (n - 1) * u'
                    lowered_power = ast.BinaryNode(u, '^', ast.BinaryNode(v, '-', ast.NumberNode(1)))
                    return ast.BinaryNode(ast.BinaryNode(v, '*', lowered_power), '*', _differentiate(u))

                # Constant base: (a ^ v)' = a ^ v * log(a) * v'
                return ast.BinaryNode(ast.BinaryNode(node, '*', ast.FunctionCallNode('log', u)), '*', _differentiate(v))

            case ast.FunctionCallNode(name=name, arg=u):
                function = BUILTINS.get(name)
                if function is None:
                    raise errors.DifferentiationError(f'Unknown function "{name}".', position=node.position)

                # Chain rule: f(u)' = f'(u) * u'
                return ast.BinaryNode(function.derivative(u), '*', _differentiate(u))

            case ast.UnaryNode(operator=operator) | ast.BinaryNode(operator=operator):
                raise errors.DifferentiationError(f'Unsupported operation "{operator}"', position=node.position)

            case _:
                raise errors.DifferentiationError(f'Unexpected AST node {node}')

    return _differentiate(root)
