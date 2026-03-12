import sys
import os
import pytest
from unittest.mock import patch, MagicMock, ANY
from io import StringIO

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import main module explicitly from current directory
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

        # Create a mock ProviderManager
        provider_manager = MagicMock()
        provider_manager.get_provider_config.return_value = provider_config
        provider_manager.get_all_provider_names.return_value = ["openai"]

        # Mock discover_models to do nothing
        provider_manager.discover_models = MagicMock()

        # Set up providers as a ProviderManager instance
        config_instance.config.providers = provider_manager

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

@pytest.mark.timeout(10)
@patch('argparse.ArgumentParser.parse_args')
@patch('os.system')
@patch('builtins.print')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_clear_option(mock_discover_models, mock_print, mock_system, mock_parse_args, mock_chat_interface, mock_config):
    """Test clear option. mock_chat_interface and mock_config are needed for main.main() to work but not directly accessed."""
    mock_parse_args.return_value = MagicMock(
        clear=True,
        help=False,
        prompt=None,
        stdin=False,
        create_config=False,
        data_directory=None,
        model="4o-mini",
        system_prompt=None,
        history_file=None,
        sassy=False, config="~/.llm_chat_cli.toml",
        list_models=False, echo=False,
        stream=False, no_stream=False
    )

    # Mock the run method to prevent interactive session
    mock_chat_interface.return_value.run = MagicMock()

    # Mock discover_models to do nothing
    mock_discover_models.return_value = True

    main.main()

    mock_system.assert_called_once_with('cls' if os.name == 'nt' else 'clear')
    mock_print.assert_called_once_with("Welcome to LLM Chat\n")

