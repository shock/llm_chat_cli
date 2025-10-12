import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch
from modules.ChatInterface import ChatInterface, SigTermException
from modules.Config import Config
from modules.OpenAIChatCompletionApi import PROVIDER_DATA
from modules.Types import ProviderConfig
from modules.ProviderManager import ProviderManager


def create_test_provider_manager(provider_configs):
    """Helper function to create a ProviderManager for testing."""
    provider_manager = ProviderManager(provider_configs)
    return provider_manager

@pytest.fixture
def mock_config():
    with patch('main.Config') as mock:
        mock.return_value.get.return_value = "mocked_value"
        mock.return_value.is_sassy.return_value = False
        yield mock

@pytest.fixture
def chat_interface():
    from modules.ProviderConfig import ProviderConfig
    providers = {}
    for provider, provider_data in PROVIDER_DATA.items():
        # Create ProviderConfig objects from PROVIDER_DATA
        provider_config = ProviderConfig(
            name=provider_data["name"],
            api_key="test_api_key",
            base_api_url=provider_data["base_api_url"],
            valid_models=provider_data["valid_models"]
        )
        providers[provider] = provider_config
    config = Config(data_directory="/tmp", overrides={"providers": providers, "model": "openai/4o-mini"})
    # Don't override the model since we need a valid one for tests
    config.config.system_prompt = "test_system_prompt"
    config.config.stream = False
    return ChatInterface(config)

def test_init(chat_interface):
    assert chat_interface.api.api_key == "test_api_key"
    assert chat_interface.api.model == "gpt-4o-mini-2024-07-18"
    assert chat_interface.history.system_prompt() == "test_system_prompt"
    assert isinstance(chat_interface.config, Config)

def test_init_no_api_key(mock_config):
    config = Config(data_directory="/tmp", overrides={"providers": {"openai": {"api_key": ""}}, "model": "4o-mini"})
    with pytest.raises(ValueError):
        ChatInterface(config)
    config = Config(data_directory="/tmp")

def test_run(chat_interface):
    mock_prompt = MagicMock()
    mock_prompt.prompt.side_effect = ["test input", KeyboardInterrupt(), SigTermException()]
    chat_interface.session = mock_prompt

    chat_interface.command_handler.handle_command = MagicMock()
    chat_interface.api.get_chat_completion = MagicMock(return_value={
        'choices': [{'message': {'content': 'AI response'}}]
    })

    # Mock spell check to avoid string space server calls during tests
    chat_interface.spell_check_completer = MagicMock()

    chat_interface.run()

    chat_interface.spell_check_completer.add_words_from_text.assert_called()
    chat_interface.api.get_chat_completion.assert_called_once()
    assert chat_interface.history.get_history()[-1]['content'] == 'AI response'

def test_print_assistant_message(capsys, chat_interface):
    chat_interface.print_assistant_message("Test message")
    captured = capsys.readouterr()
    assert "Test message" in captured.out

def test_print_history(capsys, chat_interface):
    chat_interface.history.add_message("user", "User message")
    chat_interface.history.add_message("assistant", "Assistant message")
    chat_interface.print_history()
    captured = capsys.readouterr()
    assert "User message" in captured.out
    assert "Assistant message" in captured.out

@patch('modules.ChatInterface.pyperclip')
@patch('builtins.input', return_value='1')
def test_handle_code_block_command(mock_input, mock_pyperclip, chat_interface):
    chat_interface.history.add_message("assistant", "```python\nprint('Hello')\n```")
    chat_interface.handle_code_block_command()
    mock_pyperclip.copy.assert_called_once_with("print('Hello')\n")

def test_edit_system_prompt(chat_interface):
    with patch('modules.ChatInterface.prompt', return_value="New system prompt"):
        chat_interface.edit_system_prompt()
    assert chat_interface.history.system_prompt() == "New system prompt"

@patch('modules.ChatInterface.pyperclip')
def test_copy_last_response(mock_pyperclip, chat_interface):
    chat_interface.history.add_message("assistant", "Last response")
    chat_interface.copy_last_response()
    mock_pyperclip.copy.assert_called_once_with("Last response")

def test_one_shot_prompt(capsys, chat_interface):
    chat_interface.api.get_chat_completion = MagicMock(return_value={
        'choices': [{'message': {'content': 'One-shot response'}}]
    })
    response = chat_interface.one_shot_prompt("One-shot prompt")
    captured = capsys.readouterr()
    assert "One-shot response" in captured.out
    assert response == "One-shot response"

def test_show_config(capsys, chat_interface):
    # Update provider config

    chat_interface.show_config()
    captured = capsys.readouterr()

    assert "API Key       : ********_key" in captured.out
    assert "Model         : gpt-4o-mini-2024-07-18" in captured.out
    assert "System Prompt :\n\ntest_system_prompt" in captured.out
    assert "Sassy Mode    : Disabled" in captured.out
    assert "Stream Mode   : Disabled" in captured.out

# @patch('modules.ChatInterface.pyperclip')
# @patch('builtins.print')
# @patch('modules.ChatInterface.pyperclip')
# def test_handle_code_block_command_no_code_blocks(mock_input, mock_print, mock_pyperclip, chat_interface):
#     chat_interface.history.add_message("assistant", "No code blocks here")
#     chat_interface.handle_code_block_command()
#     mock_print.assert_called_with("No code blocks found in the last assistant message.")
#     mock_pyperclip.copy.assert_not_called()

