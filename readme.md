# GenAI RPG Hardcoded

**GenAI RPG Hardcoded** is a hardcoded Python implementation of a conversational AI system designed for a text-based role-playing game (RPG). This project offers a simplified approach to handling complex interactions typically managed by libraries like LangChain, using straightforward Python code. It showcases how to build and manage conversations, environments, and characters in an RPG setting.

## Project Overview

The primary goal of this project is to create a flexible and extensible framework for an RPG where an AI interacts with users in a narrative-driven environment. The system is designed to handle:

- **Conversations**: Manages interactions between the user and the AI, keeping track of dialogue history.
- **Environments**: Describes and updates the game's environment based on user interactions.
- **Characters**: Manages character states and processes their responses to user inputs.
- **Statistics**: Monitors the game for new characters and other relevant statistics.

## Key Components

### `ConversationManager`

The `ConversationManager` class is responsible for managing the dialogue between the user and the AI. It handles creating new conversations, adding user messages, and generating AI responses. Key methods include:

- `create_conversation(conversation_id)`: Initializes a new conversation with a unique ID.
- `add_user_message(conversation_id, message)`: Adds a user message to the conversation.
- `generate_assistant_response(conversation_id, llm_client)`: Generates a response from the AI.

### `EnvironmentManager`

The `EnvironmentManager` class deals with the game's environment, including its description and any changes based on user actions. It ensures that the environment remains consistent and up-to-date. Key methods include:

- `process_latest_environment_description()`: Processes and updates the current environment description.

### `CharacterAgent`

The `CharacterAgent` class manages the characters within the game. It processes messages intended for characters and updates their states accordingly. Key methods include:

- `process_latest_message_for_characters()`: Processes the most recent message for characters and updates their responses.

### `StatsGenerator`

The `StatsGenerator` class monitors and generates statistics related to the game. It checks for new characters and other relevant game metrics. Key methods include:

- `check_for_new_characters()`: Checks and updates the list of characters in the game.

## How It Works

When you run the `main.py` script, the following sequence of events occurs:

1. **Initialization**:
   - The `ConversationManager` is instantiated with a database name and collection name.
   - The `EnvironmentManager`, `CharacterAgent`, and `StatsGenerator` are also initialized with relevant parameters.

2. **Starting the Conversation**:
   - A new conversation is created using a specified conversation ID.
   - The user is prompted to input text.

3. **Handling User Input**:
   - User messages are added to the conversation.
   - The AI generates a response based on the conversation history.
   - The environment and characters are updated based on the latest interactions.
   - Statistics are checked for any new characters or updates.

4. **Exiting the Conversation**:
   - The loop continues until the user types `exit`, at which point the conversation ends.

## Project Structure

- `main.py`: The main script that starts the application and handles user interaction.
- `utils/`: Contains utility modules and classes for managing various aspects of the RPG:
  - `conversation_manager.py`: Implements the `ConversationManager` class.
  - `environment_manager.py`: Implements the `EnvironmentManager` class.
  - `characteragent_manager.py`: Implements the `CharacterAgent` class.
  - `stats_manager.py`: Implements the `StatsGenerator` class.

## Future Enhancements

This project is a basic implementation with room for expansion. Future enhancements could include:

- **Advanced AI Integration**: Incorporate more sophisticated AI models or APIs for better responses and interactions.
- **Extended Environment Management**: Develop more complex environments with dynamic changes and interactions.
- **Character Development**: Add deeper character profiles and interactions to enrich the gameplay experience.
- **User Interface**: Create a graphical or web-based interface to make interactions more engaging.

## Contributing

Contributions are welcome! If you have suggestions, improvements, or bug fixes, please feel free to submit a pull request. Ensure that your code follows the project's style and conventions.

---

Thank you for exploring **GenAI RPG Hardcoded**. We hope you find this project both educational and enjoyable as you delve into the world of conversational AI and RPG development!

