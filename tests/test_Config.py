import shutil
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import toml
import pytest
from modules.Config import Config, ConfigModel, DEFAULT_SYSTEM_PROMPT, SASSY_SYSTEM_PROMPT
from unittest.mock import patch, mock_open
from pydantic import ValidationError
from modules.OpenAIChatCompletionApi import DEFAULT_MODEL

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

# Fixture to clean up temporary files after tests
@pytest.fixture
def cleanup_temp_files(tmp_dir):
    yield
    if os.path.exists(tmp_dir) and os.path.isdir(tmp_dir):
        print(f"Cleaning up temporary files in {tmp_dir}", file=sys.stderr)
        shutil.rmtree(tmp_dir)

def test_load_config_with_missing_file(cleanup_temp_files):
    config_file = create_temp_config_file({}, filename='not-config.toml')
    data_directory = os.path.dirname(config_file)
    config = Config(data_directory=data_directory)
    assert config.get_provider_config("openai").api_key == ''
    assert config.get("model") == DEFAULT_MODEL
    assert config.get("system_prompt") == DEFAULT_SYSTEM_PROMPT
    assert config.get_provider_config("openai").base_api_url == "https://api.openai.com/v1"
    assert config.is_sassy() == False
