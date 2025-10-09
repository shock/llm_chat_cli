import shutil
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import toml
import pytest
from modules.Config import Config
from modules.Types import ConfigModel, DEFAULT_SYSTEM_PROMPT, SASSY_SYSTEM_PROMPT, DEFAULT_MODEL
from unittest.mock import patch, mock_open
from pydantic import ValidationError
from modules.Types import DEFAULT_MODEL

@pytest.fixture(autouse=True)
def setup_teardown():
    # Code to run before each test
    key = f"{"openai".upper()}_API_KEY"
    save_key = None
    if key in os.environ:
        save_key = os.environ[key]
        del os.environ[key]
    yield
    # Code to run after each test
    if save_key:
        os.environ[key] = save_key

@pytest.fixture
def tmp_dir():
    return os.path.join(os.getenv('TMPDIR', '/tmp'), 'test_llmc_config')

# Helper function to create a temporary config file
def create_temp_config_file(content, filename='config.toml'):
    tmp_dir = os.path.join(os.getenv('TMPDIR', '/tmp'), 'test_llmc_config')
    os.makedirs(tmp_dir, exist_ok=True)
    config_file = os.path.join(tmp_dir, filename)
    with open(config_file, 'w') as file:
        toml.dump(content, file)
    return config_file

def remove_tmp_dir():
    tmp_dir = os.path.join(os.getenv('TMPDIR', '/tmp'), 'test_llmc_config')
    if os.path.exists(tmp_dir) and os.path.isdir(tmp_dir):
        print(f"Cleaning up temporary files in {tmp_dir}")
        shutil.rmtree(tmp_dir)

# Fixture to clean up temporary files after tests
@pytest.fixture
def cleanup_temp_files(tmp_dir):
    yield
    remove_tmp_dir()

def test_load_config_with_valid_file(cleanup_temp_files):
    config_data = {
        "model": "test_model",
        "system_prompt": "test_system_prompt",
        "sassy": False,
        "providers": {
            "openai": {
                "api_key": "test_api_key1",
                "base_api_url": "https://api.openai.com/v2"
            }
        }
    }
    config_file = create_temp_config_file(config_data)
    data_directory = os.path.dirname(config_file)
    config = Config(data_directory=data_directory)
    # assert config.get_provider_config("openai").api_key == "test_api_key1"
    assert config.get("model") == "test_model"
    assert config.get_provider_config("openai").base_api_url == "https://api.openai.com/v2"
    assert config.get("system_prompt") == "test_system_prompt"
    assert config.is_sassy() == False

def test_load_config_with_partial_data(cleanup_temp_files):
    config_data = {
        "model": "test_model",
        "system_prompt": "test_system_prompt",
        "providers": {
            "openai": {
                "api_key": "test_api_key",
                "base_api_url": "https://test.openai.com/v1"
            }
        }
    }
    config_file = create_temp_config_file(config_data)
    data_directory = os.path.dirname(config_file)
    config = Config(data_directory=data_directory)
    assert config.get_provider_config("openai").api_key == "test_api_key"
    assert config.get("model") == "test_model"
    assert config.get("system_prompt") == "test_system_prompt"
    assert config.get_provider_config("openai").base_api_url == "https://test.openai.com/v1"
    assert config.is_sassy() == False

def test_load_config_with_missing_file(cleanup_temp_files):
    config_file = create_temp_config_file({}, filename='not-config.toml')
    data_directory = os.path.dirname(config_file)
    config = Config(data_directory=data_directory)
    assert config.get_provider_config("openai").api_key == 'not-configured'
    assert config.get("model") == DEFAULT_MODEL
    assert config.get("system_prompt") == DEFAULT_SYSTEM_PROMPT
    assert config.get_provider_config("openai").base_api_url == "https://api.openai.com/v1"
    assert config.is_sassy() == False

def test_load_config_with_missing_file_and_os_env_set(cleanup_temp_files):
    config_file = create_temp_config_file({}, filename='not-config.toml')
    data_directory = os.path.dirname(config_file)
    key = f"{"openai".upper()}_API_KEY"
    save_key = None
    if key in os.environ:
        save_key = os.environ[key]
        del os.environ[key]
    os.environ[key] = 'test_api_key_xx'

    config = Config(data_directory=data_directory)
    assert config.get_provider_config("openai").api_key == 'test_api_key_xx'
    assert config.get("model") == DEFAULT_MODEL
    assert config.get("system_prompt") == DEFAULT_SYSTEM_PROMPT
    assert config.get_provider_config("openai").base_api_url == "https://api.openai.com/v1"
    assert config.is_sassy() == False
    del os.environ[key]
    if save_key:
        os.environ[key] = save_key

