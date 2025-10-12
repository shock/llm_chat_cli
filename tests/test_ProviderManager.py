import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import tempfile
import yaml
from unittest.mock import MagicMock, patch, mock_open
from modules.ProviderManager import ProviderManager
from modules.ProviderConfig import ProviderConfig


# Test Fixtures

@pytest.fixture
def sample_provider_configs():
    """Create sample provider configurations for testing."""
    return {
        "openai": {
            "name": "OpenAI",
            "base_api_url": "https://api.openai.com/v1",
            "api_key": "sk-test-openai-key",
            "valid_models": {
                "gpt-4o": "gpt4o",
                "gpt-4o-mini": "gpt4o-mini",
                "gpt-3.5-turbo": "gpt35"
            },
            "invalid_models": ["gpt-4-vision", "old-model"]
        },
        "anthropic": {
            "name": "Anthropic",
            "base_api_url": "https://api.anthropic.com/v1",
            "api_key": "sk-ant-test-key",
            "valid_models": {
                "claude-3-opus-20240229": "opus",
                "claude-3-sonnet-20240229": "sonnet"
            },
            "invalid_models": ["claude-1"]
        },
        "groq": {
            "name": "Groq",
            "base_api_url": "https://api.groq.com/openai/v1",
            "api_key": "gsk-test-key",
            "valid_models": {
                "llama-3.1-70b-versatile": "llama70b",
                "mixtral-8x7b-32768": "mixtral"
            },
            "invalid_models": []
        }
    }


@pytest.fixture
def provider_manager(sample_provider_configs):
    """Create a ProviderManager instance with sample configurations."""
    return ProviderManager(sample_provider_configs)


@pytest.fixture
def mock_discovery_service():
    """Create a mock ModelDiscoveryService."""
    mock_service = MagicMock()
    mock_service.validate_api_key.return_value = True
    mock_service.discover_models.return_value = [
        {"id": "gpt-4o"},
        {"id": "gpt-4o-mini"},
        {"id": "gpt-3.5-turbo"}
    ]
    mock_service.validate_model.return_value = True
    return mock_service


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for testing file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# Test Dict-like Interface Methods

def test_get_existing_provider(provider_manager):
    """Test get() method with existing provider."""
    config = provider_manager.get("openai")
    assert config is not None
    assert isinstance(config, ProviderConfig)
    assert config.name == "OpenAI"
    assert config.api_key == "sk-test-openai-key"


def test_get_nonexistent_provider(provider_manager):
    """Test get() method with non-existent provider returns None."""
    config = provider_manager.get("nonexistent")
    assert config is None


def test_getitem_existing_provider(provider_manager):
    """Test __getitem__() method with existing provider."""
    config = provider_manager["openai"]
    assert isinstance(config, ProviderConfig)
    assert config.name == "OpenAI"


def test_getitem_nonexistent_provider(provider_manager):
    """Test __getitem__() method with non-existent provider raises KeyError."""
    with pytest.raises(KeyError):
        _ = provider_manager["nonexistent"]


def test_contains_existing_provider(provider_manager):
    """Test __contains__() method with existing provider."""
    assert "openai" in provider_manager
    assert "anthropic" in provider_manager
    assert "groq" in provider_manager


def test_contains_nonexistent_provider(provider_manager):
    """Test __contains__() method with non-existent provider."""
    assert "nonexistent" not in provider_manager
    assert "cohere" not in provider_manager


def test_keys(provider_manager):
    """Test keys() method returns all provider names."""
    keys = provider_manager.keys()
    assert isinstance(keys, list)
    assert set(keys) == {"openai", "anthropic", "groq"}


def test_values(provider_manager):
    """Test values() method returns all provider configs."""
    values = provider_manager.values()
    assert isinstance(values, list)
    assert len(values) == 3
    assert all(isinstance(v, ProviderConfig) for v in values)


def test_items(provider_manager):
    """Test items() method returns all (name, config) pairs."""
    items = provider_manager.items()
    assert isinstance(items, list)
    assert len(items) == 3
    for name, config in items:
        assert isinstance(name, str)
        assert isinstance(config, ProviderConfig)
        assert name in ["openai", "anthropic", "groq"]


def test_model_dump(provider_manager):
    """Test model_dump() method serializes to dictionary."""
    dumped = provider_manager.model_dump()
    assert isinstance(dumped, dict)
    assert "openai" in dumped
    assert "anthropic" in dumped
    assert "groq" in dumped
    assert dumped["openai"]["name"] == "OpenAI"
    assert dumped["openai"]["api_key"] == "sk-test-openai-key"


