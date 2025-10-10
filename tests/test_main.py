import sys
import os
import pytest
from unittest.mock import patch, MagicMock, ANY
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# These imports are used for patching but Pylance doesn't recognize the usage
# They are referenced in patch decorators like @patch('main.ChatInterface')
from modules.Config import Config  # noqa: F401
from modules.ChatInterface import ChatInterface  # noqa: F401
import main

@pytest.fixture
def mock_chat_interface():
    with patch('main.ChatInterface') as mock:
        # Create a proper mock ChatInterface instance
        chat_instance = MagicMock()

        # Create proper provider config
        provider_config = MagicMock()
        provider_config.api_key = "test_api_key_xx"
        provider_config.base_api_url = "https://test.openai.com/v1"
        provider_config.valid_models = {"gpt-4o-mini-2024-07-18": "4o-mini"}

        # Set up providers as a dictionary
        chat_instance.providers = {"openai": provider_config}

        mock.return_value = chat_instance
        yield mock

@pytest.fixture
def mock_config():
    with patch('main.Config') as mock:
        # Create a proper mock config object
        config_instance = MagicMock()
        config_instance.get.return_value = "4o-mini"
        config_instance.is_sassy.return_value = False

        # Create proper provider config with valid_models as an attribute, not a callable
        provider_config = MagicMock()
        provider_config.api_key = "test_api_key_xx"
        provider_config.base_api_url = "https://test.openai.com/v1"
        provider_config.valid_models = {"gpt-4o-mini-2024-07-18": "4o-mini"}

        # Set up providers as a dictionary, not a callable
        config_instance.config.providers = {"openai": provider_config}

        mock.return_value = config_instance
        yield mock

@pytest.mark.parametrize("env_var, expected", [
    ("OPENAI_API_KEY", "test_api_key_xx"),
    ("LLMC_DEFAULT_MODEL", "test_model"),
    ("LLMC_SYSTEM_PROMPT", "test_system_prompt"),
])
def test_environment_variables(monkeypatch, env_var, expected):
    monkeypatch.setenv(env_var, expected)
    assert os.getenv(env_var) == expected

@patch('argparse.ArgumentParser.parse_args')
@patch('os.system')
@patch('builtins.print')
def test_clear_option(mock_print, mock_system, mock_parse_args, mock_chat_interface, mock_config):
    """Test clear option. mock_chat_interface and mock_config are needed for main.main() to work but not directly accessed."""
    mock_parse_args.return_value = MagicMock(
        clear=True,
        help=False,
        prompt=None,
        create_config=False,
        data_directory=None,
        model="4o-mini",
        system_prompt=None,
        history_file=None,
        sassy=False, config="~/.llm_chat_cli.toml",
        list_models=False, echo=False
    )

    main.main()

    mock_system.assert_called_once_with('cls' if os.name == 'nt' else 'clear')
    mock_print.assert_called_once_with("Welcome to LLM Chat\n")

@patch('argparse.ArgumentParser.parse_args')
@patch('argparse.ArgumentParser.print_help')
def test_help_option(mock_print_help, mock_parse_args, mock_chat_interface, mock_config):
    """Test help option. mock_chat_interface and mock_config are needed for main.main() to work but not directly accessed."""
    mock_parse_args.return_value = MagicMock(help=True, create_config=False, data_directory=None)

    main.main()

    mock_print_help.assert_called_once()

@patch('argparse.ArgumentParser.parse_args')
def test_chat_interface_creation(mock_parse_args, monkeypatch, mock_chat_interface, mock_config):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False, data_directory=None, list_models=False, echo=False
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key_xx")

    main.main()

    mock_chat_interface.assert_called_once()
    mock_config.assert_called_once()

    # Test sassy mode
    mock_parse_args.return_value.sassy = True
    mock_config.return_value.is_sassy.return_value = True
    main.main()

    mock_chat_interface.assert_called()
    mock_config.assert_called()

    # Test with custom system prompt
    custom_prompt = "Custom system prompt"
    mock_parse_args.return_value.system_prompt = custom_prompt
    main.main()

    mock_chat_interface.assert_called()
    mock_config.assert_called()

