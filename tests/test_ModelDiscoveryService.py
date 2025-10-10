"""
Unit tests for ModelDiscoveryService class.

Tests all methods and edge cases for the ModelDiscoveryService with mocked HTTP calls.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from modules.ModelDiscoveryService import ModelDiscoveryService
from modules.ProviderConfig import ProviderConfig


class TestModelDiscoveryService:
    """Test ModelDiscoveryService with mocked HTTP calls."""

    @pytest.fixture
    def mock_provider_config(self):
        """Create a mock ProviderConfig instance with test data."""
        return ProviderConfig(
            name="Test Provider",
            base_api_url="https://test.openai.com/v1",
            api_key="test-api-key-123",
            valid_models={"gpt-4": "gpt4", "gpt-3.5-turbo": "gpt35"},
            invalid_models=["deprecated-model"]
        )

    @pytest.fixture
    def mock_discovery_service(self):
        """Create a ModelDiscoveryService instance."""
        return ModelDiscoveryService()

    def test_discover_models_success(self, mock_provider_config, mock_discovery_service):
        """Test successful model discovery with HTTP call."""
        # Mock response data
        mock_response_data = {
            "data": [
                {"id": "gpt-4", "object": "model"},
                {"id": "gpt-3.5-turbo", "object": "model"},
                {"id": "claude-3-opus", "object": "model"}
            ]
        }

        with patch('modules.ModelDiscoveryService.requests.get') as mock_get:
            # Configure mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Call the method
            result = mock_discovery_service.discover_models(mock_provider_config)

            # Verify HTTP call was made
            mock_get.assert_called_once_with(
                "https://test.openai.com/v1/models",
                headers={
                    "Authorization": "Bearer test-api-key-123",
                    "Content-Type": "application/json"
                },
                timeout=10
            )

            # Verify models are cached
            assert mock_provider_config._cached_models == mock_response_data["data"]
            assert mock_provider_config._cache_timestamp > 0

            # Verify correct return value
            assert result == mock_response_data["data"]

    def test_discover_models_cache_hit(self, mock_provider_config, mock_discovery_service):
        """Test cache hit when models are already cached and not expired."""
        # Set up cached models with recent timestamp
        cached_models = [
            {"id": "gpt-4", "object": "model"},
            {"id": "gpt-3.5-turbo", "object": "model"}
        ]
        mock_provider_config._cached_models = cached_models
        mock_provider_config._cache_timestamp = time.time() - 100  # 100 seconds ago (within 5 min cache)

        with patch('modules.ModelDiscoveryService.requests.get') as mock_get:
            # Call the method without force_refresh
            result = mock_discovery_service.discover_models(mock_provider_config)

            # Verify no HTTP request was made
            mock_get.assert_not_called()

            # Verify cached models returned
            assert result == cached_models

    def test_discover_models_cache_expired(self, mock_provider_config, mock_discovery_service):
        """Test cache miss when cache is expired."""
        # Set up cached models with old timestamp
        old_cached_models = [
            {"id": "old-model", "object": "model"}
        ]
        mock_provider_config._cached_models = old_cached_models
        mock_provider_config._cache_timestamp = time.time() - 400  # 400 seconds ago (expired)

        # Mock new response data
        new_response_data = {
            "data": [
                {"id": "gpt-4", "object": "model"},
                {"id": "gpt-3.5-turbo", "object": "model"}
            ]
        }

        with patch('modules.ModelDiscoveryService.requests.get') as mock_get:
            # Configure mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = new_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Call the method
            result = mock_discovery_service.discover_models(mock_provider_config)

            # Verify HTTP request was made
            mock_get.assert_called_once()

            # Verify cache was updated
            assert mock_provider_config._cached_models == new_response_data["data"]
            assert mock_provider_config._cache_timestamp > time.time() - 10  # Recent timestamp

            # Verify new models returned
            assert result == new_response_data["data"]

    def test_discover_models_force_refresh(self, mock_provider_config, mock_discovery_service):
        """Test force refresh bypasses cache."""
        # Set up cached models
        cached_models = [
            {"id": "cached-model", "object": "model"}
        ]
        mock_provider_config._cached_models = cached_models
        mock_provider_config._cache_timestamp = time.time() - 100  # Recent cache

        # Mock new response data
        new_response_data = {
            "data": [
                {"id": "new-model", "object": "model"}
            ]
        }

        with patch('modules.ModelDiscoveryService.requests.get') as mock_get:
            # Configure mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = new_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Call the method with force_refresh=True
            result = mock_discovery_service.discover_models(mock_provider_config, force_refresh=True)

            # Verify HTTP request was made despite cache
            mock_get.assert_called_once()

            # Verify cache was updated
            assert mock_provider_config._cached_models == new_response_data["data"]

            # Verify new models returned
            assert result == new_response_data["data"]

    def test_discover_models_error_with_cache(self, mock_provider_config, mock_discovery_service):
        """Test error handling with fallback to cached models."""
        # Set up cached models with expired timestamp
        cached_models = [
            {"id": "cached-model", "object": "model"}
        ]
        mock_provider_config._cached_models = cached_models
        mock_provider_config._cache_timestamp = time.time() - 400  # 400 seconds ago (expired)

        with patch('modules.ModelDiscoveryService.requests.get') as mock_get:
            # Configure mock to raise exception
            mock_get.side_effect = Exception("Network error")

            # Call the method
            result = mock_discovery_service.discover_models(mock_provider_config)

            # Verify HTTP request was attempted
            mock_get.assert_called_once()

            # Verify fallback to cached models
            assert result == cached_models

    def test_discover_models_error_without_cache(self, mock_provider_config, mock_discovery_service):
        """Test error handling without cached models."""
        # Ensure no cached models
        mock_provider_config._cached_models = []
        mock_provider_config._cache_timestamp = 0

        with patch('modules.ModelDiscoveryService.requests.get') as mock_get:
            # Configure mock to raise exception
            mock_get.side_effect = Exception("Network error")

            # Call the method
            result = mock_discovery_service.discover_models(mock_provider_config)

            # Verify HTTP request was attempted
            mock_get.assert_called_once()

            # Verify empty list returned
            assert result == []

    def test_validate_model_success(self, mock_provider_config, mock_discovery_service):
        """Test successful model validation."""
        # Mock response with "pong" content
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "pong"
                    }
                }
            ]
        }

        with patch('modules.ModelDiscoveryService.requests.post') as mock_post:
            # Configure mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            # Call the method
            result = mock_discovery_service.validate_model(mock_provider_config, "gpt-4")

            # Verify HTTP call was made
            mock_post.assert_called_once_with(
                "https://test.openai.com/v1/chat/completions",
                headers={
                    "Authorization": "Bearer test-api-key-123",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": "If I say 'ping', you will respond with 'pong'."},
                        {"role": "user", "content": "ping"}
                    ],
                    "max_tokens": 10,
                    "temperature": 0.1
                },
                timeout=10
            )

            # Verify returns True
            assert result is True

    def test_validate_model_failure(self, mock_provider_config, mock_discovery_service):
        """Test model validation failure due to exception."""
        with patch('modules.ModelDiscoveryService.requests.post') as mock_post:
            # Configure mock to raise exception
            mock_post.side_effect = Exception("API error")

            # Call the method
            result = mock_discovery_service.validate_model(mock_provider_config, "gpt-4")

            # Verify HTTP call was attempted
            mock_post.assert_called_once()

            # Verify returns False
            assert result is False

    def test_validate_model_wrong_response(self, mock_provider_config, mock_discovery_service):
        """Test model validation with wrong response content."""
        # Mock response without "pong" content
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "hello"
                    }
                }
            ]
        }

        with patch('modules.ModelDiscoveryService.requests.post') as mock_post:
            # Configure mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            # Call the method
            result = mock_discovery_service.validate_model(mock_provider_config, "gpt-4")

            # Verify HTTP call was made
            mock_post.assert_called_once()

            # Verify returns False (no "pong" in response)
            assert result is False

    def test_validate_api_key_valid(self, mock_provider_config, mock_discovery_service):
        """Test API key validation with valid key."""
        mock_provider_config.api_key = "valid-api-key-123"

        result = mock_discovery_service.validate_api_key(mock_provider_config)

        assert result is True

    def test_validate_api_key_empty(self, mock_provider_config, mock_discovery_service):
        """Test API key validation with empty string."""
        mock_provider_config.api_key = ""

        result = mock_discovery_service.validate_api_key(mock_provider_config)

        assert result is False

    def test_validate_api_key_none(self, mock_provider_config, mock_discovery_service):
        """Test API key validation with None."""
        mock_provider_config.api_key = None

        result = mock_discovery_service.validate_api_key(mock_provider_config)

        assert result is False

    def test_validate_api_key_whitespace(self, mock_provider_config, mock_discovery_service):
        """Test API key validation with whitespace-only string."""
        mock_provider_config.api_key = "   \n\t  "

        result = mock_discovery_service.validate_api_key(mock_provider_config)

        assert result is False