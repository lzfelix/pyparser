from collections.abc import Iterable, Mapping
from typing import Self

from pyparser.errors import ExpressionError, PyParserError
from pyparser.lexer import tokenizer
from pyparser.operations import evaluator, printer
from pyparser.operations.differentiator import differentiate
from pyparser.operations.helpers import variable_uses
from pyparser.parser import ast, parser


class Expression:
    """An arithmetic expression over a fixed set of declared variables.

    The source is tokenized and parsed once, on construction. Every variable the expression
    uses must be declared; declaring `x` covers both `x` and indexed uses such as `x[0]`.
    Expressions are immutable: differentiating returns a new `Expression` with the same
    declared variables, which can be evaluated or differentiated again.
    """

    __slots__ = ('_tree', '_variables')

    _tree: ast.Node
    _variables: tuple[str, ...]

    def __init__(self, source: str, variables: Iterable[str]) -> None:
        declared = _declare(variables)
        tree = parser.parse(tokenizer.tokenize(source))
        _check_declared(tree, declared)
        self._set(tree, declared)

    @classmethod
    def _from_tree(cls, tree: ast.Node, variables: tuple[str, ...]) -> Self:
        expression = object.__new__(cls)
        expression._set(tree, variables)
        return expression

    def _set(self, tree: ast.Node, variables: tuple[str, ...]) -> None:
        object.__setattr__(self, '_tree', tree)
        object.__setattr__(self, '_variables', variables)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(f'{type(self).__name__} is immutable')

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f'{type(self).__name__} is immutable')

    @property
    def variables(self) -> tuple[str, ...]:
        return self._variables

    @property
    def tree(self) -> ast.Node:
        return self._tree

    def evaluate(self, values: Mapping[str, evaluator.Value]) -> int | float:
        """Evaluates the expression with a value for every declared variable.

        A variable used with an index (`x[0]`) is bound to a sequence of numbers.
        """
        missing = [name for name in self._variables if name not in values]
        if missing:
            raise ExpressionError(f'Missing values for {_quoted(missing)}')

        unknown = [name for name in values if name not in self._variables]
        if unknown:
            raise ExpressionError(f'Values given for undeclared {_quoted(unknown)}')

        return evaluator.evaluate(self._tree, values)

    def differentiate(self, var: str, order: int = 1) -> Expression:
        """Builds the `order`-th partial derivative with respect to `var`.

        `var` is a declared variable, either plain (`'x'`) or indexed (`'x[1]'`). Order 0
        returns this same expression. The result is not simplified.
        """
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            raise ExpressionError(f'Derivative order must be a non-negative integer, got {order!r}')

        target = self._declared_variable(var)
        if order == 0:
            return self

        tree = self._tree
        for _ in range(order):
            tree = differentiate(tree, target)
        return Expression._from_tree(tree, self._variables)

    def gradient(self, variables: Iterable[str] | None = None) -> tuple[Expression, ...]:
        """Builds the first partial derivative with respect to each of `variables`.

        Defaults to the declared variables, in declaration order. Indexed variables
        (`'x[0]'`) must be listed explicitly.
        """
        if isinstance(variables, str):
            raise ExpressionError(f'Variables must be a collection of names, not the string {variables!r}')

        names = self._variables if variables is None else variables
        return tuple(self.differentiate(name) for name in names)

    def _declared_variable(self, var: str) -> ast.VariableNode | ast.IndexedVariableNode:
        node = _parse_variable(var)
        if node.name not in self._variables:
            raise ExpressionError(f'Cannot differentiate with respect to undeclared variable "{var}"')
        return node

    def __str__(self) -> str:
        return printer.to_string(self._tree)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({str(self)!r}, variables={self._variables!r})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Expression):
            return NotImplemented
        return (self._tree, self._variables) == (other._tree, other._variables)

    def __hash__(self) -> int:
        return hash((self._tree, self._variables))


def _declare(variables: Iterable[str]) -> tuple[str, ...]:
    if isinstance(variables, str):
        raise ExpressionError(f'Variables must be a collection of names, not the string {variables!r}')

    declared = tuple(variables)
    for name in declared:
        if not isinstance(_parse_variable(name), ast.VariableNode):
            raise ExpressionError(f'Declared variable "{name}" must be a plain name, without an index')

    duplicates = sorted({name for name in declared if declared.count(name) > 1})
    if duplicates:
        raise ExpressionError(f'Duplicate declaration of {_quoted(duplicates)}')

    return declared


def _check_declared(tree: ast.Node, declared: tuple[str, ...]) -> None:
    for use in variable_uses(tree):
        if use.name not in declared:
            raise ExpressionError(f'Undeclared variable "{use.name}"', position=use.position)


def _parse_variable(text: str) -> ast.VariableNode | ast.IndexedVariableNode:
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
