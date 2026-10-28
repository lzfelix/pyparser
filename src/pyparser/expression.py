from collections.abc import Iterable, Mapping
from typing import Self

from pyparser.constants import CONSTANTS
from pyparser.errors import ExpressionError, PyParserError
from pyparser.lexer import tokenizer
from pyparser.operations import evaluator, printer
from pyparser.operations.differentiator import differentiate
from pyparser.operations.helpers import variable_uses
from pyparser.parser import ast, parser


type Variable = ast.VariableNode | ast.IndexedVariableNode


class Expression:
    """An arithmetic expression, parsed once from its source.

    Its variables are the ones its source uses, plain (`x`) or indexed (`x[0]`), in order of
    first appearance; built-in constants are not variables. Expressions are immutable:
    differentiating returns a new `Expression` that keeps the variables of the original, so
    every derivative can be evaluated at the same point and differentiated again.
    """

    __slots__ = ('_tree', '_uses')

    _tree: ast.Node
    _uses: tuple[Variable, ...]

    def __init__(self, source: str) -> None:
        tree = parser.parse(tokenizer.tokenize(source))
        self._set(tree, _variables_of(tree))

    @classmethod
    def _from_tree(cls, tree: ast.Node, uses: tuple[Variable, ...]) -> Self:
        expression = object.__new__(cls)
        expression._set(tree, uses)
        return expression

    def _set(self, tree: ast.Node, uses: tuple[Variable, ...]) -> None:
        object.__setattr__(self, '_tree', tree)
        object.__setattr__(self, '_uses', uses)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(f'{type(self).__name__} is immutable')

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f'{type(self).__name__} is immutable')

    @property
    def variables(self) -> tuple[str, ...]:
        """Names of the variables, in order of first appearance; `x[0]` and `x[1]` both count as `x`."""
        return tuple(dict.fromkeys(use.name for use in self._uses))

    @property
    def tree(self) -> ast.Node:
        return self._tree

    def evaluate(self, values: Mapping[str, evaluator.Value]) -> int | float:
        """Evaluates the expression with a value for every variable, and nothing else.

        A variable used with an index (`x[0]`) is bound to a sequence of numbers.
        """
        missing = [name for name in self.variables if name not in values]
        if missing:
            raise ExpressionError(f'Missing values for {_quoted(missing)}')

        unknown = [name for name in values if name not in self.variables]
        if unknown:
            raise ExpressionError(f'Values given for unknown {_quoted(unknown)}')

        return evaluator.evaluate(self._tree, values)

    def differentiate(self, var: str, order: int = 1) -> Expression:
        """Builds the `order`-th partial derivative with respect to `var`.

        `var` must be one of the expression's variables, plain (`'x'`) or indexed (`'x[1]'`).
        Order 0 returns this same expression. The result is not simplified.
        """
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            raise ExpressionError(f'Derivative order must be a non-negative integer, got {order!r}')

        target = self._variable(var)
        if order == 0:
            return self

        tree = self._tree
        for _ in range(order):
            tree = differentiate(tree, target)
        return Expression._from_tree(tree, self._uses)

    def gradient(self, variables: Iterable[str] | None = None) -> tuple[Expression, ...]:
        """Builds the first partial derivative with respect to each of `variables`.

        Defaults to every variable of the expression, indexed ones included, in order of
        first appearance.
        """
        if isinstance(variables, str):
            raise ExpressionError(f'Variables must be a collection of names, not the string {variables!r}')

        if variables is None:
            return tuple(Expression._from_tree(differentiate(self._tree, use), self._uses) for use in self._uses)
        return tuple(self.differentiate(name) for name in variables)

    def _variable(self, var: str) -> Variable:
        node = _parse_variable(var)
        if node.name in CONSTANTS:
            raise ExpressionError(f'Cannot differentiate with respect to constant "{node.name}"')
        if node not in self._uses:
            raise ExpressionError(f'Cannot differentiate with respect to "{var.strip()}", which is not a variable of the expression')
        return node

    def __str__(self) -> str:
        return printer.to_string(self._tree)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({str(self)!r})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Expression):
            return NotImplemented
        return (self._tree, self._uses) == (other._tree, other._uses)

    def __hash__(self) -> int:
        return hash((self._tree, self._uses))


def _variables_of(tree: ast.Node) -> tuple[Variable, ...]:
    uses = []
    for use in variable_uses(tree):
        if use.name in CONSTANTS:
            if isinstance(use, ast.IndexedVariableNode):
                raise ExpressionError(f'Constant "{use.name}" cannot be indexed', position=use.position)
            continue
        uses.append(use)
    return tuple(dict.fromkeys(uses))


def _parse_variable(text: str) -> Variable:
    if not isinstance(text, str):
        raise ExpressionError(f'Variable must be a string, got {text!r}')

    # Positions in the parsing errors refer to `text`, not to the expression, so they are dropped
    try:
        node = parser.parse(tokenizer.tokenize(text))
    except PyParserError as error:
        raise ExpressionError(f'Invalid variable "{text}": {error.message}') from error

    if not isinstance(node, ast.VariableNode | ast.IndexedVariableNode):
        raise ExpressionError(f'Invalid variable "{text}": expected a name such as "x" or "x[0]"')
    return node


def _quoted(names: Iterable[str]) -> str:
    names = list(names)
    noun = 'variable' if len(names) == 1 else 'variables'
    return f'{noun} ' + ', '.join(f'"{name}"' for name in names)
