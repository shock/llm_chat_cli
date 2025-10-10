"""
Unit tests for OpenAIChatCompletionApi class.

Tests all methods and edge cases for the OpenAIChatCompletionApi with mocked HTTP calls.
Focuses on chat completion functionality after model discovery logic removal.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
from modules.ProviderConfig import ProviderConfig


class TestOpenAIChatCompletionApiInitialization:
    """Test OpenAIChatCompletionApi initialization and constructor."""

    def test_constructor_with_provider_config(self):
        """Test constructor with ProviderConfig."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4", "gpt-3.5-turbo": "gpt35"}
            )
        }

        api = OpenAIChatCompletionApi(
            provider="openai",
            model="gpt-4",
            providers=providers
        )

        assert api.provider == "openai"
        assert api.model == "gpt-4"
        assert api.api_key == "test-key-123"
        assert api.base_api_url == "https://api.openai.com/v1"
        assert api.valid_models == {"gpt-4": "gpt4", "gpt-3.5-turbo": "gpt35"}
        assert api.inverted_models == {"gpt4": "gpt-4", "gpt35": "gpt-3.5-turbo"}

    def test_constructor_default_parameters(self):
        """Test constructor with default parameters."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4"}
            )
        }

        api = OpenAIChatCompletionApi(
            provider="openai",
            model="gpt-4",
            providers=providers
        )

        assert api.provider == "openai"
        assert api.model == "gpt-4"
        assert api.api_key == "test-key-123"
        assert api.base_api_url == "https://api.openai.com/v1"

    def test_constructor_provider_not_found(self):
        """Test constructor with non-existent provider."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4"}
            )
        }

        with pytest.raises(ValueError, match="No configuration found for provider: nonexistent"):
            OpenAIChatCompletionApi(
                provider="nonexistent",
                model="gpt-4",
                providers=providers
            )


class TestChatCompletionFunctionality:
    """Test chat completion functionality."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock OpenAIChatCompletionApi instance."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4", "gpt-3.5-turbo": "gpt35"}
            )
        }
        return OpenAIChatCompletionApi(
            provider="openai",
            model="gpt-4",
            providers=providers
        )

    def test_chat_completion_basic(self, mock_api):
        """Test basic chat completion."""
        messages = [
            {"role": "user", "content": "Hello, world!"}
        ]

        mock_response_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello there!"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 9,
                "completion_tokens": 12,
                "total_tokens": 21
            }
        }

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response

            result = mock_api.get_chat_completion(messages)

            # Verify request was made correctly
            mock_post.assert_called_once_with(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": "Bearer test-key-123",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": messages,
                    "temperature": 0.0,
                    "stream": False
                },
                stream=False
            )

            # Verify response
            assert result == mock_response_data

    def test_chat_completion_with_system_message(self, mock_api):
        """Test chat completion with system message."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ]

        mock_response_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "2+2 equals 4."
                    },
                    "finish_reason": "stop"
                }
            ]
        }

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response

            result = mock_api.get_chat_completion(messages)

            # Verify request includes system message
            call_args = mock_post.call_args
            assert call_args[1]['json']['messages'] == messages

            # Verify response
            assert result == mock_response_data

    def test_chat_completion_error_handling(self, mock_api):
        """Test chat completion error handling."""
        messages = [
            {"role": "user", "content": "Hello, world!"}
        ]

        mock_response_data = {
            "error": {
                "message": "Invalid API key",
                "type": "invalid_request_error",
                "code": "invalid_api_key"
            }
        }

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response

            result = mock_api.get_chat_completion(messages)

            # Should still return the error response
            assert result == mock_response_data

    def test_extract_gpt_version_openai_gpt4(self, mock_api):
        """Test GPT version extraction for OpenAI GPT-4."""
        mock_api.model = "gpt-4"
        mock_api.provider = "openai"

        version = mock_api._extract_gpt_version()
        assert version == 4

    def test_extract_gpt_version_openai_gpt35(self, mock_api):
        """Test GPT version extraction for OpenAI GPT-3.5."""
        mock_api.model = "gpt-3.5-turbo"
        mock_api.provider = "openai"

        version = mock_api._extract_gpt_version()
        assert version == 3

    def test_extract_gpt_version_non_openai(self, mock_api):
        """Test GPT version extraction for non-OpenAI provider."""
        mock_api.model = "deepseek-chat"
        mock_api.provider = "deepseek"

        version = mock_api._extract_gpt_version()
        assert version is None

    def test_extract_gpt_version_non_gpt_model(self, mock_api):
        """Test GPT version extraction for non-GPT model."""
        mock_api.model = "claude-3-opus"
        mock_api.provider = "openai"

        version = mock_api._extract_gpt_version()
        assert version is None


