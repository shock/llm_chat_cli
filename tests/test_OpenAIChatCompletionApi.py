import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the modules directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
from modules.Types import ProviderConfig

class TestOpenAIChatCompletionApi:

    def test_create_for_model_querying(self):
        """Test the factory method for model querying."""
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider="openai",
            api_key="test-key",
            base_api_url="https://api.openai.com/v1"
        )

        assert api.provider == "openai"
        assert api.api_key == "test-key"
        assert api.base_api_url == "https://api.openai.com/v1"
        assert api.model == "dummy-model"

    def test_get_available_models_success(self):
        """Test successful model query."""
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider="openai",
            api_key="test-key",
            base_api_url="https://api.openai.com/v1"
        )

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [
                    {"id": "gpt-4", "object": "model", "created": 1234567890},
                    {"id": "gpt-3.5-turbo", "object": "model", "created": 1234567890}
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            models = api.get_available_models()

            assert len(models) == 2
            assert models[0]["id"] == "gpt-4"

    def test_get_available_models_error(self):
        """Test model query with API error."""
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider="openai",
            api_key="test-key",
            base_api_url="https://api.openai.com/v1"
        )

        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("API error")

            models = api.get_available_models()

            assert models == []

    def test_get_available_models_caching(self):
        """Test that caching works correctly."""
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider="openai",
            api_key="test-key",
            base_api_url="https://api.openai.com/v1"
        )

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [{"id": "gpt-4", "object": "model"}]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # First call should make API request
            models1 = api.get_available_models()
            assert len(models1) == 1
            assert mock_get.call_count == 1

            # Second call should use cache
            models2 = api.get_available_models()
            assert len(models2) == 1
            assert mock_get.call_count == 1  # No additional call

            # Force refresh should make new API request
            models3 = api.get_available_models(force_refresh=True)
            assert len(models3) == 1
            assert mock_get.call_count == 2

    def test_get_available_models_cache_fallback(self):
        """Test that cached models are returned on API error."""
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider="openai",
            api_key="test-key",
            base_api_url="https://api.openai.com/v1"
        )

        # First, populate the cache
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [{"id": "gpt-4", "object": "model"}]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            models1 = api.get_available_models()
            assert len(models1) == 1

        # Then simulate API failure
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("API error")

            models2 = api.get_available_models()
            assert len(models2) == 1  # Should return cached models
            assert models2[0]["id"] == "gpt-4"

    def test_integration_with_existing_validation(self):
        """Test that dynamic models integrate with existing validation logic."""
        # This test would verify that the new functionality doesn't break
        # the existing model validation and selection logic
        pass