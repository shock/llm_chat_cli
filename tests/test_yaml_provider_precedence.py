"""
Test that provider YAML config takes precedence over built-in PROVIDER_DATA.

Verifies that when openaicompat-providers.yaml defines valid_models for a provider,
those models replace (not merge with) the built-in defaults from Types.PROVIDER_DATA.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import shutil
import yaml
import pytest
from modules.Config import Config
from modules.Types import PROVIDER_DATA


@pytest.fixture
def tmp_dir():
    return os.path.join(os.getenv('TMPDIR', '/tmp'), 'test_llmc_yaml_precedence')


@pytest.fixture(autouse=True)
def cleanup(tmp_dir):
    os.makedirs(tmp_dir, exist_ok=True)
    yield
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


@pytest.fixture(autouse=True)
def clear_provider_env_keys():
    """Remove all provider API key env vars so they don't interfere."""
    saved = {}
    for provider_name in PROVIDER_DATA.keys():
        key = f"{provider_name.upper()}_API_KEY"
        if key in os.environ:
            saved[key] = os.environ[key]
            del os.environ[key]
    yield
    for key, val in saved.items():
        os.environ[key] = val


def _write_yaml_provider_config(tmp_dir, providers_yaml):
    """Write an openaicompat-providers.yaml into the temp data directory.

    Uses the correct schema with top-level 'providers' key.
    """
    yaml_path = os.path.join(tmp_dir, 'openaicompat-providers.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump({"providers": providers_yaml}, f, default_flow_style=False, sort_keys=False)
    return yaml_path


def test_yaml_valid_models_replaces_builtin(tmp_dir):
    """
    When YAML defines valid_models for deepseek, those models should
    completely replace (not merge with) the built-in PROVIDER_DATA models.
    """
    providers_yaml = {
        "deepseek": {
            "name": "DeepSeek",
            "api_key": "test-ds-key",
            "base_api_url": "https://api.deepseek.com/v1",
            "valid_models": {
                "deepseek-v4-flash": "ds-flash",
                "deepseek-v4-pro": "ds-pro",
            }
        }
    }
    _write_yaml_provider_config(tmp_dir, providers_yaml)

    config = Config(data_directory=tmp_dir)
    deepseek = config.config.providers.get_provider_config("deepseek")

    # The YAML models should be the ONLY models — no deepseek-chat from PROVIDER_DATA
    assert "deepseek-v4-flash" in deepseek.valid_models
    assert "deepseek-v4-pro" in deepseek.valid_models
    assert "deepseek-chat" not in deepseek.valid_models, \
        "YAML valid_models should replace, not merge with, built-in PROVIDER_DATA"
    assert "deepseek-reasoner" not in deepseek.valid_models, \
        "YAML valid_models should replace, not merge with, built-in PROVIDER_DATA"


def test_yaml_valid_models_appear_in_scoped_models(tmp_dir):
    """
    The valid_scoped_models list (used by tab completion) should show YAML models,
    not built-in PROVIDER_DATA models.
    """
    providers_yaml = {
        "deepseek": {
            "name": "DeepSeek",
            "api_key": "test-ds-key",
            "base_api_url": "https://api.deepseek.com/v1",
            "valid_models": {
                "deepseek-v4-flash": "ds-flash",
                "deepseek-v4-pro": "ds-pro",
            }
        }
    }
    _write_yaml_provider_config(tmp_dir, providers_yaml)

    config = Config(data_directory=tmp_dir)
    scoped_models = config.config.providers.valid_scoped_models()

    deepseek_models = [m for m in scoped_models if m.startswith("deepseek/")]

    assert any("deepseek-v4-flash" in m for m in deepseek_models), \
        f"deepseek-v4-flash should appear in scoped models, got: {deepseek_models}"
    assert not any("deepseek-chat" in m for m in deepseek_models), \
        f"deepseek-chat from PROVIDER_DATA should NOT appear, got: {deepseek_models}"


def test_yaml_partial_override_only_affects_specified_provider(tmp_dir):
    """
    If YAML only overrides deepseek, other providers should keep their
    built-in PROVIDER_DATA models.
    """
    providers_yaml = {
        "deepseek": {
            "name": "DeepSeek",
            "api_key": "test-ds-key",
            "base_api_url": "https://api.deepseek.com/v1",
            "valid_models": {
                "deepseek-v4-flash": "ds-flash",
            }
        }
    }
    _write_yaml_provider_config(tmp_dir, providers_yaml)

    config = Config(data_directory=tmp_dir)

    # DeepSeek should have only the YAML model
    deepseek = config.config.providers.get_provider_config("deepseek")
    assert "deepseek-v4-flash" in deepseek.valid_models
    assert "deepseek-chat" not in deepseek.valid_models

    # OpenAI should still have built-in models
    openai = config.config.providers.get_provider_config("openai")
    assert "gpt-4o-2024-08-06" in openai.valid_models
