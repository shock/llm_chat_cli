import re
from prompt_toolkit.completion import Completer, Completion
from jaro import jaro_winkler_metric


class ModelCommandCompleter(Completer):
    """
    A completer that provides intelligent model name suggestions for the `/mod` command.

    This completer uses Jaro-Winkler similarity matching to provide relevant model name
    completions as users type after the `/mod` command. It supports multiple completion
    formats including provider-prefixed names, short names, and long names.

    Features:
    - Intelligent substring matching using Jaro-Winkler similarity
    - Case-insensitive matching for better user experience
    - Provider context display in completion metadata
    - Error handling to maintain clean UX when ProviderManager fails
    - Performance optimizations including early termination for exact matches

    Parameters:
    -----------
    provider_manager : ProviderManager
        The provider manager instance used to fetch available model names
    mod_command_pattern : str
        Regular expression pattern to match the `/mod` command and extract model substring
    """
    def __init__(self, provider_manager, mod_command_pattern):
        self.provider_manager = provider_manager
        self.mod_command_pattern = mod_command_pattern

    def get_completions(self, document, complete_event):
        """
        Generate model name completions for the current document context.

        This method extracts the model substring from the document text, fetches available
        model names from the ProviderManager, filters them based on similarity matching,
        and yields Completion objects for display.

        Parameters:
        -----------
        document : prompt_toolkit.document.Document
            The current document containing the input text
        complete_event : prompt_toolkit.completion.CompleteEvent
            The completion event that triggered this method

        Yields:
        -------
        Completion
            Completion objects with model names and provider context metadata
        """
        # Fetch model names from ProviderManager
        model_substring = self.get_model_substring(document)
        model_substring_len = len(model_substring)
        # remove all whitespace from model_substring
        model_substring = re.sub(r'\s', '', model_substring)
        if model_substring_len < 1 and not complete_event.completion_requested:
            return

        model_names = self.provider_manager.valid_scoped_models()

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
        """
        Filter and rank model name completions based on similarity matching.

        This method uses Jaro-Winkler substring matching to find the most relevant
        model name completions and returns the top 8 matches.

        Parameters:
        -----------
        model_names : list of str
            List of available model names to filter
        model_substring : str
            The user's input substring to match against model names

        Returns:
        --------
        list of tuples (str, float)
            Top 8 ranked completions with their similarity scores
        """
        ranked_completions = substring_jaro_winkler_match(model_substring, model_names)
        return ranked_completions[:8]

    def get_model_substring(self, document):
        """
        Extract the model substring from the document text using the mod command pattern.

        This method uses regular expression matching to extract the model name portion
        following the `/mod` command in the document text.

        Parameters:
        -----------
        document : prompt_toolkit.document.Document
            The current document containing the input text

        Returns:
        --------
        str
            The extracted model substring, or empty string if no match found
        """
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

    This function is used by the ModelCommandCompleter to provide intelligent model name suggestions
    for the `/mod` command in the LLM Chat CLI.

    **Case-Insensitive Matching:** Both input strings are converted to lowercase before comparison to ensure
    case-insensitive matching for better user experience.

    **Performance Optimizations:**
    - Early termination for exact matches
    - Skip empty input strings
    - Optimized inner loop with early exit for perfect scores

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

    """
    input_len = len(input_str)
    results = []

    if input_len == 0:
        return results  # Return empty list if input string is empty

    # Convert input string to lowercase for case-insensitive matching
    input_str_lower = input_str.lower()

    for long_str in longer_strings:
        max_score = 0.0
        # Convert longer string to lowercase for case-insensitive matching
        long_str_lower = long_str.lower()

        # Check for exact prefix match first (fast path)
        if long_str_lower.startswith(input_str_lower):
            max_score = 1.0  # Assign a high score for exact prefix matches
        # Check for exact substring match (fast path)
        elif input_str_lower in long_str_lower:
            max_score = 0.99  # Assign a lower score for substring matches
        else:
            # Slide over the longer string with a window of input_str length
            for i in range(len(long_str_lower) - input_len + 1):
                substring = long_str_lower[i:i+input_len]
                score = jaro_winkler_metric(input_str_lower, substring)
                if score > max_score:
                    max_score = score
                    # Early exit if we found a perfect match
                    if max_score == 1.0:
                        break

        results.append((long_str, max_score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results