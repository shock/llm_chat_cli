"""
Unit tests for ProviderConfig class.

Tests all methods and edge cases for the ProviderConfig data model.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from modules.ProviderConfig import ProviderConfig


class TestProviderConfigInitialization:
    """Test ProviderConfig initialization and default values."""

    def test_provider_config_initialization_defaults(self):
        """Test ProviderConfig initialization with default values."""
        config = ProviderConfig()

        # Test default field values
        assert config.name == "Test Provider"
        assert config.base_api_url == "https://test.openai.com/v1"
        assert config.api_key == ""
        assert config.valid_models == {}
        assert config.invalid_models == []

        # Test runtime field initialization
        assert config._cached_models == []
        assert config._cache_timestamp == 0.0
        assert config._cache_duration == 300

    def test_provider_config_initialization_custom(self):
        """Test ProviderConfig initialization with custom values."""
        custom_valid_models = {
            "gpt-4": "gpt4",
            "gpt-3.5-turbo": "gpt35"
        }

        config = ProviderConfig(
            name="Custom Provider",
            base_api_url="https://custom.api.com/v1",
            api_key="test-key-123",
            valid_models=custom_valid_models,
            invalid_models=["old-model-1", "deprecated-model"]
        )

        # Test custom field values
        assert config.name == "Custom Provider"
        assert config.base_api_url == "https://custom.api.com/v1"
        assert config.api_key == "test-key-123"
        assert config.valid_models == custom_valid_models
        assert config.invalid_models == ["old-model-1", "deprecated-model"]

        # Test runtime field initialization
        assert config._cached_models == []
        assert config._cache_timestamp == 0.0
        assert config._cache_duration == 300

    def test_backward_compatibility(self):
        """Test ProviderConfig creation without invalid_models field (backward compatibility)."""
        # Test creation without invalid_models
        config = ProviderConfig(
            name="Legacy Provider",
            base_api_url="https://legacy.api.com/v1",
            api_key="legacy-key",
            valid_models={"model-1": "m1"}
        )

        # Verify invalid_models defaults to empty list
        assert config.invalid_models == []

        # Test YAML-like dict input without invalid_models
        config_dict = {
            "name": "YAML Provider",
            "base_api_url": "https://yaml.api.com/v1",
            "api_key": "yaml-key",
            "valid_models": {"model-2": "m2"}
        }
        config_from_dict = ProviderConfig(**config_dict)

        assert config_from_dict.invalid_models == []


class TestProviderConfigMethods:
    """Test ProviderConfig method implementations."""

    def test_get_valid_models_empty(self):
        """Test get_valid_models with empty valid_models."""
        config = ProviderConfig(valid_models={})

        result = config.get_valid_models()

        assert result == []
        assert isinstance(result, list)

    def test_get_valid_models_multiple(self):
        """Test get_valid_models with multiple valid_models."""
        valid_models = {
            "gpt-4": "gpt4",
            "gpt-3.5-turbo": "gpt35",
            "claude-3-opus": "claude3"
        }
        config = ProviderConfig(valid_models=valid_models)

        result = config.get_valid_models()

        # Verify returns list of long names only
        expected = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]
        assert sorted(result) == sorted(expected)
        assert isinstance(result, list)

    def test_get_invalid_models_empty(self):
        """Test get_invalid_models with empty invalid_models."""
        config = ProviderConfig(invalid_models=[])

        result = config.get_invalid_models()

        assert result == []
        assert isinstance(result, list)

    def test_get_invalid_models_multiple(self):
        """Test get_invalid_models with multiple invalid_models."""
        invalid_models = ["old-model-1", "deprecated-model", "legacy-model"]
        config = ProviderConfig(invalid_models=invalid_models)

        result = config.get_invalid_models()

        # Verify returns copy (not reference)
        assert result == invalid_models
        assert result is not invalid_models  # Should be a copy

    def test_find_model_exact_match_long_name(self):
        """Test find_model with exact match on long name."""
        valid_models = {
            "gpt-4": "gpt4",
            "gpt-3.5-turbo": "gpt35",
            "claude-3-opus": "claude3"
        }
        config = ProviderConfig(valid_models=valid_models)

        # Exact match on long name
        result = config.find_model("gpt-4")
        assert result == "gpt-4"

        result = config.find_model("claude-3-opus")
        assert result == "claude-3-opus"

    def test_find_model_exact_match_short_name(self):
        """Test find_model with exact match on short name."""
        valid_models = {
            "gpt-4": "gpt4",
            "gpt-3.5-turbo": "gpt35",
            "claude-3-opus": "claude3"
        }
        config = ProviderConfig(valid_models=valid_models)

        # Exact match on short name
        result = config.find_model("gpt4")
        assert result == "gpt-4"

        result = config.find_model("gpt35")
        assert result == "gpt-3.5-turbo"

    def test_find_model_case_insensitive(self):
        """Test find_model with case-insensitive matching."""
        valid_models = {
            "GPT-4": "GPT4",
            "gpt-3.5-turbo": "gpt35"
        }
        config = ProviderConfig(valid_models=valid_models)

        # Case-insensitive matching
        result = config.find_model("gpt-4")
        assert result == "GPT-4"

        result = config.find_model("GPT4")
        assert result == "GPT-4"

        result = config.find_model("GPT-3.5-TURBO")
        assert result == "gpt-3.5-turbo"

    def test_find_model_substring_match_long_name(self):
        """Test find_model with substring match on long name."""
        valid_models = {
            "gpt-4": "gpt4",
            "gpt-3.5-turbo": "gpt35",
            "claude-3-opus": "claude3"
        }
        config = ProviderConfig(valid_models=valid_models)

        # Substring match on long name
        result = config.find_model("gpt")
        assert result == "gpt-4"  # First match

        result = config.find_model("3.5")
        assert result == "gpt-3.5-turbo"

    def test_find_model_substring_match_short_name(self):
        """Test find_model with substring match on short name."""
        valid_models = {
            "gpt-4": "gpt4",
            "gpt-3.5-turbo": "gpt35",
            "claude-3-opus": "claude3"
        }
        config = ProviderConfig(valid_models=valid_models)

        # Substring match on short name
        result = config.find_model("pt4")
        assert result == "gpt-4"

        result = config.find_model("aude3")
        assert result == "claude-3-opus"

    def test_find_model_priority_order(self):
        """Test find_model search priority order."""
        valid_models = {
            "gpt-4": "gpt4",
            "gpt-4-turbo": "gpt4t",
            "gpt-3.5-turbo": "gpt35"
        }
        config = ProviderConfig(valid_models=valid_models)

        # Priority: long exact > short exact > long substring > short substring
        result = config.find_model("gpt-4")
        assert result == "gpt-4"  # Long exact match

        result = config.find_model("gpt4")
        assert result == "gpt-4"  # Short exact match

        result = config.find_model("gpt")
        assert result == "gpt-4"  # Long substring match (first)

        result = config.find_model("4t")
        assert result == "gpt-4-turbo"  # Short substring match

    def test_find_model_not_found(self):
        """Test find_model with nonexistent model name."""
        valid_models = {
            "gpt-4": "gpt4",
            "gpt-3.5-turbo": "gpt35"
        }
        config = ProviderConfig(valid_models=valid_models)

        # Nonexistent model that doesn't match any substring
        result = config.find_model("xyz-non-matching-pattern")
        assert result is None

        # Model name that doesn't exist as exact or substring match
        result = config.find_model("claude")
        assert result is None


class TestProviderConfigMergeValidModels:
    """Test merge_valid_models method."""

    def test_merge_valid_models_new(self):
        """Test merging new models."""
        config = ProviderConfig(valid_models={
            "existing-model": "existing"
        })

        new_models = ["new-model-1", "new-model-2"]
        config.merge_valid_models(new_models)

        # Verify new models use full ID as short name
        assert config.valid_models == {
            "existing-model": "existing",
            "new-model-1": "new-model-1",
            "new-model-2": "new-model-2"
        }

    def test_merge_valid_models_existing(self):
        """Test merging models that already exist."""
        config = ProviderConfig(valid_models={
            "existing-model": "existing",
            "another-model": "another"
        })

        existing_models = ["existing-model", "another-model"]
        config.merge_valid_models(existing_models)

        # Verify existing mappings are preserved
        assert config.valid_models == {
            "existing-model": "existing",
            "another-model": "another"
        }
        # Verify no duplicate entries created
        assert len(config.valid_models) == 2

    def test_merge_valid_models_mixed(self):
        """Test merging mix of new and existing models."""
        config = ProviderConfig(valid_models={
            "existing-model": "existing",
            "another-existing": "another"
        })

        mixed_models = ["existing-model", "new-model-1", "another-existing", "new-model-2"]
        config.merge_valid_models(mixed_models)

        # Verify correct behavior for both new and existing
        assert config.valid_models == {
            "existing-model": "existing",
            "another-existing": "another",
            "new-model-1": "new-model-1",
            "new-model-2": "new-model-2"
        }

    def test_merge_valid_models_empty(self):
        """Test merging empty list of models."""
        config = ProviderConfig(valid_models={
            "existing-model": "existing"
        })

        empty_models = []
        config.merge_valid_models(empty_models)

        # Verify no changes
        assert config.valid_models == {"existing-model": "existing"}


class TestProviderConfigCacheFields:
    """Test cache-related fields and initialization."""

    def test_cache_fields_initialization(self):
        """Test cache fields initialization via model_post_init."""
        config = ProviderConfig()

        # Verify PrivateAttr fields are initialized
        assert config._cached_models == []
        assert config._cache_timestamp == 0.0
        assert config._cache_duration == 300

    def test_cache_fields_not_serialized(self):
        """Test that cache fields are not included in serialization."""
        config = ProviderConfig(
            name="Test Provider",
            base_api_url="https://test.api.com/v1",
            api_key="test-key",
            valid_models={"model-1": "m1"},
            invalid_models=["bad-model"]
        )

        # Get model dict (serialized representation)
        model_dict = config.model_dump()

        # Verify cache fields are NOT in serialized output
        assert "_cached_models" not in model_dict
        assert "_cache_timestamp" not in model_dict
        assert "_cache_duration" not in model_dict

        # Verify persisted fields ARE in serialized output
        assert "name" in model_dict
        assert "base_api_url" in model_dict
        assert "api_key" in model_dict
        assert "valid_models" in model_dict
        assert "invalid_models" in model_dict