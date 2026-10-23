from pyparser.parser import ast


# How tightly each kind of node holds together when printed without parens,
# following the grammar levels from weakest to strongest
_EXPR, _TERM, _UNARY, _POWER, _PRIMARY = range(1, 6)

_BINARY_PRECEDENCE = {
    '+': _EXPR,
    '-': _EXPR,
    '*': _TERM,
    '/': _TERM,
    '^': _POWER,
}

# Minimum precedence each operand slot accepts without parens, read off the grammar:
#   expr  := term (('+' | '-') term)*     left: expr      right: term
#   term  := unary (('*' | '/') unary)*   left: term      right: unary
#   power := primary ('^' unary)?         left: primary   right: unary
# Left-associative operators are stricter on the right, and `^` (right-associative)
# on the left, since ties are always won by the side the grammar groups towards
_BINARY_SLOTS = {
    '+': (_EXPR, _TERM),
    '-': (_EXPR, _TERM),
    '*': (_TERM, _UNARY),
    '/': (_TERM, _UNARY),
    '^': (_PRIMARY, _UNARY),
}

#   unary := ('+' | '-') unary | power
_UNARY_SLOT = _UNARY


def to_string(root: ast.Node) -> str:
    """Prints an AST using only the parens needed to parse it back into the same tree.

    Floats are printed with `str`, so values Python formats in scientific notation
    (e.g. `1e-07`) produce text the tokenizer can't read back.
    """

    def _precedence(node: ast.Node) -> int:
        match node:
            case ast.BinaryNode(operator=operator) if operator in _BINARY_PRECEDENCE:
                return _BINARY_PRECEDENCE[operator]
            case ast.UnaryNode():
                return _UNARY
            # Only transformations create negative numbers, which print with a leading sign
            case ast.NumberNode(value=value) if value < 0:
                return _UNARY
            case _:
                return _PRIMARY

    def _print_slot(node: ast.Node, minimum: int) -> str:
        text = _print(node)
        return f'({text})' if _precedence(node) < minimum else text

    def _print(node: ast.Node) -> str:
        match node:
            case ast.NumberNode(value=value):
                return str(value)
            case ast.VariableNode(name=name):
                return name
            case ast.IndexedVariableNode(name=name, index=index):
                return f'{name}[{index}]'
            case ast.FunctionCallNode(name=name, arg=arg):
                return f'{name}({_print(arg)})'
            case ast.UnaryNode(operator=operator, expr=expr):
                return f'{operator}{_print_slot(expr, _UNARY_SLOT)}'
            case ast.BinaryNode(left=left, operator=operator, right=right):
                if operator not in _BINARY_SLOTS:
                    raise ValueError(f'Unsupported operation "{operator}"')
                left_minimum, right_minimum = _BINARY_SLOTS[operator]
                return f'{_print_slot(left, left_minimum)} {operator} {_print_slot(right, right_minimum)}'
            case _:
                raise ValueError(f'Unexpected AST node {node}')

    return _print(root)