# Test Provider Management Methods

def test_get_provider_config_success(provider_manager):
    """Test get_provider_config() with existing provider."""
    config = provider_manager.get_provider_config("openai")
    assert isinstance(config, ProviderConfig)
    assert config.name == "OpenAI"
    assert config.base_api_url == "https://api.openai.com/v1"


def test_get_provider_config_keyerror(provider_manager):
    """Test get_provider_config() with non-existent provider raises KeyError."""
    with pytest.raises(KeyError) as exc_info:
        provider_manager.get_provider_config("nonexistent")
    assert "Provider 'nonexistent' not found" in str(exc_info.value)


def test_get_all_provider_names(provider_manager):
    """Test get_all_provider_names() returns all provider names."""
    names = provider_manager.get_all_provider_names()
    assert isinstance(names, list)
    assert set(names) == {"openai", "anthropic", "groq"}


# Test Cross-Provider Model Resolution Methods

def test_merged_models(provider_manager):
    """Test merged_models() combines models from all providers."""
    merged = provider_manager.merged_models()
    assert isinstance(merged, list)
    assert len(merged) == 7  # 3 openai + 2 anthropic + 2 groq

    # Verify structure: list of (provider_name, (long_name, short_name))
    for provider_name, (long_name, short_name) in merged:
        assert provider_name in ["openai", "anthropic", "groq"]
        assert isinstance(long_name, str)
        assert isinstance(short_name, str)

    # Check specific models are present
    provider_models = {provider: (long, short) for provider, (long, short) in merged}
    assert any(long == "gpt-4o" for _, (long, _) in merged)
    assert any(long == "claude-3-opus-20240229" for _, (long, _) in merged)
    assert any(long == "llama-3.1-70b-versatile" for _, (long, _) in merged)


def test_merged_models_with_empty_valid_models(sample_provider_configs):
    """Test merged_models() handles providers with no valid models."""
    sample_provider_configs["empty_provider"] = {
        "name": "Empty Provider",
        "base_api_url": "https://api.empty.com/v1",
        "api_key": "sk-test",
        "valid_models": {},
        "invalid_models": []
    }
    manager = ProviderManager(sample_provider_configs)
    merged = manager.merged_models()
    # Should still return models from other providers
    assert len(merged) == 7  # Same as before, empty provider contributes nothing


def test_valid_scoped_models(provider_manager):
    """Test valid_scoped_models() generates formatted model strings."""
    scoped = provider_manager.valid_scoped_models()
    assert isinstance(scoped, list)
    assert len(scoped) == 7

    # Check format: "provider/long_name (short_name)"
    assert "openai/gpt-4o (gpt4o)" in scoped
    assert "anthropic/claude-3-opus-20240229 (opus)" in scoped
    assert "groq/llama-3.1-70b-versatile (llama70b)" in scoped


def test_get_api_for_model_string_with_provider_prefix_long_name(provider_manager):
    """Test get_api_for_model_string() with provider-prefixed long model name."""
    provider_config, model = provider_manager.get_api_for_model_string("openai/gpt-4o")
    assert isinstance(provider_config, ProviderConfig)
    assert provider_config.name == "OpenAI"
    assert model == "gpt-4o"


def test_get_api_for_model_string_with_provider_prefix_short_name(provider_manager):
    """Test get_api_for_model_string() with provider-prefixed short model name."""
    provider_config, model = provider_manager.get_api_for_model_string("openai/gpt4o")
    assert isinstance(provider_config, ProviderConfig)
    assert provider_config.name == "OpenAI"
    assert model == "gpt4o"


def test_get_api_for_model_string_with_provider_prefix_invalid_model(provider_manager):
    """Test get_api_for_model_string() with invalid model for specified provider."""
    with pytest.raises(ValueError) as exc_info:
        provider_manager.get_api_for_model_string("openai/nonexistent-model")
    assert "Invalid model for provider openai: nonexistent-model" in str(exc_info.value)


def test_get_api_for_model_string_without_prefix_long_name(provider_manager):
    """Test get_api_for_model_string() without prefix searches across providers."""
    provider_config, model = provider_manager.get_api_for_model_string("gpt-4o")
    assert isinstance(provider_config, ProviderConfig)
    assert provider_config.name == "OpenAI"
    assert model == "gpt-4o"


