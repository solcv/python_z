from dataclasses import FrozenInstanceError

import pytest

from pyflow import Task, Workflow, WorkflowValidationError


def function(inputs, params):
    return inputs, params


def test_task_copies_mutable_inputs():
    dependencies = {'source'}
    params = {'nested': [1]}
    task = Task('target', function, dependencies, params, 'Opis')
    dependencies.add('other')
    params['nested'].append(2)
    assert task.dependencies == frozenset({'source'})
    assert task.params == {'nested': [1]}
    assert task.description == 'Opis'
    with pytest.raises(TypeError):
        task.params['new'] = 1
    with pytest.raises(FrozenInstanceError):
        task.name = 'changed'


@pytest.mark.parametrize('name', ['', '   '])
def test_empty_name(name):
    with pytest.raises(ValueError):
        Task(name, function)


def test_self_dependency():
    with pytest.raises(ValueError):
        Task('a', function, {'a'})


def test_invalid_function():
    with pytest.raises(ValueError):
        Task('a', None)


def test_invalid_dependency_name():
    with pytest.raises(ValueError):
        Task('a', function, {''})


def test_defaults_are_independent():
    a, b = Task('a', function), Task('b', function)
    assert a.dependencies == b.dependencies == frozenset()
    assert a.params == b.params == {}
    assert a.function({'x': 2}, {'y': 3}) == ({'x': 2}, {'y': 3})


def test_duplicate_rejected_without_replacement():
    workflow = Workflow()
    original = Task('a', function)
    workflow.add_task(original)
    with pytest.raises(WorkflowValidationError, match='a'):
        workflow.add_task(Task('a', function))
    assert workflow.tasks['a'] is original
