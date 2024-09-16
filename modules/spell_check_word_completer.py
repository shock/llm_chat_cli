from prompt_toolkit.completion import Completer, Completion
from difflib import get_close_matches
import re
from modules.word_list_manager import WordListManager

class SpellCheckWordCompleter(Completer):
    def __init__(self, word_list_manager: WordListManager):
        self.word_list_manager = word_list_manager

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)

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

        # For manual completion, include spell-check suggestions
        spell_suggestions = get_close_matches(word_before_cursor, word_list, n=3, cutoff=0.6)
        completion_suggestions = [word for word in word_list if word.lower().startswith(word_before_cursor.lower())]
        suggestions = list(set(completion_suggestions + spell_suggestions))

        for suggestion in suggestions:
            yield Completion(suggestion, start_position=-len(word_before_cursor))
