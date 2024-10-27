import requests
import json

class OpenAIApi:
    """Class to interact with the OpenAI API."""

    # class level array of valid models
    valid_models = {
        "4o": "gpt-4o-2024-08-06",
        "4o-mini": "gpt-4o-mini-2024-07-18",
    }

    inverted_models = {v: k for k, v in valid_models.items()}

    DEFAULT_MODEL = valid_models["4o-mini"]

    # class method to validate model
    @classmethod
    def validate_model(cls, model):
        """Validate the model."""
        if model in cls.valid_models.keys():
            model = cls.valid_models[model]
        if model not in cls.valid_models.values():
            raise ValueError(f"Invalid model: {model}.  Valid models: {', '.join([f'{value} ({key})' for (key, value) in cls.valid_models.items()])}")
        return model

    def __init__(self, api_key, model="gpt-4o-mini-2024-07-18", base_api_url="https://api.openai.com/v1"):
        """Initialize the OpenAI API with an API key, model, system prompt, and base API URL."""
        self.api_key = api_key
        self.model = self.validate_model(model)
        self.base_api_url = base_api_url

    def set_model(self, model):
        """Set the model to be used."""
        # make sure the model is valid
        if model in self.valid_models.keys():
            model = self.valid_models[model]
        if model not in self.valid_models.values():
            raise ValueError(f"Invalid model: {model}.  Valid models: {', '.join([f"{value} (key)" for key, value in self.valid_models.keys()])}")
        self.model = model

    def brief_model(self):
        """Get a brief description of the model."""
        return self.inverted_models[self.model]

    def get_chat_completion(self, messages, stream=False):
        """Get a chat completion from the OpenAI API."""
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
        else:
            return response.json()

    def _stream_response(self, response):
        """Stream the response and yield chunks as they arrive."""
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

    def stream_chat_completion(self, messages):
        """Stream a chat completion from the OpenAI API and print as it's received."""
        response = ""
        for chunk in self.get_chat_completion(messages, stream=True):
            print(chunk, end='', flush=True)
            response += chunk
        print()  # Print a newline at the end
        return response
