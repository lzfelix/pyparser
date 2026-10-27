import math
from collections.abc import Mapping
from types import MappingProxyType


CONSTANTS: Mapping[str, float] = MappingProxyType({
    'e': math.e,
    'pi': math.pi,
})
