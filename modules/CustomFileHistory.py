from prompt_toolkit.history import FileHistory

class CustomFileHistory(FileHistory):
    """
    :class:`.FileHistory` class that limits the number of history entries.
    """

    def __init__(self, filename: str, max_history: int = None, skip_prefixes: list[str] = []) -> None:
        super().__init__(filename)
        self.max_history = max_history
        self.skip_prefixes = skip_prefixes

    def append_string(self, string: str) -> None:
        if any(string.startswith(prefix) for prefix in self.skip_prefixes):
            return
        super().append_string(string)
        if self.max_history and len(self._loaded_strings) > self.max_history:
            self._loaded_strings.pop()
            self._truncate_file()

    def _truncate_file(self) -> None:
        """
        Truncate the file to remove the oldest entry.
        """
        with open(self.filename, "rb") as f:
            lines = f.readlines()

        # Find the position of the last entry to keep.
        count = 0
        pos = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith(b"+"):
                count += 1
                if count == self.max_history:
                    pos = i
                    break

        # Write back the truncated file.
        with open(self.filename, "wb") as f:
            f.writelines(lines[:pos])

    def clear_history(self):
        """Clear the history file."""
        with open(self.filename, "w") as f:
            f.write("") # clear the file
        self._loaded_strings = []
