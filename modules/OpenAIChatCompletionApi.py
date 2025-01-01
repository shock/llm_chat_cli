import requests
import json
from typing import Dict, Any

PROVIDER_NAMES = {
    "openai": "OpenAI",
    "deepseek": "DeepSeek",
}

DEFAULT_MODEL = "openai/4o-mini"

class OpenAIChatCompletionApi:
    """Base class for OpenAI-compatible chat completion APIs."""

    DEFAULT_MODEL = "<unknown>"
    PROVIDER_NAME = "<unknown>"
    VALID_MODELS = {}

    def __init__(self, api_key: str, model: str, base_api_url: str, valid_models: Dict[str, str]):
        """
        Initialize the API with provider-specific configuration.

        Args:
            api_key: Provider API key
            model: Model to use
            base_api_url: Base API URL for the provider
            valid_models: Dictionary of valid models for this provider
        """
        self.api_key = api_key
        self.base_api_url = base_api_url
        self.valid_models = valid_models.copy()
        self.inverted_models = {v: k for k, v in valid_models.items()}
        self.set_model(model)

    def set_model(self, model: str):
        """
        Set the model to use.

        Args:
            model: Model name to use

        Raises:
            ValueError: If model is not supported
        """
        self.model = self.validate_model(model)

    def validate_model(self, model: str) -> str:
        """
        Validate the model against the provider's supported models.

        Args:
            model: Model name to validate

        Returns:
            Validated model name

        Raises:
            ValueError: If model is not supported
        """
        for key, value in self.valid_models.items():
            if model == key:
                return key
            if model == value:
                return key
        raise ValueError(
            f"Invalid model: {model}. Valid models: {', '.join(self.valid_models)}"
        )

    def brief_model(self) -> str:
        """Get a brief description of the model."""
        return self.valid_models.get(self.model, self.model)

    def get_chat_completion(self, messages: list, stream: bool = False) -> Dict[str, Any]:
        """
        Get a chat completion from the API.

        Args:
            messages: List of messages in the conversation
            stream: Whether to stream the response

        Returns:
            Dictionary containing the API response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
            "stream": stream
        }

        response = requests.post(
            f"{self.base_api_url}/chat/completions",
            headers=headers,
            json=data,
            stream=stream
        )

        if stream:
            return self._stream_response(response)
        return response.json()

    def _stream_response(self, response) -> str:
        """
        Stream the response and yield chunks as they arrive.

        Args:
            response: Streaming response object

        Yields:
            Chunks of the response as they arrive
        """
        for chunk in response.iter_lines():
            if chunk:
                chunk = chunk.decode('utf-8')
                if chunk.startswith('data: '):
                    chunk = chunk[6:]  # Remove the 'data: ' prefix
                if chunk != '[DONE]':
                    chunk_data = json.loads(chunk)
                    content = chunk_data['choices'][0]['delta'].get('content', '')
                    if content:
                        yield content

class OpenAIApi(OpenAIChatCompletionApi):
    """Class to interact with the OpenAI API."""

    PROVIDER_NAME = "openai"
    DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"
    VALID_MODELS = {
        "gpt-4o-2024-08-06": "4o",
        "gpt-4o-mini-2024-07-18": "4o-mini"
    }

    def __init__(self, api_key: str, model: str = "gpt-4o-mini-2024-07-18",
                 base_api_url: str = "https://api.openai.com/v1"):
        """
        Initialize the OpenAI API.

        Args:
            api_key: OpenAI API key
            model: Model to use
            base_api_url: Base API URL
        """
        super().__init__(api_key, model, base_api_url, self.VALID_MODELS)

    def validate_api_key(self) -> bool:
        """
        Validate the OpenAI API key.

        Returns:
            bool: True if key is valid, False otherwise
        """
        # OpenAI-specific API key validation logic
        return self.api_key.startswith("sk-") and len(self.api_key) == 51

    def stream_chat_completion(self, messages: list) -> str:
        """
        Stream a chat completion and print as it's received.

        Args:
            messages: List of messages in the conversation

        Returns:
            Complete response as a string
        """
        response = ""
        for chunk in self.get_chat_completion(messages, stream=True):
            print(chunk, end='', flush=True)
            response += chunk
        print()  # Print a newline at the end
        return response

class DeepSeekApi(OpenAIChatCompletionApi):
    """Class to interact with the DeepSeek API."""

    PROVIDER_NAME = "deepseek"
    DEFAULT_MODEL = "ds3" # deepseek v3
    VALID_MODELS = {
        "deepseek-chat": "ds3",
    }

    def __init__(self, api_key: str, model: str = "deepseek-chat",
                 base_api_url: str = "https://api.deepseek.com/v1"):
        """
        Initialize the DeepSeek API.

        Args:
            api_key: DeepSeek API key
            model: Model to use
            base_api_url: Base API URL
        """
        super().__init__(api_key, model, base_api_url, self.VALID_MODELS)

    def validate_api_key(self) -> bool:
        """
        Validate the DeepSeek API key.

        Returns:
            bool: True if key is valid, False otherwise
        """
        # DeepSeek-specific API key validation logic
        return self.api_key.startswith("ds-") and len(self.api_key) == 51

import re
def split_first_slash(text):
    # Use regex to split at the first slash
    match = re.match(r'([^/]*)/?(.*)', text)
    if match:
        if match.groups()[1] == '':
            return ('', match.groups()[0])
        return match.groups()
    return ('', text)

class OpenAIChatCompletionApi:
    @classmethod
    def get_api_for_model_string( cls, api_key: str, model_string: str = "4o-mini",
                 base_api_url: str = "https://api.openai.com/v1") -> OpenAIChatCompletionApi:
        # match the provider prefix (contiguous characters leading up to a '/')
        provider, model = split_first_slash(model_string)
        provider = provider.lower()
        if provider == "":
            provider = "openai"
        if provider in PROVIDER_NAMES.keys():
            provider = provider
            model = model_string[model_string.find('/')+1 :]
        # case statement for the provider class
        print(provider, model)
        if provider == "openai":
            return OpenAIApi(api_key, model, base_api_url)
        elif provider == "deepseek":
            return DeepSeekApi(api_key, model, base_api_url)
        raise ValueError(f"Invalid provider prefix: {provider}")
