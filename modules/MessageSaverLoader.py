import json

class MessageSaverLoader:
    """Handles saving and loading the message history to/from files."""

    @staticmethod
    def save_history(history, filename):
        """Save the message history to a file."""
        try:
            with open(filename, 'w') as f:
                json.dump(history, f, indent=4)
            print(f"Chat history saved to `{filename}`.")
            return True
        except Exception as e:
            print(f"Error: Failed to save history to `{filename}`: {e}")
            return False

    @staticmethod
    def load_history(filename):
        """Load the message history from a file."""
        try:
            with open(filename, 'r') as f:
                history = json.load(f)
            print(f"Chat history loaded from `{filename}`.")
            return history
        except Exception as e:
            print(f"Error: Failed to load history from `{filename}`: {e}")
            return None