def test_get_api_for_model_string_without_prefix_short_name(provider_manager):
    """Test get_api_for_model_string() without prefix using short name."""
    provider_config, model = provider_manager.get_api_for_model_string("opus")
    assert isinstance(provider_config, ProviderConfig)
    assert provider_config.name == "Anthropic"
    assert model == "claude-3-opus-20240229"  # Returns long name


def test_get_api_for_model_string_without_prefix_invalid_model(provider_manager):
    """Test get_api_for_model_string() with invalid model raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        provider_manager.get_api_for_model_string("totally-invalid-model")
    assert "Invalid model: totally-invalid-model" in str(exc_info.value)


def test_get_api_for_model_string_case_insensitive_provider(provider_manager):
    """Test get_api_for_model_string() with case-insensitive provider prefix."""
    provider_config, model = provider_manager.get_api_for_model_string("OpenAI/gpt-4o")
    assert provider_config.name == "OpenAI"
    assert model == "gpt-4o"

    provider_config, model = provider_manager.get_api_for_model_string("GROQ/mixtral-8x7b-32768")
    assert provider_config.name == "Groq"
    assert model == "mixtral-8x7b-32768"


def test_validate_model_success(provider_manager):
    """Test validate_model() with valid model."""
    model = provider_manager.validate_model("openai/gpt-4o")
    assert model == "gpt-4o"

    model = provider_manager.validate_model("opus")
    assert model == "claude-3-opus-20240229"


def test_validate_model_failure(provider_manager):
    """Test validate_model() with invalid model raises ValueError."""
    with pytest.raises(ValueError):
        provider_manager.validate_model("invalid-model")

    with pytest.raises(ValueError):
        provider_manager.validate_model("openai/nonexistent")


def test_split_first_slash_with_slash(provider_manager):
    """Test split_first_slash() with slash present."""
    prefix, model = provider_manager.split_first_slash("openai/gpt-4o")
    assert prefix == "openai"
    assert model == "gpt-4o"

    prefix, model = provider_manager.split_first_slash("provider/model/with/slashes")
    assert prefix == "provider"
    assert model == "model/with/slashes"


def test_split_first_slash_without_slash(provider_manager):
    """Test split_first_slash() without slash."""
    prefix, model = provider_manager.split_first_slash("gpt-4o")
    assert prefix == ""
    assert model == "gpt-4o"


# Test Model Discovery Methods

def test_discover_models_all_providers(provider_manager, mock_discovery_service):
    """Test discover_models() with all providers and data_directory parameter."""
    provider_manager.discovery_service = mock_discovery_service

    with tempfile.TemporaryDirectory() as tmpdir:
        result = provider_manager.discover_models(data_directory=tmpdir)

        assert result is True
        assert mock_discovery_service.discover_models.call_count == 3  # Called for each provider
        assert mock_discovery_service.validate_api_key.call_count == 3


def test_discover_models_specific_provider(provider_manager, mock_discovery_service):
    """Test discover_models() with provider filtering."""
    provider_manager.discovery_service = mock_discovery_service

    with tempfile.TemporaryDirectory() as tmpdir:
        result = provider_manager.discover_models(provider="openai", data_directory=tmpdir)

        assert result is True
        assert mock_discovery_service.discover_models.call_count == 1
        assert mock_discovery_service.validate_api_key.call_count == 1


def test_discover_models_nonexistent_provider(provider_manager, mock_discovery_service, capsys):
    """Test discover_models() with non-existent provider."""
    provider_manager.discovery_service = mock_discovery_service

    with tempfile.TemporaryDirectory() as tmpdir:
        result = provider_manager.discover_models(provider="nonexistent", data_directory=tmpdir)

        assert result is False
        captured = capsys.readouterr()
        assert "Provider 'nonexistent' not found" in captured.out


def test_discover_models_no_api_key(provider_manager, mock_discovery_service, capsys):
    """Test discover_models() skips providers without valid API keys."""
    mock_discovery_service.validate_api_key.return_value = False
    provider_manager.discovery_service = mock_discovery_service

    with tempfile.TemporaryDirectory() as tmpdir:
        result = provider_manager.discover_models(data_directory=tmpdir)

        # Should still return True but skip providers
        assert result is True
        captured = capsys.readouterr()
        assert "No valid API key configured" in captured.out


def test_discover_models_api_error(provider_manager, mock_discovery_service, capsys):
    """Test discover_models() handles API errors gracefully."""
    mock_discovery_service.discover_models.side_effect = Exception("API Error")
    provider_manager.discovery_service = mock_discovery_service

    with tempfile.TemporaryDirectory() as tmpdir:
        result = provider_manager.discover_models(data_directory=tmpdir)

        assert result is False
        captured = capsys.readouterr()
        assert "Error discovering models" in captured.out


def test_discover_models_force_refresh(provider_manager, mock_discovery_service):
    """Test discover_models() with force_refresh parameter."""
    provider_manager.discovery_service = mock_discovery_service

    with tempfile.TemporaryDirectory() as tmpdir:
        result = provider_manager.discover_models(force_refresh=True, data_directory=tmpdir)

        assert result is True
        # Verify force_refresh was passed to discover_models
        for call in mock_discovery_service.discover_models.call_args_list:
            assert call[0][1] is True  # force_refresh parameter


def test_discover_models_persist_on_success(provider_manager, mock_discovery_service, temp_data_dir):
    """Test discover_models() persists configurations when persist_on_success=True."""
    provider_manager.discovery_service = mock_discovery_service

    result = provider_manager.discover_models(
        persist_on_success=True,
        data_directory=temp_data_dir
    )

    assert result is True

    # Check that YAML file was created
    yaml_path = os.path.join(temp_data_dir, "openaicompat-providers.yaml")
    assert os.path.exists(yaml_path)


def test_discover_models_no_persist_on_failure(provider_manager, mock_discovery_service, temp_data_dir):
    """Test discover_models() does not persist when discovery fails."""
    mock_discovery_service.discover_models.side_effect = Exception("API Error")
    provider_manager.discovery_service = mock_discovery_service

    result = provider_manager.discover_models(
        persist_on_success=True,
        data_directory=temp_data_dir
    )

    assert result is False

    # Check that YAML file was not created
    yaml_path = os.path.join(temp_data_dir, "openaicompat-providers.yaml")
    assert not os.path.exists(yaml_path)


def test_get_available_models_all_providers(provider_manager):
    """Test get_available_models() returns models from all providers."""
    models = provider_manager.get_available_models()
    assert isinstance(models, list)
    assert "gpt-4o" in models
    assert "gpt-4o-mini" in models
    assert "claude-3-opus-20240229" in models
    assert "llama-3.1-70b-versatile" in models


def test_get_available_models_filtered(provider_manager):
    """Test get_available_models() with provider filter."""
    models = provider_manager.get_available_models(filter_by_provider="openai")
    assert isinstance(models, list)
    assert "gpt-4o" in models
    assert "gpt-4o-mini" in models
    # Should not include models from other providers
    assert "claude-3-opus-20240229" not in models
    assert "llama-3.1-70b-versatile" not in models


# Test Utility Methods

def test_get_short_name():
    """Test get_short_name() static method."""
    short_name = ProviderManager.get_short_name("gpt-4o-mini-2024-07-18")
    # Currently returns the same name
    assert short_name == "gpt-4o-mini-2024-07-18"


def test_find_model_success(provider_manager):
    """Test find_model() finds model across providers."""
    results = provider_manager.find_model("gpt-4o")
    assert isinstance(results, list)
    assert len(results) == 1

    provider_config, model_name = results[0]
    assert isinstance(provider_config, ProviderConfig)
    assert provider_config.name == "OpenAI"
    assert model_name == "gpt-4o"


def test_find_model_multiple_providers(sample_provider_configs):
    """Test find_model() when model exists in multiple providers."""
    # Add same model to multiple providers
    sample_provider_configs["openai"]["valid_models"]["shared-model"] = "shared"
    sample_provider_configs["groq"]["valid_models"]["shared-model"] = "shared"

    manager = ProviderManager(sample_provider_configs)
    results = manager.find_model("shared-model")

    assert len(results) == 2
    provider_names = [config.name for config, _ in results]
    assert "OpenAI" in provider_names
    assert "Groq" in provider_names


def test_find_model_not_found(provider_manager):
    """Test find_model() returns empty list when model not found."""
    results = provider_manager.find_model("nonexistent-model")
    assert isinstance(results, list)
    assert len(results) == 0


def test_find_model_partial_match(provider_manager):
    """Test find_model() with partial name matching."""
    results = provider_manager.find_model("gpt")
    assert isinstance(results, list)
    assert len(results) >= 1  # Should find at least one GPT model


# Test YAML Persistence

def test_persist_provider_configs(provider_manager, temp_data_dir):
    """Test persist_provider_configs() creates YAML file with correct structure."""
    provider_manager.persist_provider_configs(temp_data_dir)

    yaml_path = os.path.join(temp_data_dir, "openaicompat-providers.yaml")
    assert os.path.exists(yaml_path)

    # Read and verify YAML content
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    assert "providers" in data
    assert "openai" in data["providers"]
    assert "anthropic" in data["providers"]
    assert "groq" in data["providers"]

    # Verify structure of openai provider
    openai_data = data["providers"]["openai"]
    assert openai_data["name"] == "OpenAI"
    assert openai_data["base_api_url"] == "https://api.openai.com/v1"
    assert openai_data["api_key"] == "sk-test-openai-key"
    assert "valid_models" in openai_data
    assert "invalid_models" in openai_data

    # Verify runtime fields are NOT persisted
    assert "_cached_models" not in str(data)
    assert "_cache_timestamp" not in str(data)
    assert "_cache_duration" not in str(data)


def test_persist_provider_configs_creates_directory(provider_manager):
    """Test persist_provider_configs() creates data directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a nested path that doesn't exist
        nested_path = os.path.join(tmpdir, "nested", "path")

        provider_manager.persist_provider_configs(nested_path)

        assert os.path.exists(nested_path)
        yaml_path = os.path.join(nested_path, "openaicompat-providers.yaml")
        assert os.path.exists(yaml_path)


