from utils.imports import *
from utils.conversation_manager import ConversationManager
from utils.environment_manager import EnvironmentManager
from utils.characteragent_manager import CharacterAgent
from utils.stats_manager import StatsGenerator


def main():
    conversation_manager = ConversationManager(DATABASE_NAME, COLLECTION_NAME)
    conversation_id = "test_1"
    environment_manager = EnvironmentManager(DATABASE_NAME, COLLECTION_NAME, conversation_id)
    character_manager = CharacterAgent(DATABASE_NAME, COLLECTION_NAME, "test_1")
    conversation_manager.create_conversation(conversation_id)
    stats_agent = StatsGenerator(DATABASE_NAME, COLLECTION_NAME)

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("Exiting conversation.")
            break

        conversation_manager.add_user_message(conversation_id, user_input)

        conversation_manager.generate_assistant_response(conversation_id, llm_client)
        environment_manager.process_latest_environment_description()
        character_manager.process_latest_message_for_characters()
        stats_agent.check_for_new_characters()
        
if __name__ == "__main__":
    main()