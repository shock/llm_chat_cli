from prompt_toolkit.completion import Completer


class DelegatingCompleter(Completer):
    """
    A delegating completer that routes completion requests between two completers.

    This completer uses a decision function to determine which of two underlying
    completers should handle the current completion request. This is particularly
    useful for context-aware completion where different completion strategies
    are needed for different parts of the input.

    In the LLM Chat CLI, this is used to switch between model name completion
    (when typing after `/mod `) and general word completion (for regular chat input).

    Parameters:
    -----------
    completer_a : Completer
        The first completer to delegate to when decision_function returns True
    completer_b : Completer
        The second completer to delegate to when decision_function returns False
    decision_function : callable
        A function that takes a Document and returns a boolean indicating
        which completer should handle the request
    """
    def __init__(self, completer_a, completer_b, decision_function):
        self.completer_a = completer_a
        self.completer_b = completer_b
        self.decision_function = decision_function

    def get_completions(self, document, complete_event):
        """
        Generate completions by delegating to the appropriate underlying completer.

        This method uses the decision function to determine which completer
        (completer_a or completer_b) should handle the current completion request,
        then delegates to that completer's get_completions method.

        Parameters:
        -----------
        document : prompt_toolkit.document.Document
            The current document containing the input text
        complete_event : prompt_toolkit.completion.CompleteEvent
            The completion event that triggered this method

        Yields:
        -------
        Completion
            Completion objects from the delegated completer
        """
        if self.decision_function(document):
            yield from self.completer_a.get_completions(document, complete_event)
        else:
            yield from self.completer_b.get_completions(document, complete_event)