def test_persist_provider_configs_default_directory(provider_manager, temp_data_dir):
    """Test persist_provider_configs() uses default directory when not specified."""
    with patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', mock_open()) as mock_file, \
         patch('yaml.dump') as mock_dump:

        provider_manager.persist_provider_configs()

        # Should use default ~/.llm_chat_cli
        expected_path = os.path.expanduser("~/.llm_chat_cli/openaicompat-providers.yaml")
        mock_file.assert_called_once_with(expected_path, 'w')


def test_persist_provider_configs_handles_errors(provider_manager, temp_data_dir, capsys):
    """Test persist_provider_configs() handles write errors gracefully."""
    with patch('builtins.open', side_effect=IOError("Permission denied")):
        with pytest.raises(IOError):
            provider_manager.persist_provider_configs(temp_data_dir)

        captured = capsys.readouterr()
        assert "Error persisting provider configurations" in captured.out


# Test Caching Functionality

def test_cache_initialization(sample_provider_configs):
    """Test that cached_valid_scoped_models is initialized to None."""
    provider_manager = ProviderManager(sample_provider_configs)
    assert provider_manager.cached_valid_scoped_models is None


def test_valid_scoped_models_caching(provider_manager, temp_data_dir):
    """Test that valid_scoped_models caches results and invalidates properly."""
    # First call should populate cache
    first_result = provider_manager.valid_scoped_models()
    assert provider_manager.cached_valid_scoped_models is not None
    assert provider_manager.cached_valid_scoped_models == first_result

    # Second call should return cached result
    second_result = provider_manager.valid_scoped_models()
    assert second_result == first_result
    assert provider_manager.cached_valid_scoped_models == first_result

    # After discover_models, cache should be invalidated
    provider_manager.discover_models(data_directory=temp_data_dir, persist_on_success=False)
    assert provider_manager.cached_valid_scoped_models is None

    # Next call should generate fresh results
    third_result = provider_manager.valid_scoped_models()
    assert provider_manager.cached_valid_scoped_models is not None
    assert provider_manager.cached_valid_scoped_models == third_result


