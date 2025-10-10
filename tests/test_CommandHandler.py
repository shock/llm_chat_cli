import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch
from modules.CommandHandler import CommandHandler
from modules.InAppHelp import IN_APP_HELP

class MockChatInterface:
    def __init__(self):
        self.chat_history = MagicMock()
        self.history = MagicMock()
        self.print_history = MagicMock()
        self.edit_system_prompt = MagicMock()
        self.show_config = MagicMock()
        self.handle_code_block_command = MagicMock()
        self.export_markdown = MagicMock()
        self.set_model = MagicMock()
        self.set_default_model = MagicMock()
        self.clear_history = MagicMock()

        # Mock ProviderManager configuration
        self.config = MagicMock()
        self.config.config = MagicMock()
        self.config.config.providers = MagicMock()

@pytest.fixture
def command_handler():
    return CommandHandler(MockChatInterface())

def test_help_command(command_handler, capsys):
    command_handler.handle_command('/help')
    captured = capsys.readouterr()
    assert IN_APP_HELP in captured.out

def test_clear_history_command(command_handler, capsys):
    command_handler.handle_command('/clear_history')
    command_handler.chat_interface.chat_history.clear_history.assert_called_once()
    captured = capsys.readouterr()
    assert "Chat file history cleared." in captured.out

@patch('os.system')
def test_clear_command(mock_system, command_handler):
    command_handler.handle_command('/clear')
    mock_system.assert_called_once()

def test_reset_command(command_handler, capsys):
    command_handler.handle_command('/reset')
    command_handler.chat_interface.clear_history.assert_called_once()
    captured = capsys.readouterr()
    assert "Chat history reset." in captured.out

@patch('builtins.input', return_value='test.json')
def test_save_command(mock_input, command_handler):
    command_handler.handle_command('/save')
    command_handler.chat_interface.history.save_history.assert_called_once_with('test.json')

@patch('builtins.input', return_value='test.json')
def test_load_command(mock_input, command_handler):
    command_handler.chat_interface.history.load_history.return_value = True
    command_handler.handle_command('/load')
    command_handler.chat_interface.history.load_history.assert_called_once_with('test.json')
    command_handler.chat_interface.print_history.assert_called_once()

def test_sp_command(command_handler):
    command_handler.handle_command('/sp')
    command_handler.chat_interface.edit_system_prompt.assert_called_once()

def test_cb_command(command_handler):
    command_handler.handle_command('/cb')
    command_handler.chat_interface.handle_code_block_command.assert_called_once()

def test_md_command(command_handler):
    command_handler.handle_command('/md')
    command_handler.chat_interface.export_markdown.assert_called_once()

def test_unknown_command(command_handler, capsys):
    command_handler.handle_command('/unknown')
    captured = capsys.readouterr()
    assert "Unknown command. Type /h for a list of commands." in captured.out

@pytest.mark.parametrize("exit_command", ['/exit', '/e', '/q'])
def test_exit_command(exit_command, command_handler):
    with pytest.raises(SystemExit):
        command_handler.handle_command(exit_command)

# Tests for handle_list_command method
def test_handle_list_command_with_provider_filter(command_handler):
    """Test /list command with provider filter argument."""
    # Mock ProviderManager methods
    mock_provider_config = MagicMock()
    mock_provider_config.get_valid_models.return_value = ['gpt-4o', 'gpt-4o-mini']
    mock_provider_config.valid_models = {
        'gpt-4o': 'gpt4o',
        'gpt-4o-mini': 'gpt4omini'
    }

    # Reset mock call count before test
    command_handler.chat_interface.config.config.providers.get.reset_mock()
    command_handler.chat_interface.config.config.providers.get.return_value = mock_provider_config

    # Test with provider filter
    result = command_handler.handle_list_command(['openai'])

    # Verify ProviderManager was called correctly
    assert command_handler.chat_interface.config.config.providers.get.call_count == 2
    command_handler.chat_interface.config.config.providers.get.assert_any_call('openai')

    # Verify output format
    assert '**OPENAI - Available Models:**' in result
    assert '• openai/gpt-4o (gpt4o)' in result
    assert '• openai/gpt-4o-mini (gpt4omini)' in result

