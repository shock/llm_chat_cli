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

    def __init__(self, config_file, api_key=None, create_config=False):
        self.config_file = config_file
        self.api_key = api_key
        self.config = self.load_config(create_config)

    def load_config(self, create_config=False):
        """Load configuration from the specified file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as file:
                    config_data = toml.load(file)
            except Exception as e:
                if not create_config:
                    print(f"Error loading config file: {e}")
                    raise e
                config_data = {}
        else:
            if not create_config:
                print(f"WARNING: no config file found at {self.config_file}.")
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

    def create_default_config(self, force=False):
        """Create a default configuration file."""
        if os.path.exists(self.config_file) and not force:
            confirm = input(f"Configuration file {self.config_file} already exists. Overwrite? (y/N): ")
            if confirm.lower() != 'y':
                print("Configuration creation aborted.")
                return False

        default_config = self.config
        config_dict = default_config.model_dump()

        with open(self.config_file, 'w') as f:
            f.write("# LLM API Chat Configuration File\n\n")
            for key, value in config_dict.items():
                f.write(f"# {ConfigModel.model_fields[key].description}\n")  # Use .description directly
                f.write(f"{toml.dumps({key: value})}\n\n")

        print(f"Default configuration file created at {self.config_file}")
        return True
