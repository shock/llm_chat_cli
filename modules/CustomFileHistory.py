import re
from prompt_toolkit.history import FileHistory
from typing import Optional

"""
CustomFileHistory class that limits the number of history entries.
For use with prompt_toolkit.
"""
class CustomFileHistory(FileHistory):
    """
    :class:`.FileHistory` class that limits the number of history entries.
    """

    def __init__(self, filename: str, max_history: Optional[int] = None, skip_prefixes: list[str] = []) -> None:
        super().__init__(filename)
        self.max_history = max_history
        self.skip_prefixes = skip_prefixes
        self.usage_count = 0
        self.high_water_mark = 10

    def append_string(self, string: str) -> None:
        if any(string.startswith(prefix) for prefix in self.skip_prefixes):
            return
        super().append_string(string)
        self.usage_count += 1
        if self.usage_count > self.high_water_mark:
            self.usage_count = 0
            self._truncate_file()

    def _truncate_file(self) -> None:
        """
        Truncate the file to remove the oldest entries.
        """
        # Open the file and read its contents
        with open(self.filename, 'r') as file:
            content = file.read()

        # Define the regex pattern
        pattern = r'\n#.*?(?:\n\+.*?)*(?=\n#|\Z)'

        # Find all matches in the content
        matches = re.findall(pattern, content, re.DOTALL)

        if self.max_history and len(matches) > self.max_history:
            matches = matches[-self.max_history:]

            # Store each entry in an array
            entries = [f"\n{match.strip()}" for match in matches]

            with open(self.filename, "w") as f:
                # write the truncated entrieq to the file
                f.write("\n".join(entries))
                f.write("\n")

            self._loaded_strings = list(self.load_history_strings())


    def clear_history(self):
        """Clear the history file."""
        with open(self.filename, "w") as f:
            f.write("") # clear the file
        self._loaded_strings = []