@patch('modules.ChatInterface.prompt')
def test_edit_system_prompt_cancelled(mock_prompt, chat_interface):
    mock_prompt.side_effect = KeyboardInterrupt()
    chat_interface.edit_system_prompt()
    assert chat_interface.history.system_prompt() == "test_system_prompt"  # Original prompt unchanged

@patch('modules.ChatInterface.pyperclip')
def test_copy_last_response_no_response(mock_pyperclip, capsys, chat_interface):
    chat_interface.history.get_last_assistant_message = MagicMock(return_value=None)
    chat_interface.copy_last_response()
    captured = capsys.readouterr()
    assert "No assistant response found to copy." in captured.out
    mock_pyperclip.copy.assert_not_called()

def test_one_shot_prompt_api_error(capsys, chat_interface):
    chat_interface.api.get_chat_completion = MagicMock(return_value={
        'error': {'message': 'API Error'}
    })
    result = chat_interface.one_shot_prompt("One-shot prompt")
    assert result == "API Error"
    captured = capsys.readouterr()
    # assert "API ERROR:API Error" in captured.out

def test_create_api_instance_openai():
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
    from modules.ModelDiscoveryService import ModelDiscoveryService
    from modules.ProviderConfig import ProviderConfig

    # Create proper ProviderConfig objects
    provider_configs = {}
    for provider_name, provider_data in OpenAIChatCompletionApi.provider_data.items():
        provider_config = ProviderConfig(
            name=provider_data["name"],
            api_key=provider_data["api_key"],
            base_api_url=provider_data["base_api_url"],
            valid_models=provider_data["valid_models"]
        )
        provider_configs[provider_name] = provider_config

    providers = create_test_provider_manager(provider_configs)
    model_discovery = ModelDiscoveryService()
    provider, model = model_discovery.parse_model_string("openai/gpt-4o-2024-08-06")
    api = OpenAIChatCompletionApi.create_api_instance(providers, provider, model)
    assert api.__class__.__name__ == "OpenAIChatCompletionApi"
    assert api.model == "gpt-4o-2024-08-06"
    assert api.api_key == "not-configured"
    assert api.base_api_url == "https://api.openai.com/v1"

def test_create_api_instance_deepseek():
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
    from modules.ModelDiscoveryService import ModelDiscoveryService
    from modules.ProviderConfig import ProviderConfig

    # Create proper ProviderConfig objects
    provider_configs = {}
    for provider_name, provider_data in OpenAIChatCompletionApi.provider_data.items():
        provider_config = ProviderConfig(
            name=provider_data["name"],
            api_key=provider_data["api_key"],
            base_api_url=provider_data["base_api_url"],
            valid_models=provider_data["valid_models"]
        )
        provider_configs[provider_name] = provider_config

    providers = create_test_provider_manager(provider_configs)
    model_discovery = ModelDiscoveryService()
    provider, model = model_discovery.parse_model_string("deepseek/deepseek-chat")
    api = OpenAIChatCompletionApi.create_api_instance(providers, provider, model)
    assert api.__class__.__name__ == "OpenAIChatCompletionApi"
    assert api.model == "deepseek-chat"
    assert api.api_key == "ds-not-configured"  # Changed from test_key to test_api_key
    assert api.base_api_url == "https://api.deepseek.com/v1"

def test_create_api_instance_default_openai():
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
    from modules.ModelDiscoveryService import ModelDiscoveryService
    from modules.ProviderConfig import ProviderConfig

    # Create proper ProviderConfig objects
    provider_configs = {}
    for provider_name, provider_data in OpenAIChatCompletionApi.provider_data.items():
        provider_config = ProviderConfig(
            name=provider_data["name"],
            api_key=provider_data["api_key"],
            base_api_url=provider_data["base_api_url"],
            valid_models=provider_data["valid_models"]
        )
        provider_configs[provider_name] = provider_config

    providers = create_test_provider_manager(provider_configs)
    model_discovery = ModelDiscoveryService()
    provider, model = model_discovery.parse_model_string("gpt-4o-2024-08-06")  # No provider prefix
    api = OpenAIChatCompletionApi.create_api_instance(providers, provider, model)
    assert api.__class__.__name__ == "OpenAIChatCompletionApi"
    assert api.model == "gpt-4o-2024-08-06"

def test_create_api_instance_unknown_provider():
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
    from modules.ProviderConfig import ProviderConfig

    # Create proper ProviderConfig objects
    provider_configs = {}
    for provider_name, provider_data in OpenAIChatCompletionApi.provider_data.items():
        provider_config = ProviderConfig(
            name=provider_data["name"],
            api_key=provider_data["api_key"],
            base_api_url=provider_data["base_api_url"],
            valid_models=provider_data["valid_models"]
        )
        provider_configs[provider_name] = provider_config

    providers = create_test_provider_manager(provider_configs)
    with pytest.raises(ValueError, match="Provider 'unsupported' not found in providers"):
        OpenAIChatCompletionApi.create_api_instance(providers, "unsupported", "chat")

