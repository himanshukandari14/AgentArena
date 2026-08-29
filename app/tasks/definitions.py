from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class TaskDefinition:
    id: str
    description: str
    difficulty: str
    verifier: Callable