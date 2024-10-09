from datetime import datetime
class MarkdownExporter:
    def __init__(self, model_name, message_history, date=datetime.now(), skip_system=True):
        self.message_history = message_history
        self.model_name = model_name
        self.date = date
        self.skip_system = skip_system

    def markdown(self, skip_system=True):
        """Export the message history to Markdown."""
        markdown = ""
        # print the model name and date
        markdown += f"# {self.model_name} Chat Log\n\n"
        markdown += f"Date: {self.date.strftime("%Y-%m-%d %H:%M:%S")}\n\n"
        # print the message history
        messages = self.message_history.history.copy()
        # skip the system prompt if requested
        if self.skip_system and messages[0]['role'] == 'system':
            messages = messages[1:]
        for msg in messages:
            role = msg['role']
            # capitalize the role
            role = role[0].upper() + role[1:]
            markdown += f"## {role}\n\n{msg['content']}\n\n"
        return markdown