def test_handle_list_command_without_provider_filter(command_handler):
    """Test /list command without provider filter (all providers)."""
    # Mock ProviderManager methods
    mock_openai_config = MagicMock()
    mock_openai_config.get_valid_models.return_value = ['gpt-4o', 'gpt-4o-mini']
    mock_openai_config.valid_models = {
        'gpt-4o': 'gpt4o',
        'gpt-4o-mini': 'gpt4omini'
    }

    mock_anthropic_config = MagicMock()
    mock_anthropic_config.get_valid_models.return_value = ['claude-3-5-sonnet-20241022']
    mock_anthropic_config.valid_models = {
        'claude-3-5-sonnet-20241022': 'claude35sonnet'
    }

    command_handler.chat_interface.config.config.providers.get_all_provider_names.return_value = ['openai', 'anthropic']
    command_handler.chat_interface.config.config.providers.get.side_effect = [
        mock_openai_config, mock_anthropic_config
    ]

    # Test without provider filter
    result = command_handler.handle_list_command([])

    # Verify ProviderManager was called correctly
    command_handler.chat_interface.config.config.providers.get_all_provider_names.assert_called_once()
    assert command_handler.chat_interface.config.config.providers.get.call_count == 2

    # Verify output format
    assert '**OPENAI - Available Models:**' in result
    assert '• openai/gpt-4o (gpt4o)' in result
    assert '• openai/gpt-4o-mini (gpt4omini)' in result
    assert '**ANTHROPIC - Available Models:**' in result
    assert '• anthropic/claude-3-5-sonnet-20241022 (claude35sonnet)' in result

def test_handle_list_command_with_invalid_provider(command_handler):
    """Test /list command with invalid provider name."""
    # Mock ProviderManager to return None for invalid provider
    command_handler.chat_interface.config.config.providers.get.return_value = None

    # Test with invalid provider
    result = command_handler.handle_list_command(['invalid_provider'])

    # Verify error message
    assert result == "Error: Provider 'invalid_provider' not found"

    # Verify ProviderManager was called correctly
    command_handler.chat_interface.config.config.providers.get.assert_called_once_with('invalid_provider')

def test_handle_list_command_integration_with_provider_manager(command_handler):
    """Test integration with ProviderManager's model discovery."""
    # Mock ProviderManager methods
    mock_provider_config = MagicMock()
    mock_provider_config.get_valid_models.return_value = ['model1', 'model2']
    mock_provider_config.valid_models = {
        'model1': 'short1',
        'model2': 'short2'
    }

    command_handler.chat_interface.config.config.providers.get_all_provider_names.return_value = ['test_provider']
    command_handler.chat_interface.config.config.providers.get.return_value = mock_provider_config

    # Test the integration
    result = command_handler.handle_list_command([])

    # Verify ProviderManager integration
    command_handler.chat_interface.config.config.providers.get_all_provider_names.assert_called_once()
    command_handler.chat_interface.config.config.providers.get.assert_called_once_with('test_provider')
    mock_provider_config.get_valid_models.assert_called_once()

    # Verify output
    assert '**TEST_PROVIDER - Available Models:**' in result
    assert '• test_provider/model1 (short1)' in result
    assert '• test_provider/model2 (short2)' in result

def test_handle_list_command_output_formatting(command_handler):
    """Test output formatting for different provider scenarios."""
    # Test case 1: Provider with models that have different short names
    mock_provider1 = MagicMock()
    mock_provider1.get_valid_models.return_value = ['long-model-name-2024', 'simple-model']
    mock_provider1.valid_models = {
        'long-model-name-2024': 'short-name',
        'simple-model': 'simple-model'  # Same as long name
    }

    # Test case 2: Provider with no models configured
    mock_provider2 = MagicMock()
    mock_provider2.get_valid_models.return_value = []
    mock_provider2.valid_models = {}

    command_handler.chat_interface.config.config.providers.get_all_provider_names.return_value = ['provider1', 'provider2']
    command_handler.chat_interface.config.config.providers.get.side_effect = [
        mock_provider1, mock_provider2
    ]

    result = command_handler.handle_list_command([])

    # Verify formatting for different scenarios
    assert '**PROVIDER1 - Available Models:**' in result
    assert '• provider1/long-model-name-2024 (short-name)' in result  # Different short name
    assert '• provider1/simple-model' in result  # Same short name, no parentheses
    assert '**PROVIDER2:**' in result
    assert 'No models configured' in result

def test_handle_list_command_no_providers_configured(command_handler):
    """Test /list command when no providers are configured."""
    # Mock ProviderManager with no providers
    command_handler.chat_interface.config.config.providers.get_all_provider_names.return_value = []

    # Test without providers
    result = command_handler.handle_list_command([])

    # Verify empty result message
    assert result == "No providers configured"

    # Verify ProviderManager was called correctly
    command_handler.chat_interface.config.config.providers.get_all_provider_names.assert_called_once()
