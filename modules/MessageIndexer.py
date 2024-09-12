class MessageIndexer:
    """Handles indexing of user and assistant messages."""

    def __init__(self, history):
        self.history = history
        self.user_indexes = []
        self.assistant_indexes = []
        self.user_message_index = 0
        self.assistant_message_index = -1
        self.update_indexes()

    def update_indexes(self):
        """Update the list of user and assistant message indexes."""
        self.update_user_indexes()
        self.update_assistant_indexes()

    def update_user_indexes(self):
        """Update the list of user message indexes."""
        self.user_indexes = [i for i, msg in enumerate(self.history) if msg['role'] == 'user']

    def update_assistant_indexes(self):
        """Update the list of assistant message indexes."""
        self.assistant_indexes = [i for i, msg in enumerate(self.history) if msg['role'] == 'assistant']

    def in_seek_user(self):
        """Check if the history is currently seeking a user message."""
        return self.user_message_index < len(self.user_indexes)

    def in_seek_assistant(self):
        """Check if the history is currently seeking an assistant message."""
        return self.assistant_message_index < len(self.assistant_indexes) - 1

    def seek_previous_user_message(self):
        """Seek to the previous user message."""
        if self.user_message_index > 0:
            self.user_message_index -= 1
        if self.in_seek_user():
            return self.history[self.user_indexes[self.user_message_index]]
        return None

    def seek_next_user_message(self):
        """Seek to the next user message."""
        if self.in_seek_user():
            self.user_message_index += 1
        if self.in_seek_user():
            return self.history[self.user_indexes[self.user_message_index]]
        return None

    def seek_previous_assistant_message(self):
        """Seek to the previous assistant message."""
        if self.assistant_message_index > 0:
            self.assistant_message_index -= 1
        if self.in_seek_assistant():
            return self.history[self.assistant_indexes[self.assistant_message_index]]
        return None

    def seek_next_assistant_message(self):
        """Seek to the next assistant message."""
        if self.in_seek_assistant():
            self.assistant_message_index += 1
            if self.in_seek_assistant():
                return self.history[self.assistant_indexes[self.assistant_message_index]]
        return None

    def get_last_assistant_message(self):
        """Get the current assistant message."""
        if self.in_seek_assistant():
            return self.history[self.assistant_indexes[self.assistant_message_index]]
        elif self.assistant_indexes:
            return self.history[self.assistant_indexes[-1]]
        return None
