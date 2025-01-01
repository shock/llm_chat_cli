### Sessions (a.k.a. chats, threads, conversations)
- sessions are currently message histories as managed by the MessageHistory class
  - we want to extend the concept of sessions to include metadata
  - metadata includes the session name, creation date, and last update date (for sorting and display purposes)
- we'll add --session command line option to specify a session file
- session files are stored in the data directory specified in the config file
- session files are named with the session name and a timestamp
- session files are stored as JSON files
- There will be a Session class that manages the session file.  It will extend the MessageHistory class and add the metadata.

#### Default Session

- A new session will be created if no session is specified and no session file exists.  This session will be named "default" and will be stored in the data directory specified in the config file.
- The default session's filename will be "default.json" and will be stored in the data directory specified in the config file.
- If the user resets the chat history, the default session will automatically renamed and a new default session will be created.
- The default session's history (and thus datafile) will be updated in realtime as the user interacts with the chat interface.
- If the user exits the chat interface via KeyboardInterrupt, the default session will be saved without renaming.
- When the app is launched, the default session will be loaded and resumed if it exists, and the chat interface will be displayed with the default session's history.  The user can continue to interact with the chat interface and the default session will be updated in realtime.
- when the user saves the default session, the session will be saved with a new name (generated from the current timestamp and a LLM generated name) and any further interactions will be saved to the new session until the user exits the chat interface, or resets the chat history, or deletes the session.

#### Session Management

- The user can manage sessions by entering the /session command.  This will take the user into sesssion management mode, where they can rename, delete, and load sessions.
- The user can also load a session by entering the /load command followed by the session name.
- will will leverage prompt_toolkit to provide a list of sessions and allow the user to select one to load, rename, or delete.

#### Session file format with example data

```json
{
    "name": "history",
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
