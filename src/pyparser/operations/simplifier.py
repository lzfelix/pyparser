import operator

from pyparser.parser import ast


# Division is left out so that fractions such as `1 / 3` stay exact
_FOLDABLE = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '^': operator.pow,
}

# Larger exponents are left unfolded, since `9 ^ 9 ^ 9` would take ages to compute
_MAX_FOLDED_EXPONENT = 64


def simplify(root: ast.Node) -> ast.Node:
    """Builds an equivalent tree with arithmetic on numbers already computed, and terms that
    don't change the result removed: `x * 1 + 0 * y` simplifies to `x`.

    Function calls and constants are kept symbolic, so `log(2)` and `2 * pi` are left as they are.
    Negative numbers are written as a negated positive number, as the parser reads them, so a
    simplified tree prints into text that parses back into the same tree.
    """
    match root:
        case ast.NumberNode(value=value):
            return _number(value, root.position)
        case ast.VariableNode() | ast.IndexedVariableNode():
            return root
        case ast.UnaryNode(operator=sign, expr=expr):
            return _simplify_unary(sign, simplify(expr), root.position)
        case ast.BinaryNode(left=left, operator=op, right=right):
            return _simplify_binary(simplify(left), op, simplify(right), root.position)
        case ast.FunctionCallNode(name=name, arg=arg):
            return ast.FunctionCallNode(name, simplify(arg), position=root.position)
        case _:
            raise ValueError(f'Unexpected AST node {root}')


def _simplify_unary(sign: str, u: ast.Node, position: int | None) -> ast.Node:
    value = _value(u)
    if sign in ('+', '-') and value is not None:
        return _number(value if sign == '+' else -value, position)

    match sign, u:
        # +u = u
        case '+', _:
            return u
        # -(-u) = u
        case '-', ast.UnaryNode(operator='-', expr=w):
            return w
    return ast.UnaryNode(sign, u, position=position)


def _simplify_binary(u: ast.Node, op: str, v: ast.Node, position: int | None) -> ast.Node:
    folded = _fold(_value(u), op, _value(v))
    if folded is not None:
        return _number(folded, position)

    a, b = _value(u), _value(v)
    match op:
        case '+':
            # 0 + v = v,  u + 0 = u
            if a == 0:
                return v
            if b == 0:
                return u
        case '-':
            # u - 0 = u,  0 - v = -v
            if b == 0:
                return u
            if a == 0:
                return _simplify_unary('-', v, position)
        case '*':
            # 0 * v = u * 0 = 0,  1 * v = v,  u * 1 = u
            if a == 0 or b == 0:
                return _number(0, position)
            if a == 1:
                return v
            if b == 1:
                return u
        case '/':
            # u / 1 = u,  0 / v = 0 unless v is the number 0
            if b == 1:
                return u
            if a == 0 and b != 0:
                return _number(0, position)
        case '^':
            # u ^ 0 = 1 ^ v = 1,  u ^ 1 = u
            if b == 0 or a == 1:
                return _number(1, position)
            if b == 1:
                return u
    return ast.BinaryNode(u, op, v, position=position)


def _fold(a: int | float | None, op: str, b: int | float | None) -> int | float | None:
    if a is None or b is None or op not in _FOLDABLE:
        return None
    if op == '^' and abs(b) > _MAX_FOLDED_EXPONENT:
        return None

    # Operations that fail, such as `0 ^ -1`, are left for the evaluator to report
    try:
        result = _FOLDABLE[op](a, b)
    except ArithmeticError:
        return None
    # A negative base with a fractional exponent gives a complex number
    return None if isinstance(result, complex) else result


def _value(node: ast.Node) -> int | float | None:
    match node:
        case ast.NumberNode(value=value):
            return value
        case ast.UnaryNode(operator='-', expr=ast.NumberNode(value=value)):
            return -value
        case _:
            return None


def _number(value: int | float, position: int | None = None) -> ast.Node:
    if value < 0:
        return ast.UnaryNode('-', ast.NumberNode(-value), position=position)
    # abs turns -0.0 into 0.0, which would otherwise print with a sign
    return ast.NumberNode(abs(value), position=position)
