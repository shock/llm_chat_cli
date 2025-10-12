from prompt_toolkit.completion import Completer, Completion
from typing import Iterable


class DelegatingCompleter(Completer):
    def __init__(self, completer_a, completer_b, decision_function):
        self.completer_a = completer_a
        self.completer_b = completer_b
        self.decision_function = decision_function

    def get_completions(self, document, complete_event):
        if self.decision_function(document):
            yield from self.completer_a.get_completions(document, complete_event)
        else:
            yield from self.completer_b.get_completions(document, complete_event)