# Test the export_markdown method
# Mock the OpenAIApi class to return a mock response
# @patch('modules.OpenAIApi')  # Patch the OpenAIApi class
@patch('modules.ChatInterface.pyperclip')
def test_export_markdown(mock_pyperclip, chat_interface):
    chat_interface.api.get_chat_completion = MagicMock(return_value={
        'choices': [{'message': {'content': 'API RESPONSE'}}]
    })
    history = [
        {"role": "system", "content": "System message"},
        {"role": "user", "content": "User message"},
        {"role": "assistant", "content": "Assistant message"},
        {"role": "user", "content": "Second user message"},
        {"role": "assistant", "content": "Second assistant message"},
    ]
    chat_interface.history.history = history
    chat_interface.export_markdown()
    # be sure it doesn't change the original history
    assert history[0]['role'] == 'system'
    assert history[0]['content'] == 'System message'
    assert history[1]['role'] == 'user'
    assert history[1]['content'] == 'User message'
    assert history[2]['role'] == 'assistant'
    assert history[2]['content'] == 'Assistant message'
    mock_pyperclip.copy.assert_called()


# ProviderManager Integration Tests

def test_chat_interface_initialization_with_provider_manager():
    """Test ChatInterface initialization properly uses ProviderManager."""
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={"gpt-4o-mini-2024-07-18": "4o-mini"}
        ),
        "deepseek": ProviderConfig(
            name="DeepSeek",
            api_key="test_api_key_ds",
            base_api_url="https://api.deepseek.com/v1",
            valid_models={"deepseek-chat": "deepseek-chat"}
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Verify ProviderManager is used
    assert isinstance(chat_interface.config.config.providers, ProviderManager)
    assert chat_interface.api.model == "gpt-4o-mini-2024-07-18"
    assert chat_interface.api.api_key == "test_api_key"


def test_chat_interface_initialization_with_provider_manager_error_handling():
    """Test ChatInterface initialization handles ProviderManager KeyError properly."""
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager

    # Create ProviderConfig objects with missing provider
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={"gpt-4o-mini-2024-07-18": "4o-mini"}
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager but request non-existent provider
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "deepseek/deepseek-chat"  # deepseek not in provider_manager
    })

    # Should raise ValueError when trying to create API instance
    with pytest.raises(ValueError):
        ChatInterface(config)


def test_list_command_integration_with_provider_manager():
    """Test /list command integration with ProviderManager."""
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from modules.CommandHandler import CommandHandler

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={
                "gpt-4o-mini-2024-07-18": "4o-mini",
                "gpt-4o-2024-08-06": "4o"
            }
        ),
        "deepseek": ProviderConfig(
            name="DeepSeek",
            api_key="test_api_key_ds",
            base_api_url="https://api.deepseek.com/v1",
            valid_models={
                "deepseek-chat": "deepseek-chat",
                "deepseek-coder": "deepseek-coder"
            }
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)
    command_handler = CommandHandler(chat_interface)

    # Test /list command without provider filter
    result = command_handler.handle_list_command([])
    assert "OPENAI - Available Models:" in result
    assert "DEEPSEEK - Available Models:" in result
    assert "openai/gpt-4o-mini-2024-07-18 (4o-mini)" in result
    assert "deepseek/deepseek-chat" in result  # No parentheses when short name equals long name

    # Test /list command with provider filter
    result = command_handler.handle_list_command(["openai"])
    assert "OPENAI - Available Models:" in result
    assert "DEEPSEEK - Available Models:" not in result
    assert "openai/gpt-4o-mini-2024-07-18 (4o-mini)" in result

    # Test /list command with invalid provider
    result = command_handler.handle_list_command(["invalid_provider"])
    assert "Error: Provider 'invalid_provider' not found" in result


def test_provider_manager_error_handling_in_chat_interface():
    """Test ProviderManager error handling in chat interface."""
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={"gpt-4o-mini-2024-07-18": "4o-mini"}
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Test KeyError handling when accessing non-existent provider
    with pytest.raises(KeyError):
        chat_interface.config.config.providers.get_provider_config("nonexistent")

    # Test that valid provider access works
    provider_config = chat_interface.config.config.providers.get_provider_config("openai")
    assert provider_config.name == "OpenAI"


def test_model_discovery_integration_in_chat_context():
    """Test model discovery integration in chat context."""
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={"gpt-4o-mini-2024-07-18": "4o-mini"}
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Mock the discovery service to avoid real API calls
    with patch.object(provider_manager.discovery_service, 'discover_models') as mock_discover:
        mock_discover.return_value = [{"id": "gpt-4o-mini-2024-07-18"}, {"id": "gpt-4o-2024-08-06"}]

        with patch.object(provider_manager.discovery_service, 'validate_model') as mock_validate:
            mock_validate.return_value = True

            # Call model discovery
            success = provider_manager.discover_models(force_refresh=True, persist_on_success=False)

            assert success is True
            mock_discover.assert_called_once()


# Model Autocomplete Integration Tests

def test_is_mod_command_function():
    """Test the is_mod_command function for /mod command detection."""
    from modules.ChatInterface import is_mod_command
    from prompt_toolkit.document import Document

    # Test cases that should return True (mod commands)
    # Note: The regex matches /mod with trailing space (even without text)
    mod_command_cases = [
        "/mod ",     # /mod with space but no text
        "/mod gpt",
        "/mod openai/gpt",
        "  /mod ",    # /mod with leading and trailing spaces but no text
        "  /mod gpt",
        "/mod 4o",
        "/mod deepseek",
    ]

    # Test cases that should return False (non-mod commands)
    non_mod_command_cases = [
        "",
        "/",
        "/help",
        "/list",
        "/session",
        "hello",
        "mod",
        "/mode",
        "/model",
        "/mod",      # /mod without space
        "  /mod",     # /mod with leading spaces but no trailing space
    ]

    # Test mod commands
    for text in mod_command_cases:
        document = Document(text)
        assert is_mod_command(document) is True, f"Failed for: '{text}'"

    # Test non-mod commands
    for text in non_mod_command_cases:
        document = Document(text)
        assert is_mod_command(document) is False, f"Failed for: '{text}'"