def test_load_config_with_missing_directory(cleanup_temp_files):
    # Should not raise an exception anymore - should handle gracefully
    config = Config(data_directory='non_existent_directory')
    # Verify that we can still get provider config even with missing directory
    assert config.get_provider_config("openai").api_key == 'not-configured'
    assert config.get("model") == DEFAULT_MODEL

def test_load_config_with_invalid_data(cleanup_temp_files, capsys):
    config_data = {
        "model": "test_model",
        "system_prompt": "test_system_prompt",
        "sassy": "not_a_boolean"  # Invalid type
    }
    config_file = create_temp_config_file(config_data)
    data_directory = os.path.dirname(config_file)
    # assert that ValidationError is raised
    with pytest.raises(ValidationError):
        Config(data_directory=data_directory)

def test_is_sassy_method(cleanup_temp_files):
    config_data = {
        "model": "test_model",
        "system_prompt": "test_system_prompt",
        "sassy": True
    }
    config_file = create_temp_config_file(config_data)
    data_directory = os.path.dirname(config_file)
    config = Config(data_directory=data_directory)
    assert config.is_sassy() == True

    config_data["sassy"] = False
    config_file = create_temp_config_file(config_data)
    config = Config(config_file)
    assert config.is_sassy() == False

def test_create_default_config(cleanup_temp_files, monkeypatch):
    non_config_file = create_temp_config_file({}, filename='not-config.toml')
    data_directory = os.path.dirname(non_config_file)
    config = Config(data_directory=data_directory, create_config=True)
    config_file = os.path.join(data_directory, "config.toml")

    config_attrs = config.config.model_dump()
    assert config_attrs["providers"]["openai"]["api_key"] == "not-configured"
    # Test creating a new config file
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    assert os.path.exists(config_file)

    # Verify the content of the created file
    with open(config_file, 'r') as f:
        content = f.read()
        assert "# Model Name" in content
        assert "# Default System Prompt" in content
        assert "# Sassy Mode" in content

    toml_attrs = toml.load(config_file)
    for key, value in config_attrs.items():
        assert toml_attrs[key] == value

@pytest.fixture
def mock_config_file():
    config_content = """
    model = "test-model"
    system_prompt = "Test system prompt"
    data_directory = "~/.test_llm_chat_cli"
    sassy = false
    stream = false

    [providers.openai]
    api_key = "test_api_key"
    base_api_url = "https://test.openai.com/v1"
    """
    return config_content

@pytest.fixture
def sassy_config_file():
    config_content = """
    model = "test-model"
    system_prompt = "SASSY_SYSTEM_PROMPT"
    data_directory = "~/.test_llm_chat_cli"
    sassy = true
    stream = false

    [providers.openai]
    api_key = "test_api_key"
    base_api_url = "https://test.openai.com/v1"
    """
    return config_content

def test_config_initialization_with_no_directory(tmp_dir, cleanup_temp_files):
    dd = os.path.expanduser(f"{tmp_dir}/.test_llm_chat_cli")
    config = Config(data_directory=dd, create_config=True)
    assert config.data_directory == dd
    assert config.config_file == os.path.join(dd, "config.toml")

def test_config_load(tmp_dir, mock_config_file):
    with patch("builtins.open", mock_open(read_data=mock_config_file)):
        with patch("os.path.exists", return_value=[True, False]):
            config = Config(data_directory=tmp_dir)
            assert config.config.providers["openai"].api_key == "test_api_key"
            assert config.config.providers["openai"].base_api_url == "https://test.openai.com/v1"
            assert config.config.model == "test-model"
            assert config.config.system_prompt == "Test system prompt"
            assert config.config.sassy == False
            assert config.config.stream == False

def test_sassy_config_load(tmp_dir, sassy_config_file):
    with patch("builtins.open", mock_open(read_data=sassy_config_file)):
        with patch("os.path.exists", return_value=[True, False]):
            config = Config(data_directory=tmp_dir)
            assert config.config.providers["openai"].api_key == "test_api_key"
            assert config.config.providers["openai"].base_api_url == "https://test.openai.com/v1"
            assert config.config.model == "test-model"
            # assert config.config.sassy == True
            assert config.config.system_prompt == SASSY_SYSTEM_PROMPT
            assert config.config.stream == False

def test_config_create_default(tmp_dir, cleanup_temp_files):
    with patch("builtins.open", mock_open()) as mock_file:
        config = Config(data_directory=f"{tmp_dir}/.test_llm_chat_cli", create_config=True)
        write_call_args = mock_file().write.call_args_list
        assert any("api_key" in str(args) for args in write_call_args)
        assert any("base_api_url" in str(args) for args in write_call_args)
        assert any("model" in str(args) for args in write_call_args)
        assert any("system_prompt" in str(args) for args in write_call_args)
        assert any("sassy" in str(args) for args in write_call_args)
        assert any("stream" in str(args) for args in write_call_args)
