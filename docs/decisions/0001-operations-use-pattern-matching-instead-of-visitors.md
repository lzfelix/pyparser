# 0001. Operations use pattern matching instead of the visitor pattern

- **Status:** Accepted
- **Date:** 2026-10-23

## Context

Several operations walk the AST, each producing something different:

- `evaluator.evaluate(root, variables)` returns a number.
- `printer.to_string(root)` returns a string.
- A differentiator (in progress) and a simplifier (planned) will return new trees.

Every operation needs to dispatch on the node type (`NumberNode`, `VariableNode`, `IndexedVariableNode`, `UnaryNode`, `BinaryNode`, `FunctionCallNode`). The classic object-oriented way to add operations over a tree is the visitor pattern, so we considered it before adding more operations.

## Decision

Each operation is a plain function that dispatches with `match` over the node dataclasses:

```python
def evaluate(root: ast.Node, variables=None) -> int | float:
    def _evaluate(node: ast.Node) -> int | float:
        match node:
            case ast.NumberNode() as number:
                return number.value
            case ast.BinaryNode() as binary:
                ...
            case _:
                raise errors.EvaluationError(f'Unexpected AST node {node}')

    return _evaluate(root)
```

Context that stays fixed during a walk (variables, the variable to differentiate by) is captured by a nested function, not stored on an object.

AST nodes stay pure data: frozen dataclasses with no behaviour.

## Consequences

- **Nodes know nothing about operations.** Adding an operation means adding a module under `operations/`, without touching `ast.py`. Adding a node type means changing `ast.py` and adding a `case` to each operation that needs it.
- **Less code.** No `accept` methods on nodes and no visitor base class or per-operation classes.
- **Missing cases fail at runtime, not earlier.** If an operation lacks a `case` for a node type, it is only noticed when that node reaches the `case _: raise` fallback. Tests are the safety net for now.

## Alternatives considered

### Visitor pattern

Each node gets an `accept(visitor)` method, and each operation is a class with `visit_number`, `visit_binary`, and so on.

- **For:** an abstract visitor base class fails as soon as an operation forgetting a `visit_*` method is instantiated. A base visitor can also provide default traversal, so operations override only the nodes they care about.
- **Against:**
  - It adds behaviour to the AST dataclasses: `accept` exists only to serve operations, and every new node type must implement it.
  - The pattern mainly compensates for languages without pattern matching. Python's `match` on dataclasses dispatches directly.
  - Context would move from a nested function's closure to instance attributes (`Evaluator(variables).visit(node)`), a shape previously rejected as awkward.

Rejected.

### `functools.singledispatch`

One registered function per node type. It dispatches on type without changing the nodes, but spreads an operation over many decorated functions and makes sharing walk-wide context awkward. Not worth it over `match`.

## Future option

If missing cases become a problem, get early detection without changing the nodes:

1. Declare the node union: `type Node = NumberNode | VariableNode | IndexedVariableNode | UnaryNode | BinaryNode | FunctionCallNode`.
2. End each `match` with `case _: assert_never(node)`.
3. Run a type checker (pyright or mypy) in CI, which then reports any operation that doesn't handle every node type.