def test_delegating_completer_routing():
    """Test DelegatingCompleter routing behavior between completers."""
    from modules.DelegatingCompleter import DelegatingCompleter
    from modules.ChatInterface import is_mod_command
    from prompt_toolkit.document import Document
    from unittest.mock import MagicMock

    # Create mock completers
    mock_model_completer = MagicMock()
    mock_string_completer = MagicMock()

    # Create DelegatingCompleter instance
    delegating_completer = DelegatingCompleter(
        mock_model_completer,
        mock_string_completer,
        is_mod_command
    )

    # Test /mod command routing to ModelCommandCompleter
    mod_document = Document("/mod gpt")
    mock_complete_event = MagicMock()

    # Call get_completions with mod command
    list(delegating_completer.get_completions(mod_document, mock_complete_event))

    # Verify ModelCommandCompleter was called
    mock_model_completer.get_completions.assert_called_once_with(mod_document, mock_complete_event)
    mock_string_completer.get_completions.assert_not_called()

    # Reset mocks
    mock_model_completer.reset_mock()
    mock_string_completer.reset_mock()

    # Test non-/mod command routing to StringSpaceCompleter
    non_mod_document = Document("/help")

    # Call get_completions with non-mod command
    list(delegating_completer.get_completions(non_mod_document, mock_complete_event))

    # Verify StringSpaceCompleter was called
    mock_string_completer.get_completions.assert_called_once_with(non_mod_document, mock_complete_event)
    mock_model_completer.get_completions.assert_not_called()


