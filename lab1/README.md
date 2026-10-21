# PyFlow — Laboratorium 1

Model zadań i deterministyczny plan wykonania skierowanego grafu acyklicznego
(DAG). Python 3.11+. Pakiet używa układu `src/`. Laboratorium 1 planuje zadania;
wykonywanie funkcji zadań będzie przedmiotem kolejnych laboratoriów.

## Instalacja i testy

W terminalu, w katalogu projektu:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
```

W VS Code wybierz interpreter `.venv/bin/python`. Polecenia powyżej wpisuj
w terminalu, a kod Pythona poniżej w pliku `.py` lub konsoli Pythona.

## Przykład

```python
from pyflow import Task, Workflow, topological_order, execution_layers


def extract(inputs, params):
    return params['data']


def clean(inputs, params):
    return [value for value in inputs['extract'] if value is not None]


def report(inputs, params):
    return {'a': inputs['clean_a'], 'b': inputs['clean_b']}


workflow = Workflow()
workflow.add_task(Task('extract', extract, params={'data': [1, None, 2]}))
workflow.add_task(Task('clean_a', clean, {'extract'}))
workflow.add_task(Task('clean_b', clean, {'extract'}))
workflow.add_task(Task('report', report, {'clean_a', 'clean_b'}))
workflow.validate()

assert topological_order(workflow) == ['extract', 'clean_a', 'clean_b', 'report']
assert execution_layers(workflow) == [
    ['extract'], ['clean_a', 'clean_b'], ['report']
]
```

`function(inputs, params)` przyjmuje mapowanie wyników bezpośrednich zależności
oraz mapowanie parametrów zadania. `Task` jest zamrożoną dataclass;
zależności są kopiowane do `frozenset`, parametry kopiowane głęboko i opakowane
w mapowanie tylko do odczytu. Zagnieżdżone wartości parametrów pozostają
mutowalne, ale są odseparowane od oryginalnego wejścia.

Pusta lub biała nazwa, niewywoływalna funkcja, niepoprawna nazwa zależności
oraz zależność od siebie powodują `ValueError`. `add_task` odrzuca duplikaty
przez `WorkflowValidationError` (podklasę `ValueError`). `validate` i oba
planery zgłaszają ten wyjątek dla brakujących zależności i cykli.
Zależności można zarejestrować po zadaniu, przed walidacją. Pusty workflow
jest poprawny i daje puste plany. Planery nie zmieniają definicji workflowu.

## Algorytm i złożoność

Algorytm Kahna zlicza niespełnione zależności i usuwa kolejne gotowe węzły.
Sortowanie topologiczne wybiera alfabetycznie najmniejszą aktualnie gotową
nazwę przez kopiec. Warstwy przetwarzają całą bieżącą grupę przed kolejną;
każda grupa jest posortowana alfabetycznie. Zablokowane węzły po zakończeniu
przetwarzania oznaczają cykl; diagnostyka wymienia także węzły zależne od cyklu.

Dla V zadań i E zależności oba planery mają czas O(E + V log V)
i pamięć O(V + E), przy standardowym założeniu stałego kosztu operacji na nazwach.
`validate()` korzysta z tego samego planera topologicznego.

Testy obejmują pusty graf, pojedyncze zadanie, łańcuch, niezależne zadania,
rozgałęzienia i połączenia, duplikaty, brakujące zależności, zależność od siebie,
cykle, izolację danych, deterministyczność i poprawność warstw.
