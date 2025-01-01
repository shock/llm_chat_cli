import requests
import json
from typing import Dict, Any

class OpenAIChatCompletionApi:
    """Base class for OpenAI-compatible chat completion APIs."""
    
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
        self.valid_models = valid_models
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
        if model in self.valid_models:
            return model
        raise ValueError(
            f"Invalid model: {model}. Valid models: {', '.join(self.valid_models)}"
        )
        
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
