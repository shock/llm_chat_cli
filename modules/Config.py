import os
import sys
import toml
from pydantic import BaseModel, Field, ValidationError

USER_NAME = "brother (with a lowercase b)"

SASSY_SYSTEM_PROMPT = """You're name is Lemmy. You are a rude, ugly, contrary, argumentative, complainer
that begrudgingly does what you're told and answers questions with a sassy, elitest attiude.
Use ascii and unicode characters when writing math equations.  Latex is not supported."""

DEFAULT_SYSTEM_PROMPT = f"""You're name is Lemmy.
You are a helpful assistant that answers questions factuallybased on the provided context.
Call the user {USER_NAME}.  If the user seems confused or entering
jibberish or incomplete messages, tell them so, and then tell them to "type /help for a list of commands"
Use ascii and unicode characters when writing math equations.  Latex is not supported."""

class ConfigModel(BaseModel):
    api_key: str = Field(description="OpenAI API Key", default="")
    base_api_url: str = Field(default="https://api.openai.com/v1", description="Base API URL")
    model: str = Field(default="gpt-4o-mini-2024-07-18", description="OpenAI Model Name")
    system_prompt: str = Field(default=DEFAULT_SYSTEM_PROMPT, description="Default System Prompt")
    sassy: bool = Field(default=False, description="Sassy Mode")
    stream: bool = Field(default=True, description="Stream Mode")

class Config:
    """Class to handle configuration load and storage."""

    def __init__(self, data_directory=None, config_file=None, overrides={}, create_config=False, load_config=True):
        self.data_directory = os.path.expanduser(data_directory or "~/.llm_chat_cli")
        config_file = config_file or os.path.join(self.data_directory, "config.toml")
        self.config_file = os.path.join(self.data_directory, "config.toml")
        self.overrides = overrides
        self.config = self.load_config(config_file, create_config)

        if not os.path.exists(self.data_directory):
            if create_config:
                os.makedirs(self.data_directory)
            else:
                raise FileNotFoundError(f"Data directory {self.data_directory} does not exist.")

        if not os.path.exists(os.path.join(self.data_directory, "config.toml")):
            if create_config:
                self.save()
                print(f"Created default configuration file in {self.data_directory}")


    def load_config(self, config_file, create_config=False):
        """Load configuration from the specified file."""
        config_data = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as file:
                    config_data = toml.load(file)
            except Exception as e:
                if not create_config:
                    print(f"Error loading config file: {e}")
                    raise e
                config_data = {}
        else:
            if not create_config:
                print(f"WARNING: no config file found at {config_file}.", file=sys.stderr)

        if config_data.get("sassy", False):
            config_data["system_prompt"] = SASSY_SYSTEM_PROMPT

        # override config values with command line or environment variables
        for key, value in self.overrides.items():
            if value:
                config_data[key] = value

        try:
            return ConfigModel(**config_data)
        except ValidationError as e:
            raise e

    def save(self):
        """Save the configuration to the config file."""
        config_file = os.path.join(self.data_directory, "config.toml")
        with open(config_file, 'w') as f:
            f.write("# LLM API Chat Configuration File\n\n")
            for key, value in self.config.model_dump().items():
                f.write(f"# {ConfigModel.model_fields[key].description}\n")  # Use .description directly
                f.write(f"{toml.dumps({key: value})}\n\n")
        self.new_config = False

    def get(self, key):
        """Get a configuration value by key."""
        return self.data_directory if key == 'data_directory' else getattr(self.config, key)

    def is_sassy(self):
        """Check if sassy mode is enabled."""
        return self.config.sassy