def test_cache_invalidation_on_discover_models(provider_manager, temp_data_dir):
    """Test that discover_models properly invalidates the cache."""
    # Populate cache
    provider_manager.valid_scoped_models()
    assert provider_manager.cached_valid_scoped_models is not None

    # Call discover_models - should invalidate cache
    provider_manager.discover_models(data_directory=temp_data_dir, persist_on_success=False)
    assert provider_manager.cached_valid_scoped_models is None


def test_cache_invalidation_on_discover_models_with_provider_filter(provider_manager, temp_data_dir):
    """Test that discover_models invalidates cache even with provider filter."""
    # Populate cache
    provider_manager.valid_scoped_models()
    assert provider_manager.cached_valid_scoped_models is not None

    # Call discover_models with provider filter - should still invalidate cache
    provider_manager.discover_models(provider="openai", data_directory=temp_data_dir, persist_on_success=False)
    assert provider_manager.cached_valid_scoped_models is None


def test_cache_backward_compatibility(provider_manager):
    """Test that valid_scoped_models maintains backward compatibility."""
    # Test that method signature and return format remain unchanged
    result = provider_manager.valid_scoped_models()
    assert isinstance(result, list)
    assert len(result) > 0

    # Verify the format of returned strings
    for model_string in result:
        assert "/" in model_string
        assert "(" in model_string
        assert ")" in model_string