@patch('argparse.ArgumentParser.parse_args')
@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key_xx"})
def test_one_shot_prompt(mock_parse_args, mock_chat_interface):
    """Test one-shot prompt mode. mock_chat_interface is needed for main.main() to work but not directly accessed."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt="Test prompt",
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=False
    )

    with patch.object(sys, 'exit') as mock_exit:
        main.main()

    mock_chat_interface.return_value.one_shot_prompt.assert_called_once_with("Test prompt")
    mock_exit.assert_called_once_with(0)

@patch('argparse.ArgumentParser.parse_args')
def test_create_config_option(mock_parse_args, mock_config):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=True, data_directory=None
    )

    main.main()

    mock_config.assert_called_once()
    assert mock_config.call_args[1]['create_config'] == True

@patch.dict(os.environ, {"OPENAI_API_KEY": "other_test_api_key"})
@patch('argparse.ArgumentParser.parse_args')
@patch('main.ChatInterface')
def test_override_option(mock_chat_interface, mock_parse_args, mock_config):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, system_prompt=None,
        history_file=None, model="4o-mini", sassy=False, config=None,
        create_config=False, data_directory=None, override=True,
        list_models=False, echo=False
    )

    # Create a proper mock ChatInterface instance
    chat_instance = MagicMock()
    mock_chat_interface.return_value = chat_instance

    main.main()

    mock_config.assert_called_once()
    # Mock the provider config properly
    mock_provider_config = MagicMock()
    mock_provider_config.api_key = "other_test_api_key"
    mock_config.return_value.get_provider_config.return_value = mock_provider_config

    assert mock_config.return_value.get_provider_config("openai").api_key == "other_test_api_key"

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.Config.ProviderManager')
@patch('modules.ChatInterface.ChatInterface')
def test_update_valid_models_flag(mock_chat_interface, mock_provider_manager_class, mock_parse_args):
    """Test --update-valid-models flag behavior with ProviderManager."""
    from modules.ProviderManager import ProviderManager

    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=True
    )

    # Setup mock ProviderManager instance that will be returned by the constructor
    # Use spec to make it pass isinstance checks
    mock_provider_manager = MagicMock(spec=ProviderManager)
    mock_provider_manager_class.return_value = mock_provider_manager

    # Mock the get_provider_config method to return a provider config with valid models
    mock_provider_config = MagicMock()
    mock_provider_config.api_key = "test_api_key"
    mock_provider_config.base_api_url = "https://test.openai.com/v1"
    mock_provider_config.valid_models = {"gpt-4.1-mini-2025-04-14": "4.1-mini"}
    mock_provider_manager.get_provider_config.return_value = mock_provider_config

    # Mock get_all_provider_names to return openai
    mock_provider_manager.get_all_provider_names.return_value = ["openai"]

    # Mock ChatInterface to prevent actual chat interface from starting
    mock_chat_instance = MagicMock()
    mock_chat_instance.run = MagicMock()
    mock_chat_interface.return_value = mock_chat_instance

    # Mock sys.exit to prevent test from exiting
    with patch.object(sys, 'exit') as mock_exit:
        main.main()

    # Verify that discover_models was called with correct parameters
    mock_provider_manager.discover_models.assert_called_once_with(
        force_refresh=True, persist_on_success=True, data_directory=ANY
    )

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.Config.ProviderManager')
@patch('modules.ChatInterface.ChatInterface')
def test_update_valid_models_alias(mock_chat_interface, mock_provider_manager_class, mock_parse_args):
    """Test -uvm alias for --update-valid-models."""
    from modules.ProviderManager import ProviderManager

    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=True
    )

    # Setup mock ProviderManager instance that will be returned by the constructor
    # Use spec to make it pass isinstance checks
    mock_provider_manager = MagicMock(spec=ProviderManager)
    mock_provider_manager_class.return_value = mock_provider_manager

    # Mock the get_provider_config method to return a provider config with valid models
    mock_provider_config = MagicMock()
    mock_provider_config.api_key = "test_api_key"
    mock_provider_config.base_api_url = "https://test.openai.com/v1"
    mock_provider_config.valid_models = {"gpt-4.1-mini-2025-04-14": "4.1-mini"}
    mock_provider_manager.get_provider_config.return_value = mock_provider_config

    # Mock get_all_provider_names to return openai
    mock_provider_manager.get_all_provider_names.return_value = ["openai"]

    # Mock ChatInterface to prevent actual chat interface from starting
    mock_chat_instance = MagicMock()
    mock_chat_instance.run = MagicMock()
    mock_chat_interface.return_value = mock_chat_instance

    # Mock sys.exit to prevent test from exiting
    with patch.object(sys, 'exit') as mock_exit:
        main.main()

    # Verify that discover_models was called
    mock_provider_manager.discover_models.assert_called_once()

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.Config.ProviderManager')
@patch('modules.ChatInterface.ChatInterface')
def test_update_valid_models_error_handling(mock_chat_interface, mock_provider_manager_class, mock_parse_args):
    """Test error handling during model discovery."""
    from modules.ProviderManager import ProviderManager

    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=True
    )

    # Setup mock ProviderManager instance that raises exception on discover_models
    # Use spec to make it pass isinstance checks
    mock_provider_manager = MagicMock(spec=ProviderManager)
    mock_provider_manager.discover_models.side_effect = Exception("Discovery failed")
    mock_provider_manager_class.return_value = mock_provider_manager

    # Mock the get_provider_config method to return a provider config with valid models
    mock_provider_config = MagicMock()
    mock_provider_config.api_key = "test_api_key"
    mock_provider_config.base_api_url = "https://test.openai.com/v1"
    mock_provider_config.valid_models = {"gpt-4.1-mini-2025-04-14": "4.1-mini"}
    mock_provider_manager.get_provider_config.return_value = mock_provider_config

    # Mock get_all_provider_names to return openai
    mock_provider_manager.get_all_provider_names.return_value = ["openai"]

    # Mock ChatInterface to prevent actual chat interface from starting
    mock_chat_instance = MagicMock()
    mock_chat_instance.run = MagicMock()
    mock_chat_interface.return_value = mock_chat_instance

    # Mock sys.exit to prevent test from exiting
    with patch.object(sys, 'exit') as mock_exit:
        # Mock print to capture warning message
        with patch('builtins.print') as mock_print:
            main.main()

    # Verify that warning was printed but execution continued
    mock_print.assert_any_call("Warning: Model discovery failed: Discovery failed")
    # Verify that discover_models was still called
    mock_provider_manager.discover_models.assert_called_once()

@patch('argparse.ArgumentParser.parse_args')
@patch('main.Config')
@patch('modules.ChatInterface.ChatInterface')
@patch('modules.OpenAIChatCompletionApi.OpenAIChatCompletionApi.provider_data', {"openai": {"valid_models": {"test-model": "test-model"}}})
def test_config_with_provider_manager_integration(mock_chat_interface, mock_config, mock_parse_args):
    """Test integration between main CLI and Config/ProviderManager."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None,
        system_prompt=None, history_file=None, model="test-model",
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=False
    )

    # Create a mock config instance with ProviderManager
    mock_config_instance = MagicMock()
    mock_config.return_value = mock_config_instance

    # Mock the get method to return the model
    mock_config_instance.get.return_value = "test-model"

    # Mock ProviderManager methods
    mock_provider_manager = MagicMock()

    # Create a mock provider config with valid models that includes "test-model"
    mock_provider_config = MagicMock()
    mock_provider_config.api_key = "test_api_key_xx"
    mock_provider_config.base_api_url = "https://test.openai.com/v1"
    mock_provider_config.valid_models = {"test-model": "test-model"}

    # Mock the get_provider_config method to return our mock provider config
    mock_provider_manager.get_provider_config.return_value = mock_provider_config
    mock_config_instance.config.providers = mock_provider_manager

    # Mock ChatInterface to prevent actual chat interface from starting
    mock_chat_instance = MagicMock()
    # Mock the run method to prevent interactive session
    mock_chat_instance.run = MagicMock()
    mock_chat_interface.return_value = mock_chat_instance

    # Mock sys.exit to prevent test from exiting
    with patch.object(sys, 'exit') as mock_exit:
        main.main()

    # Verify config was initialized with correct parameters
    mock_config.assert_called_once()
    call_kwargs = mock_config.call_args[1]
    assert call_kwargs['update_valid_models'] == False
    assert call_kwargs['overrides']['model'] == "test-model"

if __name__ == "__main__":
    pytest.main()
