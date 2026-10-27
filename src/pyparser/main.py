from pyparser import Expression


def _evaluation_demo() -> None:
    source = '2 + 3*cos(5^0 - 1) + sin(21)^2 + cos(44/2 - (3-2))^2'
    expression = Expression(source, variables=[])

    print(f'Original expression: {source}')
    print(f'Evaluated: {expression.evaluate({})}')
    print(f'Expression reconstructed from tree: {expression}')


def _gradient_descent_demo() -> None:
    function = Expression('(x - 3) ^ 2 + 2 * (y + 1) ^ 2', variables=['x', 'y'])
    gradient = function.gradient()
    learning_rate = 0.1
    steps = 50

    print(f'Minimizing f(x, y) = {function}')
    for name, partial in zip(function.variables, gradient):
        print(f'  df/d{name} = {partial}')

    point = {'x': 0.0, 'y': 0.0}
    for step in range(steps + 1):
        if step % 10 == 0:
            print(f'  step {step:2}: x = {point["x"]:.4f}, y = {point["y"]:.4f}, f = {function.evaluate(point):.6f}')

        slopes = [partial.evaluate(point) for partial in gradient]
        point = {name: point[name] - learning_rate * slope for name, slope in zip(function.variables, slopes)}


if __name__ == "__main__":
    _evaluation_demo()
    print()
    _gradient_descent_demo()
    print('Bye.')
