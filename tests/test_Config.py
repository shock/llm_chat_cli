import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import toml
import pytest
from modules.Config import Config, ConfigModel
from pydantic import ValidationError

# Helper function to create a temporary config file
def create_temp_config_file(content):
    with open('temp_config.toml', 'w') as file:
        toml.dump(content, file)
    return 'temp_config.toml'

# Fixture to clean up temporary files after tests
@pytest.fixture
def cleanup_temp_files():
    yield
    if os.path.exists('temp_config.toml'):
        os.remove('temp_config.toml')

def test_load_config_with_valid_file(cleanup_temp_files):
    config_data = {
        "api_key": "test_api_key",
        "model": "test_model",
        "system_prompt": "test_system_prompt",
        "data_directory": "test_data_directory",
        "sassy": True
    }
    config_file = create_temp_config_file(config_data)
    config = Config(config_file)
    assert config.get("api_key") == "test_api_key"
    assert config.get("model") == "test_model"
    assert config.get("system_prompt") == "test_system_prompt"
    assert config.get("data_directory") == "test_data_directory"
    assert config.is_sassy() == True

def test_load_config_with_partial_data(cleanup_temp_files):
    default_config_data = ConfigModel(**{"api_key": "test_api_key"})
    config_data = {
        "api_key": "test_api_key",
        "model": "test_model",
        "system_prompt": "test_system_prompt",
    }
    config_file = create_temp_config_file(config_data)
    config = Config(config_file)
    assert config.get("api_key") == "test_api_key"
    assert config.get("model") == "test_model"
    assert config.get("system_prompt") == "test_system_prompt"
    assert config.get("data_directory") == default_config_data.data_directory
    assert config.is_sassy() == default_config_data.sassy

def test_load_config_with_missing_file(cleanup_temp_files):
    config = Config('non_existent_file.toml', api_key="test_api_key")
    assert config.get("api_key") == "test_api_key"
    assert config.get("model") == "gpt-4o-mini-2024-07-18"
    assert config.get("system_prompt") == "You're name is Lemmy. You are a helpful assistant that answers questions factually based on the provided context."
    assert config.get("data_directory") == "~/.llm_chat_cli"
    assert config.is_sassy() == False

def test_load_config_with_invalid_data(cleanup_temp_files, capsys):
    config_data = {
        "api_key": 12345,  # Invalid type
        "model": "test_model",
        "system_prompt": "test_system_prompt",
        "data_directory": "test_data_directory",
        "sassy": "not_a_boolean"  # Invalid type
    }
    config_file = create_temp_config_file(config_data)
    # assert that ValidationError is raised
    with pytest.raises(ValidationError):
        Config(config_file)

def test_is_sassy_method(cleanup_temp_files):
    config_data = {
        "api_key": "test_api_key",
        "model": "test_model",
        "system_prompt": "test_system_prompt",
        "data_directory": "test_data_directory",
        "sassy": True
    }
    config_file = create_temp_config_file(config_data)
    config = Config(config_file)
    assert config.is_sassy() == True

    config_data["sassy"] = False
    config_file = create_temp_config_file(config_data)
    config = Config(config_file)
    assert config.is_sassy() == False

def test_create_default_config(cleanup_temp_files, monkeypatch):
    config_file = 'temp_config.toml'
    api_key = '<your_api_key_here>'
    config = Config(config_file, api_key=api_key)

    config_attrs = config.config.model_dump()

    assert config_attrs["api_key"] == api_key
    # Test creating a new config file
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    assert config.create_default_config() == True
    assert os.path.exists(config_file)

    # Verify the content of the created file
    with open(config_file, 'r') as f:
        content = f.read()
        assert "# OpenAI API Key" in content
        assert "# OpenAI Model Name" in content
        assert "# System Prompt" in content
        assert "# Data Directory for Session Files" in content
        assert "# Sassy Mode" in content

    toml_attrs = toml.load(config_file)
    for key, value in config_attrs.items():
        assert toml_attrs[key] == value

    # Test overwriting existing file
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    assert config.create_default_config() == True

    # Test not overwriting existing file
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    assert config.create_default_config() == False

def test_create_default_config_force(cleanup_temp_files):
    config_file = 'temp_config.toml'
    api_key = '<your_api_key_here>'
    config = Config(config_file, api_key=api_key)

    # Create initial config
    config.create_default_config()

    # Modify the file
    with open(config_file, 'a') as f:
        f.write("# Modified content")

    # Force overwrite
    assert config.create_default_config(force=True) == True

    # Verify the content is reset to default
    with open(config_file, 'r') as f:
        content = f.read()
        assert "# Modified content" not in content
