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
