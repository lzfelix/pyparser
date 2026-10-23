from dataclasses import dataclass, field


class Node:
    pass


# Positions point back to the source expression for error messages. They are
# excluded from equality so that trees compare by structure only, and are None
# for nodes that don't come from the source (e.g. built by a transformation).


@dataclass(frozen=True, slots=True)
class UnaryNode(Node):
    operator: str
    expr: Node
    position: int | None = field(default=None, compare=False)


@dataclass(frozen=True, slots=True)
class BinaryNode(Node):
    left: Node
    operator: str
    right: Node
    position: int | None = field(default=None, compare=False)


@dataclass(frozen=True, slots=True)
class NumberNode(Node):
    value: int | float
    position: int | None = field(default=None, compare=False)


@dataclass(frozen=True, slots=True)
class VariableNode(Node):
    name: str
    position: int | None = field(default=None, compare=False)


@dataclass(frozen=True, slots=True)
class FunctionCallNode(Node):
    name: str
    arg: Node
    position: int | None = field(default=None, compare=False)