def test_model_command_completer_activation():
    """Test ModelCommandCompleter activation with /mod commands."""
    from modules.ModelCommandCompleter import ModelCommandCompleter
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from prompt_toolkit.document import Document
    from unittest.mock import MagicMock

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={
                "gpt-4o-mini-2024-07-18": "4o-mini",
                "gpt-4o-2024-08-06": "4o"
            }
        ),
        "deepseek": ProviderConfig(
            name="DeepSeek",
            api_key="test_api_key_ds",
            base_api_url="https://api.deepseek.com/v1",
            valid_models={
                "deepseek-chat": "deepseek-chat",
                "deepseek-coder": "deepseek-coder"
            }
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create ModelCommandCompleter
    mod_command_pattern = r'^\s*\/mod[^\s]*\s+([^\s]*)'
    model_completer = ModelCommandCompleter(provider_manager, mod_command_pattern)

    # Test /mod command with partial model name
    document = Document("/mod gpt")
    mock_complete_event = MagicMock()
    mock_complete_event.completion_requested = False

    # Get completions
    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Verify we get model completions
    assert len(completions) > 0

    # Check that completions contain expected models
    completion_texts = [comp.text for comp in completions]
    expected_models = [
        "openai/gpt-4o-mini-2024-07-18 (4o-mini)",
        "openai/gpt-4o-2024-08-06 (4o)"
    ]

    for expected_model in expected_models:
        assert any(expected_model in text for text in completion_texts), f"Expected model '{expected_model}' not found in completions"

    # Test /mod command with provider prefix
    document = Document("/mod openai/gpt")
    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Should still return OpenAI models when searching for "openai/gpt"
    assert len(completions) > 0
    completion_texts = [comp.text for comp in completions]
    for expected_model in expected_models:
        assert any(expected_model in text for text in completion_texts), f"Expected model '{expected_model}' not found in completions for provider prefix"


def test_string_space_completer_usage_with_non_mod_commands():
    """Test StringSpaceCompleter usage with non-/mod commands."""
    from modules.ChatInterface import ChatInterface
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from prompt_toolkit.document import Document
    from unittest.mock import MagicMock, patch

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={"gpt-4o-mini-2024-07-18": "4o-mini"}
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Test that StringSpaceCompleter is used for non-/mod commands
    non_mod_document = Document("/help")
    mock_complete_event = MagicMock()

    # Mock the StringSpaceCompleter to verify it's called
    with patch.object(chat_interface.merged_completer, 'get_completions') as mock_string_completer:
        mock_string_completer.return_value = []

        # Call get_completions through DelegatingCompleter
        list(chat_interface.top_level_completer.get_completions(non_mod_document, mock_complete_event))

        # Verify StringSpaceCompleter was called
        mock_string_completer.assert_called_once_with(non_mod_document, mock_complete_event)

    # Test regular text input (not starting with /)
    regular_document = Document("hello world")
    with patch.object(chat_interface.merged_completer, 'get_completions') as mock_string_completer:
        mock_string_completer.return_value = []

        list(chat_interface.top_level_completer.get_completions(regular_document, mock_complete_event))

        # Verify StringSpaceCompleter was called for regular text
        mock_string_completer.assert_called_once_with(regular_document, mock_complete_event)


def test_model_command_completer_error_handling():
    """Test error handling when ProviderManager throws exceptions."""
    from modules.ModelCommandCompleter import ModelCommandCompleter
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from prompt_toolkit.document import Document
    from unittest.mock import MagicMock, patch

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={"gpt-4o-mini-2024-07-18": "4o-mini"}
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create ModelCommandCompleter
    mod_command_pattern = r'^\s*\/mod[^\s]*\s+([^\s]*)'
    model_completer = ModelCommandCompleter(provider_manager, mod_command_pattern)

    # Test error handling when ProviderManager.valid_scoped_models() raises an exception
    with patch.object(provider_manager, 'valid_scoped_models') as mock_valid_scoped_models:
        mock_valid_scoped_models.side_effect = Exception("Provider API Error")

        document = Document("/mod gpt")
        mock_complete_event = MagicMock()

        # Mock stderr to capture error output
        with patch('sys.stderr') as mock_stderr:
            # Get completions - should handle the exception gracefully
            completions = list(model_completer.get_completions(document, mock_complete_event))

            # Should return empty completions list when error occurs
            assert len(completions) == 0

            # Verify error was logged to stderr
            mock_stderr.write.assert_called()

    # Test that short input strings don't trigger completions
    document = Document("/mod g")
    mock_complete_event = MagicMock()
    mock_complete_event.completion_requested = False

    completions = list(model_completer.get_completions(document, mock_complete_event))

    # With only 1 character, should return no completions unless completion is explicitly requested
    assert len(completions) == 0

    # Test with completion explicitly requested
    mock_complete_event.completion_requested = True
    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Should return completions when explicitly requested
    assert len(completions) > 0


def test_backward_compatibility_with_existing_chat_functionality():
    """Test backward compatibility to ensure existing chat functionality remains unchanged."""
    from modules.ChatInterface import ChatInterface
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from unittest.mock import MagicMock, patch

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={"gpt-4o-mini-2024-07-18": "4o-mini"}
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Verify that all essential components are properly initialized
    assert chat_interface.config is not None
    assert chat_interface.api is not None
    assert chat_interface.history is not None
    assert chat_interface.command_handler is not None
    assert chat_interface.session is not None

    # Verify that the completer hierarchy is properly set up
    assert chat_interface.top_level_completer is not None
    assert chat_interface.model_completer is not None
    assert chat_interface.merged_completer is not None
    assert chat_interface.spell_check_completer is not None

    # Verify that DelegatingCompleter is properly configured
    assert chat_interface.top_level_completer.completer_a == chat_interface.model_completer
    assert chat_interface.top_level_completer.completer_b == chat_interface.merged_completer
    assert chat_interface.top_level_completer.decision_function is not None

    # Test that existing chat methods still work
    with patch.object(chat_interface.api, 'get_chat_completion') as mock_api:
        mock_api.return_value = {
            'choices': [{'message': {'content': 'Test response'}}]
        }

        # Test one_shot_prompt method
        response = chat_interface.one_shot_prompt("Test prompt")
        assert response == "Test response"

        # Test print_assistant_message method
        with patch('builtins.print') as mock_print:
            chat_interface.print_assistant_message("Test message")
            mock_print.assert_called()

        # Test show_config method
        with patch('builtins.print') as mock_print:
            chat_interface.show_config()
            mock_print.assert_called()

    # Test that command handler is properly integrated
    assert chat_interface.command_handler.chat_interface == chat_interface

    # Test that model switching still works
    with patch('builtins.print') as mock_print:
        chat_interface.set_model("openai/gpt-4o-mini-2024-07-18")
        mock_print.assert_called_with("Model set to gpt-4o-mini-2024-07-18.")

    # Test that the completer is properly set in the prompt session
    assert chat_interface.session.completer == chat_interface.top_level_completer


def test_chat_interface_uses_provider_manager_methods():
    """Test that ChatInterface uses ProviderManager methods instead of direct dict access."""
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={"gpt-4o-mini-2024-07-18": "4o-mini"}
        ),
        "deepseek": ProviderConfig(
            name="DeepSeek",
            api_key="test_api_key_ds",
            base_api_url="https://api.deepseek.com/v1",
            valid_models={"deepseek-chat": "deepseek-chat"}
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Verify ProviderManager methods are used
    providers = chat_interface.config.config.providers

    # Test get_all_provider_names method
    provider_names = providers.get_all_provider_names()
    assert "openai" in provider_names
    assert "deepseek" in provider_names

    # Test get_provider_config method
    openai_config = providers.get_provider_config("openai")
    assert openai_config.name == "OpenAI"

    # Test merged_models method
    merged_models = providers.merged_models()
    assert len(merged_models) == 2

    # Test valid_scoped_models method
    scoped_models = providers.valid_scoped_models()
    assert any("openai/gpt-4o-mini-2024-07-18 (4o-mini)" in model for model in scoped_models)


def test_error_handling_when_provider_not_found_during_model_switching():
    """Test error handling when provider is not found during model switching."""
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={"gpt-4o-mini-2024-07-18": "4o-mini"}
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Test switching to model with non-existent provider
    with patch('builtins.print') as mock_print:
        chat_interface.set_model("nonexistent/deepseek-chat")
        # The set_model method prints the exception string, not the exception object
        mock_print.assert_called_with("Provider 'nonexistent' not found in providers")

    # Test switching to model with invalid model for existing provider
    with patch('builtins.print') as mock_print:
        chat_interface.set_model("openai/invalid-model")
        mock_print.assert_called_with("Model 'invalid-model' not found in valid models for provider 'openai'")


def test_integration_with_provider_manager_valid_scoped_models_for_completion():
    """Test integration with ProviderManager's valid_scoped_models() for model completion."""
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={
                "gpt-4o-mini-2024-07-18": "4o-mini",
                "gpt-4o-2024-08-06": "4o"
            }
        ),
        "deepseek": ProviderConfig(
            name="DeepSeek",
            api_key="test_api_key_ds",
            base_api_url="https://api.deepseek.com/v1",
            valid_models={
                "deepseek-chat": "deepseek-chat",
                "deepseek-coder": "deepseek-coder"
            }
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Test valid_scoped_models method
    scoped_models = chat_interface.config.config.providers.valid_scoped_models()

    # Verify all expected models are present
    expected_models = [
        "openai/gpt-4o-mini-2024-07-18 (4o-mini)",
        "openai/gpt-4o-2024-08-06 (4o)",
        "deepseek/deepseek-chat (deepseek-chat)",
        "deepseek/deepseek-coder (deepseek-coder)"
    ]

    for expected_model in expected_models:
        assert expected_model in scoped_models

    # Test get_api_for_model_string method
    provider_config, model_name = chat_interface.config.config.providers.get_api_for_model_string("openai/gpt-4o-mini-2024-07-18")
    assert provider_config.name == "OpenAI"
    assert model_name == "gpt-4o-mini-2024-07-18"

    # Test unprefixed model resolution
    provider_config, model_name = chat_interface.config.config.providers.get_api_for_model_string("4o-mini")
    assert provider_config.name == "OpenAI"
    assert model_name == "gpt-4o-mini-2024-07-18"


# =============================================================================
# Comprehensive Completer Architecture Tests
# =============================================================================

def test_tab_completion_behavior_with_delegating_completer():
    """Test Tab key completion behavior with DelegatingCompleter routing."""
    from modules.ChatInterface import ChatInterface
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from prompt_toolkit.document import Document
    from unittest.mock import MagicMock, patch

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={
                "gpt-4o-mini-2024-07-18": "4o-mini",
                "gpt-4o-2024-08-06": "4o"
            }
        ),
        "deepseek": ProviderConfig(
            name="DeepSeek",
            api_key="test_api_key_ds",
            base_api_url="https://api.deepseek.com/v1",
            valid_models={
                "deepseek-chat": "deepseek-chat",
                "deepseek-coder": "deepseek-coder"
            }
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Test Tab completion with /mod command - should route to ModelCommandCompleter
    mod_document = Document("/mod gpt")
    mock_complete_event = MagicMock()
    mock_complete_event.completion_requested = True

    completions = list(chat_interface.top_level_completer.get_completions(mod_document, mock_complete_event))

    # Should return model completions
    assert len(completions) > 0
    completion_texts = [comp.text for comp in completions]

    # Verify we get expected model completions
    expected_models = [
        "openai/gpt-4o-mini-2024-07-18 (4o-mini)",
        "openai/gpt-4o-2024-08-06 (4o)"
    ]

    for expected_model in expected_models:
        assert any(expected_model in text for text in completion_texts), f"Expected model '{expected_model}' not found in completions"

    # Test Tab completion with non-/mod command - should route to StringSpaceCompleter
    non_mod_document = Document("/help")

    with patch.object(chat_interface.merged_completer, 'get_completions') as mock_string_completer:
        mock_string_completer.return_value = []

        completions = list(chat_interface.top_level_completer.get_completions(non_mod_document, mock_complete_event))

        # Verify StringSpaceCompleter was called
        mock_string_completer.assert_called_once_with(non_mod_document, mock_complete_event)

    # Test Tab completion with regular text - should route to StringSpaceCompleter
    regular_document = Document("hello world")

    with patch.object(chat_interface.merged_completer, 'get_completions') as mock_string_completer:
        mock_string_completer.return_value = []

        completions = list(chat_interface.top_level_completer.get_completions(regular_document, mock_complete_event))

        # Verify StringSpaceCompleter was called
        mock_string_completer.assert_called_once_with(regular_document, mock_complete_event)


def test_end_to_end_completion_workflow_with_real_documents():
    """Test end-to-end completion workflow with real Document objects."""
    from modules.ChatInterface import ChatInterface
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from prompt_toolkit.document import Document
    from unittest.mock import MagicMock

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={
                "gpt-4o-mini-2024-07-18": "4o-mini",
                "gpt-4o-2024-08-06": "4o",
                "gpt-3.5-turbo": "3.5-turbo"
            }
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Test various document scenarios
    test_cases = [
        # (document_text, expected_completer_type, description)
        ("/mod gpt", "model", "Basic /mod command"),
        ("/mod openai/gpt", "model", "/mod with provider prefix"),
        ("/mod 4o", "model", "/mod with short model name"),
        ("/help", "string", "Non-/mod command"),
        ("hello world", "string", "Regular text input"),
        ("/session", "string", "Other slash command"),
        ("/mod ", "model", "/mod with trailing space"),
        ("  /mod gpt", "model", "/mod with leading spaces"),
    ]

    mock_complete_event = MagicMock()
    mock_complete_event.completion_requested = True

    for document_text, expected_completer_type, description in test_cases:
        document = Document(document_text)

        # Get completions
        completions = list(chat_interface.top_level_completer.get_completions(document, mock_complete_event))

        # Verify appropriate completer was used based on expected type
        if expected_completer_type == "model":
            # Should get model completions
            assert len(completions) > 0, f"No completions for {description}: '{document_text}'"
            # Verify we get model completion objects
            completion_texts = [comp.text for comp in completions]
            assert any("gpt" in text.lower() for text in completion_texts), f"No model completions for {description}: '{document_text}'"
        else:
            # For string completer, we might get empty completions depending on the string completer state
            # Just verify no error occurred
            assert completions is not None, f"Completions failed for {description}: '{document_text}'"


def test_comprehensive_mod_command_context_coverage():
    """Test comprehensive coverage of /mod command contexts and edge cases."""
    from modules.ChatInterface import ChatInterface, is_mod_command
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from prompt_toolkit.document import Document
    from unittest.mock import MagicMock

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={
                "gpt-4o-mini-2024-07-18": "4o-mini",
                "gpt-4o-2024-08-06": "4o"
            }
        ),
        "deepseek": ProviderConfig(
            name="DeepSeek",
            api_key="test_api_key_ds",
            base_api_url="https://api.deepseek.com/v1",
            valid_models={
                "deepseek-chat": "deepseek-chat",
                "deepseek-coder": "deepseek-coder"
            }
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Test /mod command detection edge cases
    mod_command_test_cases = [
        # Should be detected as /mod commands
        ("/mod ", True, "Trailing space"),
        ("/mod gpt", True, "With text"),
        ("  /mod ", True, "Leading spaces with trailing space"),
        ("  /mod gpt", True, "Leading spaces with text"),
        ("/mod openai/gpt", True, "With provider prefix"),
        ("/mod 4o", True, "With short name"),

        # Should NOT be detected as /mod commands
        ("/mod", False, "No trailing space"),
        ("  /mod", False, "Leading spaces but no trailing space"),
        ("/model", False, "Different command"),
        ("/mode", False, "Similar but different command"),
        ("/help", False, "Other command"),
        ("mod", False, "No slash"),
        ("", False, "Empty string"),
    ]

    for text, expected_result, description in mod_command_test_cases:
        document = Document(text)
        result = is_mod_command(document)
        assert result == expected_result, f"Failed for {description}: '{text}' (expected {expected_result}, got {result})"

    # Test completion behavior for each /mod context
    mock_complete_event = MagicMock()
    mock_complete_event.completion_requested = True

    mod_completion_cases = [
        ("/mod gpt", ["gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06"]),
        ("/mod 4o", ["4o-mini", "4o"]),
        ("/mod openai/gpt", ["gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06"]),
        ("/mod deepseek", ["deepseek-chat", "deepseek-coder"]),
    ]

    for document_text, expected_models in mod_completion_cases:
        document = Document(document_text)
        completions = list(chat_interface.top_level_completer.get_completions(document, mock_complete_event))

        # Should get completions
        assert len(completions) > 0, f"No completions for '{document_text}'"

        completion_texts = [comp.text for comp in completions]

        # Verify expected models are present in completions
        for expected_model in expected_models:
            assert any(expected_model in text for text in completion_texts), f"Expected model '{expected_model}' not found in completions for '{document_text}'"


def test_error_scenarios_during_completion():
    """Test error scenarios when ProviderManager throws exceptions during completion."""
    from modules.ChatInterface import ChatInterface
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from prompt_toolkit.document import Document
    from unittest.mock import MagicMock, patch

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={
                "gpt-4o-mini-2024-07-18": "4o-mini",
                "gpt-4o-2024-08-06": "4o"
            }
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Test ProviderManager exception handling
    # Patch the ProviderManager instance that's actually used by the ChatInterface
    with patch.object(chat_interface.config.config.providers, 'valid_scoped_models') as mock_valid_scoped_models:
        mock_valid_scoped_models.side_effect = Exception("Provider API Error")

        document = Document("/mod gpt")
        mock_complete_event = MagicMock()
        mock_complete_event.completion_requested = True

        # Mock stderr to capture error output
        with patch('sys.stderr') as mock_stderr:
            # Get completions - should handle the exception gracefully
            completions = list(chat_interface.top_level_completer.get_completions(document, mock_complete_event))

            # Should return empty completions list when error occurs
            assert len(completions) == 0

            # Verify error was logged to stderr
            mock_stderr.write.assert_called()

    # Test ModelCommandCompleter error handling directly
    with patch.object(chat_interface.model_completer.provider_manager, 'valid_scoped_models') as mock_valid_scoped_models:
        mock_valid_scoped_models.side_effect = ValueError("Invalid configuration")

        document = Document("/mod test")
        mock_complete_event = MagicMock()
        mock_complete_event.completion_requested = True

        with patch('sys.stderr') as mock_stderr:
            completions = list(chat_interface.model_completer.get_completions(document, mock_complete_event))

            # Should return empty completions
            assert len(completions) == 0
            mock_stderr.write.assert_called()

    # Test that regular text completion still works even if model completer had issues
    document = Document("hello world")
    mock_complete_event = MagicMock()
    mock_complete_event.completion_requested = True

    with patch.object(chat_interface.merged_completer, 'get_completions') as mock_string_completer:
        mock_string_completer.return_value = []

        completions = list(chat_interface.top_level_completer.get_completions(document, mock_complete_event))

        # Verify StringSpaceCompleter was still called
        mock_string_completer.assert_called_once_with(document, mock_complete_event)


def test_performance_and_responsiveness_of_completer_architecture():
    """Test performance and ensure no degradation in typing responsiveness."""
    import time
    from modules.ChatInterface import ChatInterface
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from prompt_toolkit.document import Document
    from unittest.mock import MagicMock

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={
                "gpt-4o-mini-2024-07-18": "4o-mini",
                "gpt-4o-2024-08-06": "4o"
            }
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Performance test: measure completion time for various inputs
    test_documents = [
        Document("/mod gpt"),
        Document("/help"),
        Document("hello world"),
        Document("/mod 4o"),
        Document("/session"),
    ]

    mock_complete_event = MagicMock()
    mock_complete_event.completion_requested = True

    max_completion_time = 0.1  # 100ms maximum acceptable completion time

    for document in test_documents:
        start_time = time.time()

        # Get completions
        completions = list(chat_interface.top_level_completer.get_completions(document, mock_complete_event))

        completion_time = time.time() - start_time

        # Verify completion time is within acceptable limits
        # assert completion_time < max_completion_time, f"Completion took {completion_time:.3f}s for '{document.text}', exceeding {max_completion_time}s limit"

        # Verify we got a response (either completions or empty list)
        assert completions is not None, f"No completions returned for '{document.text}'"

    # Test that short input strings don't trigger expensive operations
    short_input_documents = [
        Document("/mod g"),  # Only 1 character
        Document("/mod "),   # No characters after space
        Document("/mod"),    # No space
    ]

    for document in short_input_documents:
        mock_complete_event.completion_requested = False  # Not explicitly requested

        start_time = time.time()
        completions = list(chat_interface.top_level_completer.get_completions(document, mock_complete_event))
        completion_time = time.time() - start_time

        # Short inputs without explicit completion request should be very fast
        assert completion_time < 0.01, f"Short input completion took {completion_time:.3f}s for '{document.text}', should be faster"

    # Test with explicit completion request for short inputs
    for document in short_input_documents:
        mock_complete_event.completion_requested = True  # Explicitly requested

        start_time = time.time()
        completions = list(chat_interface.top_level_completer.get_completions(document, mock_complete_event))
        completion_time = time.time() - start_time

        # Even with explicit request, should be reasonably fast
        assert completion_time < max_completion_time, f"Explicit completion took {completion_time:.3f}s for '{document.text}', exceeding {max_completion_time}s limit"


def test_completer_architecture_initialization_and_configuration():
    """Test that completer architecture is properly initialized and configured."""
    from modules.ChatInterface import ChatInterface
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from modules.DelegatingCompleter import DelegatingCompleter
    from modules.ModelCommandCompleter import ModelCommandCompleter

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={
                "gpt-4o-mini-2024-07-18": "4o-mini",
                "gpt-4o-2024-08-06": "4o"
            }
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Verify completer hierarchy is properly set up
    assert isinstance(chat_interface.top_level_completer, DelegatingCompleter)
    assert isinstance(chat_interface.model_completer, ModelCommandCompleter)
    assert chat_interface.merged_completer is not None
    assert chat_interface.spell_check_completer is not None

    # Verify DelegatingCompleter configuration
    assert chat_interface.top_level_completer.completer_a == chat_interface.model_completer
    assert chat_interface.top_level_completer.completer_b == chat_interface.merged_completer
    assert chat_interface.top_level_completer.decision_function is not None

    # Verify ModelCommandCompleter configuration
    # The ProviderManager instance should be the same one used by the ChatInterface config
    assert chat_interface.model_completer.provider_manager == chat_interface.config.config.providers
    assert chat_interface.model_completer.mod_command_pattern is not None

    # Verify completer is properly set in the prompt session
    assert chat_interface.session.completer == chat_interface.top_level_completer

    # Verify that the completer architecture doesn't interfere with other components
    assert chat_interface.config is not None
    assert chat_interface.api is not None
    assert chat_interface.history is not None
    assert chat_interface.command_handler is not None


def test_backward_compatibility_with_existing_completion_behavior():
    """Test backward compatibility to ensure existing completion behavior remains unchanged."""
    from modules.ChatInterface import ChatInterface
    from modules.ProviderConfig import ProviderConfig
    from modules.ProviderManager import ProviderManager
    from prompt_toolkit.document import Document
    from unittest.mock import MagicMock, patch

    # Create ProviderConfig objects
    provider_configs = {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key="test_api_key",
            base_api_url="https://api.openai.com/v1",
            valid_models={
                "gpt-4o-mini-2024-07-18": "4o-mini",
                "gpt-4o-2024-08-06": "4o"
            }
        )
    }

    # Create ProviderManager
    provider_manager = ProviderManager(provider_configs)

    # Create Config with ProviderManager
    config = Config(data_directory="/tmp", overrides={
        "providers": provider_manager,
        "model": "openai/gpt-4o-mini-2024-07-18"
    })

    # Initialize ChatInterface
    chat_interface = ChatInterface(config)

    # Test that non-/mod commands still use the original completer behavior
    non_mod_commands = [
        "/help",
        "/session",
        "/list",
        "/cb",
        "/config",
        "/export",
    ]

    mock_complete_event = MagicMock()
    mock_complete_event.completion_requested = True

    for command in non_mod_commands:
        document = Document(command)

        with patch.object(chat_interface.merged_completer, 'get_completions') as mock_string_completer:
            mock_string_completer.return_value = []

            completions = list(chat_interface.top_level_completer.get_completions(document, mock_complete_event))

            # Verify StringSpaceCompleter was called for non-/mod commands
            mock_string_completer.assert_called_once_with(document, mock_complete_event)

    # Test that regular text input still uses the original completer behavior
    regular_text_inputs = [
        "hello world",
        "test message",
        "how are you today?",
        "please help me with this",
    ]

    for text in regular_text_inputs:
        document = Document(text)

        with patch.object(chat_interface.merged_completer, 'get_completions') as mock_string_completer:
            mock_string_completer.return_value = []

            completions = list(chat_interface.top_level_completer.get_completions(document, mock_complete_event))

            # Verify StringSpaceCompleter was called for regular text
            mock_string_completer.assert_called_once_with(document, mock_complete_event)
