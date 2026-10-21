from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping
from types import MappingProxyType


@dataclass(frozen=True)
class Task:
    name: str
    function: Callable[
        [Mapping[str, Any], Mapping[str, Any]], Any
    ]
    dependencies: frozenset[str] = field(
        default_factory=frozenset
    )
    params: Mapping[str, Any] = field(
        default_factory=dict
    )
    description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Nazwa zadania nie może być pusta")

        if not callable(self.function):
            raise ValueError("Funkcja zadania musi być wywoływalna")
        object.__setattr__(self, "dependencies", frozenset(self.dependencies))
        if any(not isinstance(name, str) or not name.strip() for name in self.dependencies):
            raise ValueError("Nazwy zależności muszą być niepustymi napisami")
        object.__setattr__(self, "params", MappingProxyType(deepcopy(dict(self.params))))

        if self.name in self.dependencies:
            raise ValueError("Zadanie nie może zależeć od siebie")

class WorkflowValidationError(ValueError):
    pass

class Workflow:
    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}

    def add_task(self, task: Task) -> None:
        if task.name in self.tasks:
            raise WorkflowValidationError(
                f"Zadanie '{task.name}' już istnieje"
            )

        self.tasks[task.name] = task
    def validate(self) -> None:
        """Raise WorkflowValidationError for missing dependencies or cycles."""
        from .graph import topological_order

        topological_order(self)
