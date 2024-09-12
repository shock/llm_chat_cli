import json
from modules.MessageSaverLoader import MessageSaverLoader

class MessageHistory:
    """Class to manage the chat message history."""

    def __init__(self, system_prompt=None):
        """Initialize the message history with an optional system prompt."""
        self.user_indexes = []
        if not system_prompt:
            raise ValueError("System prompt is required")
        self.history = []
        self.add_message("system", system_prompt)

    def system_prompt(self, system_prompt=None):
        """Set or get the system prompt."""
        if system_prompt:
            self.history[0]['content'] = system_prompt
        return self.history[0]['content']

    def update_indexes(self):
        """Update the list of user and assistant message indexes."""
        self.update_user_indexes()
        self.update_assistant_indexes()

    def update_user_indexes(self):
        """Update the list of user message indexes."""
        self.user_indexes = []
        self.user_message_index = 0
        for i, msg in enumerate(self.history):
            if msg['role'] == 'user':
                self.user_message_index += 1
                self.user_indexes.append(i)

    def update_assistant_indexes(self):
        """Update the list of assistant message indexes."""
        self.assistant_indexes = []
        self.assistant_message_index = -1
        for i, msg in enumerate(self.history):
            if msg['role'] == 'assistant':
                self.assistant_message_index += 1
                self.assistant_indexes.append(i)

    def add_message(self, role, content):
        """Add a message to the history."""
        self.history.append({"role": role, "content": content})
        self.update_indexes()

    def get_history(self):
        """Return the current message history."""
        return self.history

    def clear_history(self):
        """Clear the message history."""
        # keep the system prompt
        self.history = [self.history[0]]
        self.update_indexes()

    def in_seek_user(self):
        """Check if the history is currently seeking."""
        return (self.user_message_index < len(self.user_indexes))

    def in_seek_assistant(self):
        """Check if the history is currently seeking."""
        return (self.assistant_message_index < len(self.assistant_indexes)-1)

    def session_active(self):
        """Check if the session is active."""
        return len(self.user_indexes) > 0

    def seek_previous_user_message(self):
        """Seek to the previous user message."""
        if self.user_message_index > 0:
            self.user_message_index -= 1
        if self.in_seek_user():
            return self.history[self.user_indexes[self.user_message_index]]
        else:
            return None

    def seek_next_user_message(self):
        """Seek to the next user message."""
        if self.in_seek_user():
            self.user_message_index += 1
        if self.in_seek_user():
            return self.history[self.user_indexes[self.user_message_index]]
        else:
            return None

    def seek_previous_assistant_message(self):
        """Seek to the previous assistant message."""
        if self.assistant_message_index > 0:
            self.assistant_message_index -= 1
        if self.in_seek_assistant():
            return self.history[self.assistant_indexes[self.assistant_message_index]]
        else:
            return None

    def seek_next_assistant_message(self):
        """Seek to the next assistant message."""
        if self.in_seek_assistant():
            self.assistant_message_index += 1
            if self.in_seek_assistant():
                return self.history[self.assistant_indexes[self.assistant_message_index]]
        else:
            return None

    def get_last_assistant_message(self):
        """Get the current assistant message."""
        if self.in_seek_assistant():
            return self.history[self.assistant_indexes[self.assistant_message_index]]
        elif len(self.assistant_indexes) > 0:
            return self.history[self.assistant_indexes[-1]]
        else:
            return None

    def update_user_message(self, message):
        """Update the user message at the current seek index and truncate the following messages."""
        index = self.user_indexes[self.user_message_index]
        self.history = self.history[:index]
        self.add_message("user", message)

    def save_history(self, filename):
        """Save the message history to a file."""
        return MessageSaverLoader.save_history(self.history, filename)

    def load_history(self, filename):
        """Load the message history from a file."""
        history = MessageSaverLoader.load_history(filename)
        if history:
            self.history = history
            self.update_indexes()
            return True
        return False
