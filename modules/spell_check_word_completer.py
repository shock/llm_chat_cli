from prompt_toolkit.completion import Completer, Completion
from difflib import get_close_matches
import re
from modules.word_list_manager import WordListManager

class SpellCheckWordCompleter(Completer):
    def __init__(self, word_list_manager: WordListManager):
        self.word_list_manager = word_list_manager

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True).lower()

        if len(word_before_cursor) < 2 and not complete_event.completion_requested:
            return

        # if word_before_cursor ends with a non-word character, return
        if re.search(r'[^\w\s]', word_before_cursor):
            return

        doc_words = WordListManager.parse_text(document.text)
        # get unique doc_words
        doc_words = list(set(doc_words))
        # remove word_before_cursor from doc_words if it exists
        if word_before_cursor in doc_words:
            doc_words.remove(word_before_cursor)

        word_list = self.word_list_manager.get_word_list()
        word_list = list(set(word_list + doc_words))
        word_list = [word.lower() for word in word_list]

        # For manual completion, include spell-check suggestions
        spell_possibilities = [word for word in word_list if word.lower().startswith(word_before_cursor.lower()[0:1])]
        spell_suggestions = get_close_matches(word_before_cursor, spell_possibilities, n=3, cutoff=0.7)
        completion_suggestions = [word for word in word_list if word.lower().startswith(word_before_cursor.lower())]
        # sort comletion suggestions by length
        completion_suggestions.sort(key=len)
        suggestions = completion_suggestions + spell_suggestions
        # remove duplicates in suggestions while preserving order
        seen = set()
        result = []
        word_in_suggestions = word_before_cursor in suggestions
        for word in suggestions:
            if word not in seen and word != word_before_cursor:
                seen.add(word)
                result.append(word)
        if word_in_suggestions:
            # insert word_before_cursor at the beginning of the list
            result.insert(0, word_before_cursor)
        suggestions = result
        for suggestion in suggestions:
            yield Completion(suggestion, start_position=-len(word_before_cursor))