def test_cache_behavior_with_empty_providers():
    """Test cache behavior when there are no providers."""
    provider_manager = ProviderManager({})

    # Cache should be None initially
    assert provider_manager.cached_valid_scoped_models is None

    # First call should populate cache with empty list
    result = provider_manager.valid_scoped_models()
    assert result == []
    assert provider_manager.cached_valid_scoped_models == []

    # Second call should return cached empty list
    second_result = provider_manager.valid_scoped_models()
    assert second_result == []
    assert provider_manager.cached_valid_scoped_models == []


def test_cache_consistency_across_calls(provider_manager):
    """Test that cached results are identical to fresh results."""
    # Get fresh result
    fresh_result = provider_manager.valid_scoped_models()

    # Get cached result
    cached_result = provider_manager.valid_scoped_models()

    # They should be identical
    assert fresh_result == cached_result
    assert len(fresh_result) == len(cached_result)

    # Verify all elements are the same
    for fresh, cached in zip(fresh_result, cached_result):
        assert fresh == cached


def test_cache_invalidation_preserves_functionality(provider_manager, temp_data_dir):
    """Test that cache invalidation doesn't break functionality."""
    # Get initial result
    initial_result = provider_manager.valid_scoped_models()

    # Invalidate cache
    provider_manager.discover_models(data_directory=temp_data_dir, persist_on_success=False)
    assert provider_manager.cached_valid_scoped_models is None

    # Get result after invalidation
    after_invalidation_result = provider_manager.valid_scoped_models()

    # Results should be equivalent (same models, same format)
    assert len(initial_result) == len(after_invalidation_result)
    assert set(initial_result) == set(after_invalidation_result)


# Test Initialization

def test_init_with_dict_configs(sample_provider_configs):
    """Test ProviderManager initialization with dictionary configurations."""
    manager = ProviderManager(sample_provider_configs)

    assert len(manager.providers) == 3
    assert "openai" in manager.providers
    assert isinstance(manager.providers["openai"], ProviderConfig)


def test_init_with_provider_config_objects():
    """Test ProviderManager initialization with ProviderConfig objects."""
    configs = {
        "test_provider": ProviderConfig(
            name="Test Provider",
            base_api_url="https://api.test.com/v1",
            api_key="test-key",
            valid_models={"model-1": "m1"},
            invalid_models=[]
        )
    }

    manager = ProviderManager(configs)

    assert len(manager.providers) == 1
    assert "test_provider" in manager.providers
    assert manager.providers["test_provider"].name == "Test Provider"


def test_init_mixed_configs():
    """Test ProviderManager initialization with mixed dict and ProviderConfig objects."""
    configs = {
        "provider1": {
            "name": "Provider 1",
            "base_api_url": "https://api1.com/v1",
            "api_key": "key1",
            "valid_models": {},
            "invalid_models": []
        },
        "provider2": ProviderConfig(
            name="Provider 2",
            base_api_url="https://api2.com/v1",
            api_key="key2",
            valid_models={},
            invalid_models=[]
        )
    }

    manager = ProviderManager(configs)

    assert len(manager.providers) == 2
    assert all(isinstance(config, ProviderConfig) for config in manager.values())


# Test Edge Cases

def test_empty_provider_manager():
    """Test ProviderManager with no providers."""
    manager = ProviderManager({})

    assert len(manager.keys()) == 0
    assert manager.merged_models() == []
    assert manager.valid_scoped_models() == []

    with pytest.raises(ValueError):
        manager.get_api_for_model_string("any-model")


def test_provider_with_none_valid_models():
    """Test ProviderManager handles provider with None valid_models."""
    configs = {
        "test": {
            "name": "Test",
            "base_api_url": "https://test.com/v1",
            "api_key": "key",
            "valid_models": {},  # Use empty dict instead of None
            "invalid_models": []
        }
    }

    # ProviderConfig requires valid_models to be a dict, not None
    manager = ProviderManager(configs)
    merged = manager.merged_models()

    # Should not crash and should return empty list for this provider
    assert isinstance(merged, list)
