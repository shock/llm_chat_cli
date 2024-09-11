import requests

class OpenAIApi:
    """Class to interact with the OpenAI API."""
    def __init__(self, api_key, model="gpt-4o-mini-2024-07-18", system_prompt="You are a helpful assistant that answers questions factually based on the provided context."):
        """Initialize the OpenAI API with an API key, model, and system prompt."""
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt

    def set_model(self, model):
        """Set the model to be used."""
        self.model = model

    def set_system_prompt(self, system_prompt):
        """Set the system prompt."""
        self.system_prompt = system_prompt

    def get_chat_completion(self, messages):
        """Get a chat completion from the OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        return response.json()