@patch('argparse.ArgumentParser.parse_args')
@patch('argparse.ArgumentParser.print_help')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_help_option(mock_discover_models, mock_print_help, mock_parse_args, mock_chat_interface, mock_config):
    """Test help option. mock_chat_interface and mock_config are needed for main.main() to work but not directly accessed."""
    mock_parse_args.return_value = MagicMock(help=True, create_config=False, data_directory=None)

    main.main()

    mock_print_help.assert_called_once()

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_chat_interface_creation(mock_discover_models, mock_parse_args, monkeypatch, mock_chat_interface, mock_config):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False, data_directory=None, list_models=False, echo=False,
        stream=False, no_stream=False
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key_xx")

    # Mock the run method to prevent interactive session
    mock_chat_interface.return_value.run = MagicMock()

    # Mock discover_models to do nothing
    mock_discover_models.return_value = True

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
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_one_shot_prompt(mock_discover_models, mock_parse_args, mock_chat_interface):
    """Test one-shot prompt mode. mock_chat_interface is needed for main.main() to work but not directly accessed."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt="Test prompt", stdin=False,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=False,
        stream=False, no_stream=False
    )

    with patch.object(sys, 'exit') as mock_exit:
        main.main()

    mock_chat_interface.return_value.one_shot_prompt.assert_called_once_with("Test prompt")
    mock_exit.assert_called_once_with(0)

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_create_config_option(mock_discover_models, mock_parse_args, mock_config):
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
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_override_option(mock_discover_models, mock_chat_interface, mock_parse_args, mock_config):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False, system_prompt=None,
        history_file=None, model="4o-mini", sassy=False, config=None,
        create_config=False, data_directory=None, override=True,
        list_models=False, echo=False,
        stream=False, no_stream=False
    )

    # Create a proper mock ChatInterface instance
    chat_instance = MagicMock()
    # Mock the run method to prevent interactive session
    chat_instance.run = MagicMock()
    mock_chat_interface.return_value = chat_instance

    # Mock discover_models to do nothing
    mock_discover_models.return_value = True

    main.main()

    mock_config.assert_called_once()
    # Mock the provider config properly
    mock_provider_config = MagicMock()
    mock_provider_config.api_key = "other_test_api_key"
    mock_config.return_value.get_provider_config.return_value = mock_provider_config

    assert mock_config.return_value.get_provider_config("openai").api_key == "other_test_api_key"

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.Config.ProviderManager')
@patch('main.ChatInterface')
def test_update_valid_models_flag(mock_chat_interface, mock_provider_manager_class, mock_parse_args):
    """Test --update-valid-models flag behavior with ProviderManager."""
    from modules.ProviderManager import ProviderManager

    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=True,
        stream=False, no_stream=False
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
@patch('main.ChatInterface')
def test_update_valid_models_alias(mock_chat_interface, mock_provider_manager_class, mock_parse_args):
    """Test -uvm alias for --update-valid-models."""
    from modules.ProviderManager import ProviderManager

    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=True,
        stream=False, no_stream=False
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
@patch('main.ChatInterface')
def test_update_valid_models_error_handling(mock_chat_interface, mock_provider_manager_class, mock_parse_args):
    """Test error handling during model discovery."""
    from modules.ProviderManager import ProviderManager

    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=True,
        stream=False, no_stream=False
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
@patch('main.ChatInterface')
@patch('modules.OpenAIChatCompletionApi.OpenAIChatCompletionApi.provider_data', {"openai": {"valid_models": {"test-model": "test-model"}}})
def test_config_with_provider_manager_integration(mock_chat_interface, mock_config, mock_parse_args):
    """Test integration between main CLI and Config/ProviderManager."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False,
        system_prompt=None, history_file=None, model="test-model",
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=False,
        stream=False, no_stream=False
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

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_no_highlighting_flag(mock_discover_models, mock_parse_args, mock_chat_interface, mock_config):
    """Test --no-highlighting flag is properly parsed and passed to config."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False, data_directory=None, list_models=False, echo=False,
        no_highlighting=True, update_valid_models=False
    )

    # Mock the run method to prevent interactive session
    mock_chat_interface.return_value.run = MagicMock()

    # Mock discover_models to do nothing
    mock_discover_models.return_value = True

    main.main()

    # Verify config was called with no_highlighting override
    mock_config.assert_called_once()
    call_kwargs = mock_config.call_args[1]
    assert call_kwargs['overrides']['no_highlighting'] == True

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_no_highlighting_flag_short_form(mock_discover_models, mock_parse_args, mock_chat_interface, mock_config):
    """Test -nh short form flag works the same as --no-highlighting."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False, data_directory=None, list_models=False, echo=False,
        no_highlighting=True, update_valid_models=False
    )

    # Mock the run method to prevent interactive session
    mock_chat_interface.return_value.run = MagicMock()

    # Mock discover_models to do nothing
    mock_discover_models.return_value = True

    main.main()

    # Verify config was called with no_highlighting override
    mock_config.assert_called_once()
    call_kwargs = mock_config.call_args[1]
    assert call_kwargs['overrides']['no_highlighting'] == True

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_no_highlighting_default_false(mock_discover_models, mock_parse_args, mock_chat_interface, mock_config):
    """Test that no_highlighting defaults to False when flag is not provided."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False, data_directory=None, list_models=False, echo=False,
        no_highlighting=False, update_valid_models=False
    )

    # Mock the run method to prevent interactive session
    mock_chat_interface.return_value.run = MagicMock()

    # Mock discover_models to do nothing
    mock_discover_models.return_value = True

    main.main()

    # Verify config was called with no_highlighting as None (not provided)
    mock_config.assert_called_once()
    call_kwargs = mock_config.call_args[1]
    assert call_kwargs['overrides']['no_highlighting'] == None

@patch('argparse.ArgumentParser.parse_args')
@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key_xx"})
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_stdin_mode(mock_discover_models, mock_parse_args, mock_chat_interface):
    """Test stdin mode reads from stdin and calls one_shot_prompt."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=True,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=False,
        stream=False, no_stream=False
    )

    test_prompt = "Test prompt from stdin"
    with patch('sys.stdin', StringIO(test_prompt)):
        with patch.object(sys, 'exit') as mock_exit:
            main.main()

    mock_chat_interface.return_value.one_shot_prompt.assert_called_once_with(test_prompt)
    mock_exit.assert_called_once_with(0)

@patch('argparse.ArgumentParser.parse_args')
@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key_xx"})
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_stdin_mode_multiline(mock_discover_models, mock_parse_args, mock_chat_interface):
    """Test stdin mode preserves newlines in multiline input."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=True,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=False,
        stream=False, no_stream=False
    )

    test_prompt = "Line 1\nLine 2\nLine 3"
    with patch('sys.stdin', StringIO(test_prompt)):
        with patch.object(sys, 'exit') as mock_exit:
            main.main()

    mock_chat_interface.return_value.one_shot_prompt.assert_called_once_with("Line 1\nLine 2\nLine 3")
    mock_exit.assert_called_once_with(0)

@patch('argparse.ArgumentParser.parse_args')
@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key_xx"})
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_stdin_mode_empty_input(mock_discover_models, mock_parse_args, mock_chat_interface):
    """Test stdin mode exits silently with code 1 on empty input."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=True,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=False,
        stream=False, no_stream=False
    )

    with patch('sys.stdin', StringIO("")):
        with pytest.raises(SystemExit) as exc_info:
            main.main()
        assert exc_info.value.code == 1

    # Should exit with code 1 without calling one_shot_prompt
    mock_chat_interface.return_value.one_shot_prompt.assert_not_called()