class TestStreamingChatCompletion:
    """Test streaming chat completion functionality."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock OpenAIChatCompletionApi instance."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4"}
            )
        }
        return OpenAIChatCompletionApi(
            provider="openai",
            model="gpt-4",
            providers=providers
        )

    def test_stream_chat_completion_basic(self, mock_api):
        """Test basic streaming chat completion."""
        messages = [
            {"role": "user", "content": "Hello, world!"}
        ]

        # Mock streaming response chunks
        mock_chunks = [
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            b'data: {"choices": [{"delta": {"content": " there!"}}]}',
            b'data: [DONE]'
        ]

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = mock_chunks
            mock_post.return_value = mock_response

            # Mock the print function to capture output
            with patch('builtins.print') as mock_print:
                result = mock_api.stream_chat_completion(messages)

            # Verify request was made correctly
            mock_post.assert_called_once_with(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": "Bearer test-key-123",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": messages,
                    "temperature": 0.0,
                    "stream": True
                },
                stream=True
            )

            # Verify print calls
            assert mock_print.call_count == 3  # "Hello", " there!", and newline

            # Verify result
            assert result == "Hello there!"

    def test_stream_chat_completion_error_handling(self, mock_api):
        """Test streaming chat completion error handling."""
        messages = [
            {"role": "user", "content": "Hello, world!"}
        ]

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            with pytest.raises(Exception, match="API request failed with status code 401"):
                mock_api.stream_chat_completion(messages)

    def test_stream_response_success(self, mock_api):
        """Test _stream_response with successful response."""
        mock_chunks = [
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            b'data: {"choices": [{"delta": {"content": " world!"}}]}',
            b'data: [DONE]'
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = mock_chunks

        result = list(mock_api._stream_response(mock_response))

        assert result == ["Hello", " world!"]

    def test_stream_response_with_reasoning_content(self, mock_api):
        """Test _stream_response with reasoning content."""
        mock_chunks = [
            b'data: {"choices": [{"delta": {"reasoning_content": "Let me think"}}]}',
            b'data: {"choices": [{"delta": {"reasoning_content": " about this"}}]}',
            b'data: {"choices": [{"delta": {"content": "Answer"}}]}',
            b'data: [DONE]'
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = mock_chunks

        result = list(mock_api._stream_response(mock_response))

        expected = ["REASONING:\n\n", "Let me think", " about this", "\n\nANSWER:\n\n", "Answer"]
        assert result == expected

    def test_stream_response_error_401(self, mock_api):
        """Test _stream_response with 401 error."""
        mock_response = Mock()
        mock_response.status_code = 401

        with pytest.raises(Exception, match="API request failed with status code 401"):
            list(mock_api._stream_response(mock_response))

    def test_stream_response_error_other(self, mock_api):
        """Test _stream_response with other error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}

        with patch('modules.OpenAIChatCompletionApi.sys.stderr') as mock_stderr:
            with pytest.raises(Exception, match="API request failed with status code 500"):
                list(mock_api._stream_response(mock_response))


class TestRequestResponseHandling:
    """Test request and response handling."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock OpenAIChatCompletionApi instance."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4"}
            )
        }
        return OpenAIChatCompletionApi(
            provider="openai",
            model="gpt-4",
            providers=providers
        )

    def test_make_request_headers(self, mock_api):
        """Test request headers are correctly formed."""
        messages = [
            {"role": "user", "content": "Test message"}
        ]

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"choices": [{"message": {"content": "Test response"}}]}
            mock_post.return_value = mock_response

            mock_api.get_chat_completion(messages)

            # Verify headers
            call_args = mock_post.call_args
            headers = call_args[1]['headers']

            assert headers["Authorization"] == "Bearer test-key-123"
            assert headers["Content-Type"] == "application/json"

    def test_handle_response_success(self, mock_api):
        """Test successful response handling."""
        messages = [
            {"role": "user", "content": "Test message"}
        ]

        expected_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "choices": [{"message": {"content": "Test response"}}]
        }

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            result = mock_api.get_chat_completion(messages)

            assert result == expected_response

    def test_handle_response_error(self, mock_api):
        """Test error response handling."""
        messages = [
            {"role": "user", "content": "Test message"}
        ]

        error_response = {
            "error": {
                "message": "Rate limit exceeded",
                "type": "rate_limit_error"
            }
        }

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = error_response
            mock_post.return_value = mock_response

            result = mock_api.get_chat_completion(messages)

            # Should return the error response
            assert result == error_response


class TestBackwardCompatibility:
    """Test backward compatibility with existing functionality."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock OpenAIChatCompletionApi instance."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4"}
            )
        }
        return OpenAIChatCompletionApi(
            provider="openai",
            model="gpt-4",
            providers=providers
        )

    def test_existing_chat_functionality_unchanged(self, mock_api):
        """Test that existing chat functionality remains unchanged."""
        messages = [
            {"role": "user", "content": "Hello"}
        ]

        expected_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "choices": [{"message": {"content": "Hi there!"}}]
        }

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            result = mock_api.get_chat_completion(messages)

            # Verify the basic chat completion still works
            assert result == expected_response

    def test_api_response_format_preserved(self, mock_api):
        """Test that API response format is preserved."""
        messages = [
            {"role": "user", "content": "Test"}
        ]

        expected_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Test response"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 8,
                "total_tokens": 13
            }
        }

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            result = mock_api.get_chat_completion(messages)

            # Verify standard OpenAI response format is preserved
            assert "id" in result
            assert "object" in result
            assert "choices" in result
            assert result["object"] == "chat.completion"

    def test_error_messages_preserved(self, mock_api):
        """Test that error messages are preserved."""
        messages = [
            {"role": "user", "content": "Test"}
        ]

        error_response = {
            "error": {
                "message": "Invalid API key",
                "type": "invalid_request_error",
                "code": "invalid_api_key"
            }
        }

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = error_response
            mock_post.return_value = mock_response

            result = mock_api.get_chat_completion(messages)

            # Verify error response format is preserved
            assert "error" in result
            assert result["error"]["message"] == "Invalid API key"


