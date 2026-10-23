from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Token[T]:
    value: T
    position: int

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class FloatToken(Token[float]):
    pass


@dataclass(frozen=True, slots=True)
class IntToken(Token[int]):
    pass


@dataclass(frozen=True, slots=True)
class StringToken(Token[str]):
    pass


@dataclass(frozen=True, slots=True)
class OperatorToken(Token[str]):
    pass


@dataclass(frozen=True, slots=True)
class OpenParensToken(Token[str]):
    pass


@dataclass(frozen=True, slots=True)
class CloseParensToken(Token[str]):
    pass
