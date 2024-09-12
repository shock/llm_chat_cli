import os
import toml
from pydantic import BaseModel, Field, ValidationError

class ConfigModel(BaseModel):
    api_key: str = Field(description="OpenAI API Key")
    model: str = Field(default="gpt-4o-mini-2024-07-18", description="OpenAI Model Name")
    system_prompt: str = Field(default="You're name is Lemmy. You are a helpful assistant that answers questions factually based on the provided context.", description="System Prompt")
    data_directory: str = Field(default="~/.llm_chat_cli", description="Data Directory for Session Files")
    sassy: bool = Field(default=False, description="Sassy Mode")

class Config:
    """Class to handle configuration load and storage."""

    def __init__(self, config_file, api_key=None):
        self.config_file = config_file
        self.api_key = api_key
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from the specified file."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                config_data = toml.load(file)
        else:
            config_data = {}

        if self.api_key:
            config_data["api_key"] = self.api_key

        try:
            return ConfigModel(**config_data)
        except ValidationError as e:
            raise e

    def get(self, key):
        """Get a configuration value by key."""
        return getattr(self.config, key)

    def is_sassy(self):
        """Check if sassy mode is enabled."""
        return self.config.sassy
