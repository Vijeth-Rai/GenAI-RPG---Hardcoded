from utils.imports import *

class ConversationManager:
    def __init__(self, db_name, collection_name):
        """
        Initialize the ConversationManager with a connection to the MongoDB database and collections.
        
        Args:
            db_name (str): The name of the MongoDB database.
            collection_name (str): The name of the MongoDB collection to store conversations.
        """
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.summary_collection = self.db[f"summary_{collection_name}"]

    def _store_message(self, conversation_id, role, content):
        """
        Store a message in the MongoDB collection, and check if a summary needs to be created.
        
        Args:
            conversation_id (str): The unique identifier for the conversation.
            role (str): The role of the message sender (e.g., 'user', 'assistant', 'system').
            content (str): The content of the message.
        
        Returns:
            str: The conversation ID or upserted ID.
        """
        message_data = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        result = self.collection.update_one(
            {"conversation_id": conversation_id},
            {"$push": {"messages": message_data}},
            upsert=True
        )
        self._check_and_create_summary(conversation_id)
        return result.upserted_id or conversation_id

    def _retrieve_messages(self, conversation_id):
        """
        Retrieve all messages from a conversation.
        
        Args:
            conversation_id (str): The unique identifier for the conversation.
        
        Returns:
            list: A list of messages in the conversation.
        """
        conversation = self.collection.find_one({"conversation_id": conversation_id})
        if conversation and "messages" in conversation:
            return conversation["messages"]
        return []

    def _conversation_exists(self, conversation_id):
        """
        Check if a conversation exists in the database.
        
        Args:
            conversation_id (str): The unique identifier for the conversation.
        
        Returns:
            bool: True if the conversation exists, False otherwise.
        """
        return self.collection.find_one({"conversation_id": conversation_id}) is not None

    def create_conversation(self, conversation_id):
        """
        Create a new conversation with an initial system message if it doesn't already exist.
        
        Args:
            conversation_id (str): The unique identifier for the conversation.
        """
        if not self._conversation_exists(conversation_id):
            self._store_message(conversation_id, "system", "You are a game master. Please describe everything in detail as if you are describing an anime scene.")

    def add_user_message(self, conversation_id, user_input):
        """
        Add a user message to the conversation.
        
        Args:
            conversation_id (str): The unique identifier for the conversation.
            user_input (str): The content of the user's message.
        """
        self._store_message(conversation_id, "user", user_input)

    def _get_conversation_messages(self, conversation_id, n=10):
        """
        Retrieve the last n messages from the conversation, including the system message if it exists.
        
        Args:
            conversation_id (str): The unique identifier for the conversation.
            n (int): The number of recent messages to retrieve (excluding the system message).
        
        Returns:
            list: A list of the most recent messages, including the system message if present.
        """
        all_messages = self._retrieve_messages(conversation_id)

        system_message = None
        for msg in all_messages:
            if msg['role'] == 'system':
                system_message = {"role": msg['role'], "content": msg['content']}
                break

        recent_messages = [
            {"role": msg['role'], "content": msg['content']}
            for msg in all_messages if msg['role'] != 'system'
        ][-n:]

        if system_message:
            return [system_message] + recent_messages
        else:
            return recent_messages

    def generate_assistant_response(self, conversation_id, llm_client, n=10):
        """
        Generate a response from the assistant using the conversation history and store it in the database.
        
        Args:
            conversation_id (str): The unique identifier for the conversation.
            llm_client (obj): The client object for interacting with the language model.
            n (int): The number of recent messages to use for generating the response.
        
        Returns:
            str: The assistant's generated response.
        """
        conversation_messages = self._get_conversation_messages(conversation_id, n)

        completion = llm_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=conversation_messages,
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        assistant_response = ""
        for chunk in completion:
            assistant_response += chunk.choices[0].delta.content or ""
        self._store_message(conversation_id, "assistant", assistant_response)
        return assistant_response

    def _check_and_create_summary(self, conversation_id, n=10):
        """
        Check if a summary needs to be created based on the number of messages and create it if necessary.
        
        Args:
            conversation_id (str): The unique identifier for the conversation.
            n (int): The number of messages after which a summary should be created.
        """
        messages = self._retrieve_messages(conversation_id)
        if len([msg for msg in messages if msg['role'] != 'system']) % n == 1:
            summary_prompt, user_prompt = self._create_summary_prompt(messages, conversation_id)
            summary_text = self._generate_summary(summary_prompt, user_prompt)
            self._store_summary(conversation_id, summary_text)

    def _create_summary_prompt(self, messages, conversation_id):
        """
        Create the prompt used for generating the conversation summary.
        
        Args:
            messages (list): The list of all messages in the conversation.
            conversation_id (str): The unique identifier for the conversation.
        
        Returns:
            tuple: A tuple containing the summary prompt and user prompt.
        """
        relevant_messages = [msg for msg in messages if msg['role'] != 'system'][-10:]
        summary_prompt = "Summarize the following conversation, keeping the important information and ignoring irrelevant details. The summary should not exceed 1024 tokens:\n\n"
        previous_summary = self.summary_collection.find_one({"conversation_id": conversation_id})
        
        if previous_summary:
            summary_prompt = (
                "This is the previous summary of the conversation:\n"
                f"{previous_summary['summary']}\n\n"
                "Using the information above, create a new summary incorporating only the most relevant details from the conversation below:\n\n"
            )
        
        user_prompt = ""
        for msg in relevant_messages:
            user_prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
        
        return summary_prompt, user_prompt

    def _generate_summary(self, summary_prompt, user_prompt):
        """
        Generate the summary text using the language model.
        
        Args:
            summary_prompt (str): The prompt containing the summary instructions.
            user_prompt (str): The prompt containing the conversation messages to summarize.
        
        Returns:
            str: The generated summary text.
        """
        completion = llm_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "system", "content": summary_prompt},
                       {"role": "user", "content": user_prompt}],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )

        summary = ""
        for chunk in completion:
            summary += chunk.choices[0].delta.content or ""
        return summary

    def _store_summary(self, conversation_id, summary_text):
        """
        Store the generated summary in the summary collection in MongoDB.
        
        Args:
            conversation_id (str): The unique identifier for the conversation.
            summary_text (str): The summary text to store.
        """
        summary_data = {
            "conversation_id": conversation_id,
            "summary": summary_text,
            "timestamp": datetime.utcnow()
        }
        self.summary_collection.insert_one(summary_data)

    def display_conversation(self, conversation_id):
        """
        Display the entire conversation by printing each message with its timestamp and role.
        
        Args:
            conversation_id (str): The unique identifier for the conversation.
        """
        messages = self._retrieve_messages(conversation_id)
        for message in messages:
            print(f"[{message['timestamp']}] {message['role']}: {message['content']}")


