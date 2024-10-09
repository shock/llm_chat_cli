import pytest
from modules.MarkdownExporter import MarkdownExporter
from modules.MessageHistory import MessageHistory
from datetime import datetime

@pytest.fixture
def message_history():
    history = [
        {"role": "user", "content": "User message"},
        {"role": "assistant", "content": "Assistant message"},
        {"role": "user", "content": "Second user message"},
        {"role": "assistant", "content": "Second assistant message"},
    ]
    msg_history = MessageHistory(system_prompt="System prompt")
    for msg in history:
        msg_history.add_message(msg['role'], msg['content'])
    return msg_history

def test_markdown(message_history):
    exporter = MarkdownExporter("Test model", message_history)
    markdown = exporter.markdown()
    assert "System prompt" not in markdown
    assert "Test model" in markdown
    assert "Date:" in markdown
    assert "## User\n\n" in markdown
    assert "## Assistant\n\n" in markdown
    assert "User message" in markdown
    assert "Assistant message" in markdown
    assert "Second user message" in markdown
    assert "Second assistant message" in markdown

def test_markdown_skip_system(message_history):
    exporter = MarkdownExporter("Test model", message_history, skip_system=False)
    markdown = exporter.markdown()
    assert "System prompt" in markdown

def test_markdown_with_date(message_history):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    exporter = MarkdownExporter("Test model", message_history, date=now)
    markdown = exporter.markdown()
    assert date_str in markdown

def test_markdown_with_title(message_history):
    exporter = MarkdownExporter("Test model", message_history, title="Test title")
    markdown = exporter.markdown()
    assert "# Test title\n(Test model)" in markdown

def test_markdown_with_file(message_history):
    exporter = MarkdownExporter("Test model", message_history, file="test")
    markdown = exporter.markdown()
    assert "test.md\n\n" in markdown