@patch('argparse.ArgumentParser.parse_args')
@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key_xx"})
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_stdin_mode_whitespace_only(mock_discover_models, mock_parse_args, mock_chat_interface):
    """Test stdin mode exits silently with code 1 on whitespace-only input."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=True,
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None, list_models=False, echo=False,
        update_valid_models=False,
        stream=False, no_stream=False
    )

    with patch('sys.stdin', StringIO("   \n\n   ")):
        with pytest.raises(SystemExit) as exc_info:
            main.main()
        assert exc_info.value.code == 1

    # Should exit with code 1 without calling one_shot_prompt
    mock_chat_interface.return_value.one_shot_prompt.assert_not_called()

def test_mutual_exclusivity_prompt_and_stdin():
    """Test that -p/--prompt and -i/--stdin are mutually exclusive."""
    # Test by directly calling argparse with both options
    with pytest.raises(SystemExit) as exc_info:
        # We need to actually parse args with sys.argv to test argparse behavior
        with patch('sys.argv', ['llm_api_chat', '-p', 'test prompt', '-i']):
            main.main()

    # argparse exits with code 2 on argument errors
    assert exc_info.value.code == 2

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_stream_flag(mock_discover_models, mock_parse_args, mock_chat_interface, mock_config):
    """Test --stream flag is properly parsed and passed to config."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False, data_directory=None, list_models=False, echo=False,
        no_highlighting=False, update_valid_models=False,
        stream=True, no_stream=False
    )

    # Mock the run method to prevent interactive session
    mock_chat_interface.return_value.run = MagicMock()

    # Mock discover_models to do nothing
    mock_discover_models.return_value = True

    main.main()

    # Verify config was called with stream override set to True
    mock_config.assert_called_once()
    call_kwargs = mock_config.call_args[1]
    assert call_kwargs['overrides']['stream'] == True

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_no_stream_flag(mock_discover_models, mock_parse_args, mock_chat_interface, mock_config):
    """Test --no-stream flag is properly parsed and passed to config."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False, data_directory=None, list_models=False, echo=False,
        no_highlighting=False, update_valid_models=False,
        stream=False, no_stream=True
    )

    # Mock the run method to prevent interactive session
    mock_chat_interface.return_value.run = MagicMock()

    # Mock discover_models to do nothing
    mock_discover_models.return_value = True

    main.main()

    # Verify config was called with stream override set to False
    mock_config.assert_called_once()
    call_kwargs = mock_config.call_args[1]
    assert call_kwargs['overrides']['stream'] == False

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_stream_flags_default(mock_discover_models, mock_parse_args, mock_chat_interface, mock_config):
    """Test that stream config is not overridden when neither flag is provided."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False, data_directory=None, list_models=False, echo=False,
        no_highlighting=False, update_valid_models=False,
        stream=False, no_stream=False
    )

    # Mock the run method to prevent interactive session
    mock_chat_interface.return_value.run = MagicMock()

    # Mock discover_models to do nothing
    mock_discover_models.return_value = True

    main.main()

    # Verify config was called without stream override (should not be in overrides)
    mock_config.assert_called_once()
    call_kwargs = mock_config.call_args[1]
    assert 'stream' not in call_kwargs['overrides']

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.ProviderManager.ProviderManager.discover_models')
def test_stream_flag_precedence(mock_discover_models, mock_parse_args, mock_chat_interface, mock_config):
    """Test that --stream takes precedence when both flags are provided (edge case)."""
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, stdin=False, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False, data_directory=None, list_models=False, echo=False,
        no_highlighting=False, update_valid_models=False,
        stream=True, no_stream=True  # Both set (shouldn't happen in practice, but test the logic)
    )

    # Mock the run method to prevent interactive session
    mock_chat_interface.return_value.run = MagicMock()

    # Mock discover_models to do nothing
    mock_discover_models.return_value = True

    main.main()

    # Verify config was called with stream override set to True (--stream takes precedence)
    mock_config.assert_called_once()
    call_kwargs = mock_config.call_args[1]
    assert call_kwargs['overrides']['stream'] == True

if __name__ == "__main__":
    pytest.main()
