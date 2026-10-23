from pyparser.parser import ast


def test_equality_ignores_positions():
    assert ast.VariableNode('x', position=0) == ast.VariableNode('x', position=4)
    assert ast.NumberNode(2, position=1) == ast.NumberNode(2)


def test_equality_compares_structure():
    x_minus_x = ast.BinaryNode(ast.VariableNode('x', position=0), '-', ast.VariableNode('x', position=4))

    assert x_minus_x.left == x_minus_x.right
    assert ast.BinaryNode(ast.NumberNode(1), '+', ast.NumberNode(2)) != ast.BinaryNode(ast.NumberNode(1), '-', ast.NumberNode(2))
