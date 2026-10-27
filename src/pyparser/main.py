from pyparser.lexer import tokenizer
from pyparser.parser import parser
from pyparser.operations import evaluator, printer

if __name__ == "__main__":
    expression = '2 + 3*cos(5^0 - 1) + sin(21)^2 + cos(44/2 - (3-2))^2'
    expression_tree = parser.parse(tokenizer.tokenize(expression))

    print(f'Original expression: {expression}')
    print(f'Evaluated: {evaluator.evaluate(expression_tree)}')
    print(f'Expression reconstructed from tree: {printer.to_string(expression_tree)}')
    print('Bye.')
