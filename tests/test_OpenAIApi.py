import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import requests
from unittest.mock import patch, MagicMock
from modules.OpenAIChatCompletionApi import OpenAIApi

def test_initialization():
    """Test the initialization of OpenAIApi."""
    api = OpenAIApi(api_key="test_api_key", model="4o-mini")
    assert api.api_key == "test_api_key"
    assert api.model == "gpt-4o-mini-2024-07-18"
    assert api.base_api_url == "https://api.openai.com/v1"

def test_initialization_invalid_model():
    """Test initialization with an invalid model."""
    with pytest.raises(ValueError):
        OpenAIApi(api_key="test_api_key", model="invalid_model")

def test_set_model():
    """Test setting the model."""
    api = OpenAIApi(api_key="test_api_key", model="4o-mini")
    api.set_model("4o")
    assert api.model == "gpt-4o-2024-08-06"

def test_set_model_invalid_model():
    """Test setting an invalid model."""
    api = OpenAIApi(api_key="test_api_key", model="4o-mini")
    with pytest.raises(ValueError):
        api.set_model("invalid_model")

@patch('requests.post')
def test_get_chat_completion(mock_post):
    """Test the get_chat_completion method."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}]
    }
    mock_post.return_value = mock_response

    api = OpenAIApi(api_key="test_api_key", model="4o-mini")
    response = api.get_chat_completion([{"role": "user", "content": "Hello"}])
    assert response == {"choices": [{"message": {"content": "Test response"}}]}

# @patch('requests.post')
# def test_stream_chat_completion(mock_post):
#     """Test the stream_chat_completion method."""
#     mock_response = MagicMock()
#     mock_response.iter_lines.return_value = [
#         'data: {"choices": [{"delta": {"content": "Test"}}]}',
#         'data: {"choices": [{"delta": {"content": " response"}}]}',
#         'data: [DONE]'
#     ]
#     mock_post.return_value = mock_response

#     api = OpenAIApi(api_key="test_api_key", model="4o-mini")
#     response = api.stream_chat_completion([{"role": "user", "content": "Hello"}])
#     assert response == "Test response"