class TestIntegration:
    """Test integration with other components."""

    def test_openai_chat_completion_with_enhanced_provider_config(self):
        """Test integration with enhanced ProviderConfig."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4", "gpt-3.5-turbo": "gpt35"},
                invalid_models=["deprecated-model"]
            )
        }

        api = OpenAIChatCompletionApi(
            provider="openai",
            model="gpt-4",
            providers=providers
        )

        messages = [
            {"role": "user", "content": "Integration test"}
        ]

        expected_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "choices": [{"message": {"content": "Integration response"}}]
        }

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            result = api.get_chat_completion(messages)

            assert result == expected_response

    def test_chat_completion_after_model_discovery_removal(self):
        """Test chat completion works after model discovery removal."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4"}
            )
        }

        api = OpenAIChatCompletionApi(
            provider="openai",
            model="gpt-4",
            providers=providers
        )

        messages = [
            {"role": "user", "content": "Test after model discovery removal"}
        ]

        expected_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "choices": [{"message": {"content": "Works correctly"}}]
        }

        with patch('modules.OpenAIChatCompletionApi.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            result = api.get_chat_completion(messages)

            # Verify chat completion works without model discovery logic
            assert result == expected_response


class TestModelDiscoveryLogicRemovalVerification:
    """Verify that model discovery logic has been removed."""

    def test_no_model_discovery_methods_remain(self):
        """Verify no model discovery methods remain in OpenAIChatCompletionApi."""
        api_methods = dir(OpenAIChatCompletionApi)

        # These methods should NOT exist (were part of model discovery)
        discovery_methods = [
            'get_api_for_model_string',
            'get_models',
            'refresh_models',
            'get_valid_models',
            'is_valid_model',
            'get_model_aliases'
        ]

        for method in discovery_methods:
            assert method not in api_methods, f"Model discovery method {method} should not exist"

    def test_no_caching_fields_remain(self):
        """Verify no caching fields remain in OpenAIChatCompletionApi."""
        api_instance = OpenAIChatCompletionApi(
            provider="openai",
            model="gpt-4",
            providers={"openai": ProviderConfig()}
        )

        instance_attrs = dir(api_instance)

        # These caching fields should NOT exist
        caching_fields = [
            '_cached_models',
            '_cache_timestamp',
            '_cache_duration',
            'cached_models',
            'cache_timestamp'
        ]

        for field in caching_fields:
            assert field not in instance_attrs, f"Caching field {field} should not exist"

    def test_no_cross_provider_logic_remain(self):
        """Verify no cross-provider model discovery logic remains."""
        api_methods = dir(OpenAIChatCompletionApi)

        # These cross-provider methods should NOT exist
        cross_provider_methods = [
            'get_provider_for_model',
            'get_all_models',
            'find_model_across_providers',
            'refresh_all_models'
        ]

        for method in cross_provider_methods:
            assert method not in api_methods, f"Cross-provider method {method} should not exist"


class TestCreateApiInstance:
    """Test create_api_instance class method."""

    def test_create_api_instance_success(self):
        """Test successful creation of API instance."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4"}
            )
        }

        api = OpenAIChatCompletionApi.create_api_instance(
            providers=providers,
            provider="openai",
            model="gpt-4"
        )

        assert isinstance(api, OpenAIChatCompletionApi)
        assert api.provider == "openai"
        assert api.model == "gpt-4"
        assert api.api_key == "test-key-123"

    def test_create_api_instance_provider_not_found(self):
        """Test creation with non-existent provider."""
        providers = {
            "openai": ProviderConfig(
                name="OpenAI",
                base_api_url="https://api.openai.com/v1",
                api_key="test-key-123",
                valid_models={"gpt-4": "gpt4"}
            )
        }

        with pytest.raises(ValueError, match="Provider 'nonexistent' not found in providers"):
            OpenAIChatCompletionApi.create_api_instance(
                providers=providers,
                provider="nonexistent",
                model="gpt-4"
            )