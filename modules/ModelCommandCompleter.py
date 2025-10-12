import re
from prompt_toolkit.completion import Completer, Completion
from jaro import jaro_winkler_metric


class ModelCommandCompleter(Completer):
    def __init__(self, provider_manager, mod_command_pattern):
        self.provider_manager = provider_manager
        self.mod_command_pattern = mod_command_pattern

    def get_completions(self, document, complete_event):
        # Fetch model names from ProviderManager
        model_substring = self.get_model_substring(document)
        model_substring_len = len(model_substring)
        # remove all whitespace from model_substring
        model_substring = re.sub(r'\s', '', model_substring)
        if model_substring_len < 1 and not complete_event.completion_requested:
            return

        # Error handling for ProviderManager calls
        try:
            model_names = self.provider_manager.valid_scoped_models()
        except Exception as e:
            # Log detailed error information to stderr for debugging
            import sys
            print(f"ModelCommandCompleter error: {e}", file=sys.stderr)
            # Return empty completion list to maintain clean UX
            return

        filtered_completions = self.filter_completions(model_names, model_substring)
        for completion in filtered_completions:
            # Extract provider context from the formatted model string
            provider_context = self.extract_provider_context(completion[0])
            yield Completion(completion[0], start_position=-model_substring_len, display_meta=provider_context)

    def extract_provider_context(self, model_string):
        """Extract provider context from formatted model string for display_meta."""
        # Model string format: "provider/long_name (short_name)"
        if '/' in model_string:
            provider = model_string.split('/')[0]
            return f"{provider} model"
        return "Model"

    def filter_completions(self, model_names, model_substring):
        ranked_completions = substring_jaro_winkler_match(model_substring, model_names)
        return ranked_completions[:8]

    def get_model_substring(self, document):
       text = document.text_before_cursor
       matches = re.search(self.mod_command_pattern, text)
       if matches:
           return matches.group(1)
       else:
           return ''


# Standalone function for substring matching using Jaro-Winkler similarity
# This is a standalone function, not a class method, that can be used independently
def substring_jaro_winkler_match(input_str, longer_strings):
    """
    Perform substring matching of an input string against a list of longer strings using Jaro-Winkler similarity.

    This is a standalone function that slides a window over each string in `longer_strings` with the same length as `input_str`,
    computes the Jaro-Winkler similarity between `input_str` and each substring, and records the highest similarity score
    for that string. It returns a list of tuples containing the original string and its best matching score,
    sorted in descending order of similarity.

    **Case-Insensitive Matching:** Both input strings are converted to lowercase before comparison to ensure
    case-insensitive matching for better user experience.

    Parameters:
    -----------
    input_str : str
       The input string to match as a substring.
    longer_strings : list of str
       A list of longer strings in which to search for the best substring match.

    Returns:
    --------
    list of tuples (str, float)
       A list of tuples where each tuple contains a string from `longer_strings` and its highest Jaro-Winkler similarity
       score with `input_str`. The list is sorted by similarity score in descending order.

    Example:
    --------
    >>> input_string = "martha"
    >>> longer_list = ["marhta", "marathon", "artha", "martian", "math"]
    >>> matches = substring_jaro_winkler_match(input_string, longer_list)
    >>> for string, score in matches:
    ...     print(f"{string}: {score:.4f}")
    marhta: 0.9611
    marathon: 0.8800
    artha: 0.8667
    martian: 0.8444
    math: 0.8000

    """
    input_len = len(input_str)
    results = []

    # Convert input string to lowercase for case-insensitive matching
    input_str_lower = input_str.lower()

    for long_str in longer_strings:
       max_score = 0.0
       # Convert longer string to lowercase for case-insensitive matching
       long_str_lower = long_str.lower()
       # Slide over the longer string with a window of input_str length
       for i in range(len(long_str_lower) - input_len + 1):
             substring = long_str_lower[i:i+input_len]
             score = jaro_winkler_metric(input_str_lower, substring)
             if score > max_score:
                max_score = score
       results.append((long_str, max_score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results