"""Deterministic DAG planning using Kahn's algorithm."""

from heapq import heapify, heappop, heappush

from .models import Workflow, WorkflowValidationError


def _graph(workflow: Workflow) -> tuple[dict[str, int], dict[str, list[str]]]:
    indegrees = {name: len(task.dependencies) for name, task in workflow.tasks.items()}
    children: dict[str, list[str]] = {name: [] for name in workflow.tasks}
    for name, task in workflow.tasks.items():
        missing = task.dependencies - workflow.tasks.keys()
        if missing:
            raise WorkflowValidationError(
                f"Zadanie '{name}': niezarejestrowane zależności: {', '.join(sorted(missing))}"
            )
        for dependency in task.dependencies:
            children[dependency].append(name)
    return indegrees, children


def _check_cycle(indegrees: dict[str, int]) -> None:
    remaining = sorted(name for name, degree in indegrees.items() if degree)
    if remaining:
        raise WorkflowValidationError(
            f"Cykl w grafie; zadania zablokowane przez cykl: {', '.join(remaining)}"
        )


def topological_order(workflow: Workflow) -> list[str]:
    """Return names in dependency order, choosing the smallest ready name."""
    indegrees, children = _graph(workflow)
    ready = [name for name, degree in indegrees.items() if degree == 0]
    heapify(ready)
    order: list[str] = []
    while ready:
        name = heappop(ready)
        order.append(name)
        for child in children[name]:
            indegrees[child] -= 1
            if indegrees[child] == 0:
                heappush(ready, child)
    _check_cycle(indegrees)
    return order


def execution_layers(workflow: Workflow) -> list[list[str]]:
    """Return alphabetically sorted batches ready after all previous batches."""
    indegrees, children = _graph(workflow)
    ready = sorted(name for name, degree in indegrees.items() if degree == 0)
    layers: list[list[str]] = []
    while ready:
        layers.append(ready)
        next_ready: list[str] = []
        for name in ready:
            for child in children[name]:
                indegrees[child] -= 1
                if indegrees[child] == 0:
                    next_ready.append(child)
        ready = sorted(next_ready)
    _check_cycle(indegrees)
    return layers
