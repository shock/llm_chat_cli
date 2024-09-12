## Features

### Configuration Features

1. **Configuration File Option**:
   - Add a `--config` option to specify a configuration file.
   - If no configuration file is specified, the default configuration will be loaded from `~/.llm_chat_cli.toml`.

2. **Configuration File Format**:
   - The configuration file will be in TOML format.
   - It will include the following fields:
     - `api_key`: The OpenAI API key, which can be overridden by the `OPENAI_API_KEY` environment variable.
     - `model`: The OpenAI model name, with a default value of `gpt-4o-mini-2024-07-18`.
     - `system_prompt`: The system prompt, which can be overridden by the `LLMC_SYSTEM_PROMPT` environment variable or the `--system-prompt` command-line option.
     - `data_directory`: The directory where session files will be stored, with a default value of `~/.llm_chat_cli`.

These features aim to provide flexibility and customization options for users, allowing them to configure the tool according to their preferences and needs.

a sample TOML configuration file (`~/.llm_chat_cli.toml`) based on the features outlined in the `TODO.md` file:

```toml
# LLM API Chat Configuration File

# OpenAI API Key
api_key = "your_openai_api_key_here"

# OpenAI Model Name
model = "gpt-4o-mini-2024-07-18"

# System Prompt
system_prompt = "You're name is Lemmy. You are a helpful assistant that answers questions factually based on the provided context."

# Data Directory for Session Files
data_directory = "~/.llm_chat_cli"
```

This sample configuration file includes all the necessary fields as described in the `TODO.md` file, formatted in TOML syntax. Users can customize these values according to their specific requirements.

### Sessions (a.k.a. chats, coversations)
- sessions are message histories as managed by the MessageHistory class, plus metadata
  - metadata includes the session name, creation date, and last update date (for sorting and display purposes)
- add --session option to specify a session file
- session files are stored in the data directory specified in the config file
- session files are named with the session name and a timestamp
- session files are stored as JSON files
- There will be a Session class that manages the session file.  It will extend the MessageHistory class and add the metadata.

#### Default Session

- A new session will be created if no session is specified and no session file exists.  This session will be named "default" and will be stored in the data directory specified in the config file.
- The default session's filename will be "default.json" and will be stored in the data directory specified in the config file.
- If the user resets the chat history, the default session will automatically renamed and a new defaultsession will be created.
- The default session's history (and thus datafile) will be updated in realtime as the user interacts with the chat interface.
- If the user exits the chat interface via KeyboardInterrupt, the default session will be saved without renaming.
- When the app is launched, the default session will be loaded if it exists, and the chat interface will be displayed with the default session's history.  The user can continue to interact with the chat interface and the default session will be updated in realtime.
- when the user saves the default session, the session will be saved with a new name (generated from the current timestamp and a LLM generated name) and any further interactions will be saved to the new session until the user exits the chat interface, or resets the chat history, or deletes the session.

#### Session Management

- The user can manage sessions by entering the /session command.  This will take the user into sesssion management mode, where they can rename, delete, and load sessions.
- The user can also load a session by entering the /load command followed by the session name.
- will will leverage prompt_toolkit to provide a list of sessions and allow the user to select one to load, rename, or delete.

#### Session file format with example data

```json
{
    "name": "default",
    "creation_date": "2023-09-10T15:00:00",
    "last_update_date": "2023-09-10T15:00:00",
    "history": [
        {
            "role": "system",
            "content": "You are a helpful assistant that answers questions factually based on the provided context."
        },
        {
            "role": "user",
            "content": "Hello, how are you?"
        },
        {
            "role": "assistant",
            "content": "I'm doing well, thank you for asking.
        }
    ]
}
```

Sesssion filename format for non-default sessions: "YYYY-MM-DD-HH-MM-SS-session_name.json"
