import re
from prompt_toolkit.completion import Completer, Completion


class ModelCommandCompleter(Completer):
    """
    A completer that provides intelligent model name suggestions for the `/mod` command.

    This completer uses Jaro-Winkler similarity matching to provide relevant model name
    completions as users type after the `/mod` command. It supports multiple completion
    formats including provider-prefixed names, short names, and long names.

    Features:
    - Intelligent substring matching using Jaro-Winkler similarity
    - Case-insensitive matching for better user experience
    - short name display in completion metadata
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
            Completion objects with model names and short name metadata
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
            # Extract short name from the formatted model string
            short_name = self.extract_short_name(completion[0])
            full_name = completion[0].split(' ')[0]
            yield Completion(full_name, start_position=-model_substring_len, display_meta=short_name)

    def extract_short_name(self, model_string):
        """Extract short name from formatted model string for display_meta."""
        # Model string format: "provider/long_name (short_name)"
        match = re.search(r'\((.*?)\)', model_string)
        if match:
            return match.group(1)
        return model_string.split('/')[1]  # Fallback to long_name if no short name

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
        ranked_completions = fuzzy_subsequence_search(model_substring, model_names)
        return ranked_completions

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


def is_subsequence(query, target):
    """Check if query is a subsequence of target and return the indices of matched chars."""
    q_len, t_len = len(query), len(target)
    q_idx, t_idx = 0, 0
    matched_indices = []
    while q_idx < q_len and t_idx < t_len:
        if query[q_idx].lower() == target[t_idx].lower():
            matched_indices.append(t_idx)
            q_idx += 1
        t_idx += 1
    if q_idx == q_len:
        return matched_indices
    return None

def score_match(matched_indices, target_len):
    """Score based on spread and length."""
    if not matched_indices:
        return 0  # No matches, lowest possible score
    spread = matched_indices[-1] - matched_indices[0] + 1
    # Combine spread and length, you can tweak weights
    return spread + target_len

def fuzzy_subsequence_search(query, candidates):
    results = []
    for candidate in candidates:
        matched_indices = is_subsequence(query, candidate)
        if matched_indices is not None:
            score = score_match(matched_indices, len(candidate))
            results.append((score, candidate))
    results.sort(key=lambda x: x[0])
    return [[candidate, score] for score, candidate in results]
