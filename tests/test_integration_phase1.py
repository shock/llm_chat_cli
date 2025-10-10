"""
Integration tests for Phase 1: ProviderConfig and ModelDiscoveryService coordination
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import time
from unittest.mock import Mock, patch
from modules.ProviderConfig import ProviderConfig
from modules.ModelDiscoveryService import ModelDiscoveryService


class TestIntegrationPhase1:
    """Integration tests for ProviderConfig and ModelDiscoveryService coordination"""

    def test_model_discovery_service_updates_provider_config_cache(self):
        """Test that ModelDiscoveryService correctly updates ProviderConfig cache fields"""
        # Setup
        provider_config = ProviderConfig(
            name="Test Provider",
            base_api_url="https://api.test.com/v1",
            api_key="test-key",
            valid_models={"existing-model": "existing"}
        )
        discovery_service = ModelDiscoveryService()

        # Mock API response
        mock_models_response = {
            "data": [
                {"id": "model-1", "object": "model"},
                {"id": "model-2", "object": "model"}
            ]
        }

        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_models_response

            # Execute
            result = discovery_service.discover_models(provider_config)

            # Assert
            assert result == mock_models_response["data"]
            assert provider_config._cached_models == mock_models_response["data"]
            assert provider_config._cache_timestamp > 0
            assert provider_config._cache_timestamp <= time.time()

    def test_complete_workflow_discover_validate_merge(self):
        """Test complete workflow: discover → validate → merge"""
        # Setup
        provider_config = ProviderConfig(
            name="Test Provider",
            base_api_url="https://api.test.com/v1",
            api_key="test-key",
            valid_models={"existing-model": "existing"}
        )
        discovery_service = ModelDiscoveryService()

        # Mock discovery response
        mock_models_response = {
            "data": [
                {"id": "model-1", "object": "model"},
                {"id": "model-2", "object": "model"},
                {"id": "model-3", "object": "model"}
            ]
        }

        with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
            # Mock discovery
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_models_response

            # Mock validation - model-1 and model-2 are valid, model-3 is invalid
            def mock_post_side_effect(url, **kwargs):
                mock_response = Mock()
                mock_response.status_code = 200
                if "model-1" in kwargs.get('json', {}).get('model', '') or \
                   "model-2" in kwargs.get('json', {}).get('model', ''):
                    mock_response.json.return_value = {
                        "choices": [{"message": {"content": "pong"}}]
                    }
                else:
                    mock_response.json.return_value = {
                        "choices": [{"message": {"content": "invalid"}}]
                    }
                return mock_response

            mock_post.side_effect = mock_post_side_effect

            # Execute discovery
            discovered_models = discovery_service.discover_models(provider_config)
            model_names = [model["id"] for model in discovered_models]

            # Execute validation and categorization
            valid_models = []
            invalid_models = []

            for model_name in model_names:
                if discovery_service.validate_model(provider_config, model_name):
                    valid_models.append(model_name)
                else:
                    invalid_models.append(model_name)

            # Execute merge
            provider_config.merge_valid_models(valid_models)
            provider_config.invalid_models = invalid_models

            # Assert
            assert "model-1" in provider_config.valid_models
            assert "model-2" in provider_config.valid_models
            assert "model-3" in provider_config.invalid_models
            assert provider_config.valid_models["model-1"] == "model-1"  # full ID as short name
            assert provider_config.valid_models["model-2"] == "model-2"  # full ID as short name

    def test_error_handling_preserves_provider_config_state(self):
        """Test that error handling preserves ProviderConfig state"""
        # Setup
        provider_config = ProviderConfig(
            name="Test Provider",
            base_api_url="https://api.test.com/v1",
            api_key="test-key",
            valid_models={"existing-model": "existing"}
        )

        # Set up initial cache
        initial_cache = [{"id": "cached-model", "object": "model"}]
        provider_config._cached_models = initial_cache
        provider_config._cache_timestamp = time.time()

        discovery_service = ModelDiscoveryService()

        # Mock API failure
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("API Error")

            # Execute - should fall back to cached models
            result = discovery_service.discover_models(provider_config)

            # Assert - state preserved, fallback to cache
            assert result == initial_cache
            assert provider_config._cached_models == initial_cache
            assert provider_config._cache_timestamp > 0  # unchanged

    def test_cache_expiration_triggers_re_discovery(self):
        """Test that cache expiration triggers re-discovery"""
        # Setup
        provider_config = ProviderConfig(
            name="Test Provider",
            base_api_url="https://api.test.com/v1",
            api_key="test-key"
        )

        # Set up expired cache
        old_cache = [{"id": "old-model", "object": "model"}]
        provider_config._cached_models = old_cache
        provider_config._cache_timestamp = time.time() - 400  # 400 seconds old

        discovery_service = ModelDiscoveryService()

        # Mock new API response
        new_models_response = {
            "data": [{"id": "new-model", "object": "model"}]
        }

        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = new_models_response

            # Execute - should trigger re-discovery due to expired cache
            result = discovery_service.discover_models(provider_config)

            # Assert - new models cached
            assert result == new_models_response["data"]
            assert provider_config._cached_models == new_models_response["data"]
            assert provider_config._cache_timestamp > time.time() - 10  # recent

    def test_api_key_validation_integration(self):
        """Test API key validation integration"""
        # Test valid API key
        provider_config_valid = ProviderConfig(
            name="Test Provider",
            base_api_url="https://api.test.com/v1",
            api_key="valid-key"
        )

        # Test invalid API key
        provider_config_invalid = ProviderConfig(
            name="Test Provider",
            base_api_url="https://api.test.com/v1",
            api_key=""  # empty
        )

        discovery_service = ModelDiscoveryService()

        # Assert
        assert discovery_service.validate_api_key(provider_config_valid) is True
        assert discovery_service.validate_api_key(provider_config_invalid) is False

    def test_model_search_integration(self):
        """Test model search integration between ProviderConfig and ModelDiscoveryService"""
        # Setup provider with models
        provider_config = ProviderConfig(
            name="Test Provider",
            base_api_url="https://api.test.com/v1",
            api_key="test-key",
            valid_models={
                "gpt-4o-2024-08-06": "4o",
                "gpt-4o-mini-2024-07-18": "4o-mini"
            }
        )

        # Test exact match on long name
        assert provider_config.find_model("gpt-4o-2024-08-06") == "gpt-4o-2024-08-06"

        # Test exact match on short name
        assert provider_config.find_model("4o") == "gpt-4o-2024-08-06"

        # Test substring match
        assert provider_config.find_model("4o-mini") == "gpt-4o-mini-2024-07-18"

        # Test case insensitive
        assert provider_config.find_model("GPT-4O") == "gpt-4o-2024-08-06"

        # Test not found
        assert provider_config.find_model("nonexistent") is None