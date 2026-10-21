from itertools import permutations

import pytest

from pyflow import Task, Workflow, WorkflowValidationError, execution_layers, topological_order


def make_workflow(definition):
    workflow = Workflow()
    for name, dependencies in definition:
        workflow.add_task(Task(name, lambda inputs, params: None, dependencies))
    return workflow


@pytest.mark.parametrize(('definition', 'order', 'layers'), [
    ([], [], []),
    ([('a', set())], ['a'], [['a']]),
    ([('c', {'b'}), ('b', {'a'}), ('a', set())], ['a', 'b', 'c'], [['a'], ['b'], ['c']]),
    ([('z', set()), ('a', set())], ['a', 'z'], [['a', 'z']]),
    ([('report', {'clean_a', 'clean_b'}), ('clean_b', {'extract'}),
      ('extract', set()), ('clean_a', {'extract'})],
     ['extract', 'clean_a', 'clean_b', 'report'],
     [['extract'], ['clean_a', 'clean_b'], ['report']]),
])
def test_plans(definition, order, layers):
    workflow = make_workflow(definition)
    assert workflow.validate() is None
    assert topological_order(workflow) == order
    assert execution_layers(workflow) == layers


@pytest.mark.parametrize('planner', [Workflow.validate, topological_order, execution_layers])
@pytest.mark.parametrize(('definition', 'message'), [
    ([('a', {'missing'})], 'missing'),
    ([('a', {'b'}), ('b', {'a'})], 'Cykl'),
    ([('a', {'b'}), ('b', {'c'}), ('c', {'a'}), ('free', set())], 'Cykl'),
])
def test_invalid_graphs(planner, definition, message):
    with pytest.raises(WorkflowValidationError, match=message):
        planner(make_workflow(definition))


def test_determinism_and_global_alphabetical_choice():
    definition = [('a', {'b'}), ('b', set()), ('z', set()), ('c', {'a'})]
    for permutation in permutations(definition):
        workflow = make_workflow(permutation)
        assert topological_order(workflow) == ['b', 'a', 'c', 'z']
        assert execution_layers(workflow) == [['b', 'z'], ['a'], ['c']]


def test_layers_and_order_respect_all_dependencies_and_do_not_mutate_workflow():
    definition = [('a', set()), ('b', set()), ('c', {'a'}),
                  ('d', {'b', 'c'}), ('e', {'a', 'd'})]
    workflow = make_workflow(definition)
    before = dict(workflow.tasks)
    order = topological_order(workflow)
    assert len(order) == len(set(order)) == len(definition)
    positions = {name: i for i, name in enumerate(order)}
    completed = set()
    for layer in execution_layers(workflow):
        for name in layer:
            assert workflow.tasks[name].dependencies <= completed
            assert all(positions[dep] < positions[name] for dep in workflow.tasks[name].dependencies)
        completed.update(layer)
    assert completed == set(workflow.tasks)
    assert workflow.tasks == before
