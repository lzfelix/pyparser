from pyparser.parser import ast


def depends_on(root: ast.Node, var: ast.VariableNode | ast.IndexedVariableNode) -> bool:
    """Tells whether `var` appears anywhere in the tree rooted at `root`.

    Variables are compared by structure, so `x`, `x[0]` and `x[1]` are all different.
    Function names are not variables: `sin(y)` doesn't depend on a variable named `sin`.
    """
    match root:
        case ast.NumberNode():
            return False
        case ast.VariableNode() | ast.IndexedVariableNode():
            return root == var
        case ast.UnaryNode(expr=expr):
            return depends_on(expr, var)
        case ast.BinaryNode(left=left, right=right):
            return depends_on(left, var) or depends_on(right, var)
        case ast.FunctionCallNode(arg=arg):
            return depends_on(arg, var)
        case _:
            raise ValueError(f'Unexpected AST node {root}')


def variable_uses(root: ast.Node) -> list[ast.VariableNode | ast.IndexedVariableNode]:
    """Lists every variable in the tree rooted at `root`, in the order they appear in the source.

    Repeated uses are all listed, so each keeps its own position. Function names are not variables.
    """
    match root:
        case ast.NumberNode():
            return []
        case ast.VariableNode() | ast.IndexedVariableNode():
            return [root]
        case ast.UnaryNode(expr=expr):
            return variable_uses(expr)
        case ast.BinaryNode(left=left, right=right):
            return variable_uses(left) + variable_uses(right)
        case ast.FunctionCallNode(arg=arg):
            return variable_uses(arg)
        case _:
            raise ValueError(f'Unexpected AST node {root}')
