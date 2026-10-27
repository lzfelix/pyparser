from pyparser.lexer import tokenizer
from pyparser.parser import ast, parser
from pyparser.operations import evaluator, printer
from pyparser.operations.differentiator import differentiate


def _evaluation_demo() -> None:
    expression = '2 + 3*cos(5^0 - 1) + sin(21)^2 + cos(44/2 - (3-2))^2'
    expression_tree = parser.parse(tokenizer.tokenize(expression))

    print(f'Original expression: {expression}')
    print(f'Evaluated: {evaluator.evaluate(expression_tree)}')
    print(f'Expression reconstructed from tree: {printer.to_string(expression_tree)}')


def _gradient_descent_demo() -> None:
    expression = '(x - 3) ^ 2 + 2 * (y + 1) ^ 2'
    variables = ['x', 'y']
    learning_rate = 0.1
    steps = 50

    tree = parser.parse(tokenizer.tokenize(expression))
    gradient = [differentiate(tree, ast.VariableNode(name)) for name in variables]

    print(f'Minimizing f(x, y) = {expression}')
    for name, partial in zip(variables, gradient):
        print(f'  df/d{name} = {printer.to_string(partial)}')

    point = {'x': 0.0, 'y': 0.0}
    for step in range(steps + 1):
        if step % 10 == 0:
            print(f'  step {step:2}: x = {point["x"]:.4f}, y = {point["y"]:.4f}, f = {evaluator.evaluate(tree, point):.6f}')

        slopes = [evaluator.evaluate(partial, point) for partial in gradient]
        point = {name: point[name] - learning_rate * slope for name, slope in zip(variables, slopes)}


if __name__ == "__main__":
    _evaluation_demo()
    print()
    _gradient_descent_demo()
    print('Bye.')
