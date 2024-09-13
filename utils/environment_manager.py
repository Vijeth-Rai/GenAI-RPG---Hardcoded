from utils.imports import *

class EnvironmentManager:
    def __init__(self, db_name, collection_name, conversation_id):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.conversation_id = conversation_id
        self.environments_collection = self.db[f"environments_{collection_name}"]

    def _retrieve_latest_message(self):
        """
        Retrieve the latest message from the collection where the role is either 'assistant' or 'user'.
        
        Returns:
            dict: The latest message document, or None if no messages are found.
        """
        conversation = self.collection.find_one({"conversation_id": self.conversation_id})

        latest_message = conversation["messages"][-1]

        return latest_message

    def _is_environment_description(self, message_content):
        """
        Determine if the message content describes an environment and extract the name of the place.
        
        Args:
            message_content (str): The content of the message.
        
        Returns:
            str: The name of the place if it describes an environment, otherwise False.
        """
        # Multi-shot prompt for the LLM
        multi_shot_prompt = """
        You are an expert in understanding descriptions of places. Given a description, identify and extract the name of that place. If it does not describe a place, return 'False'. Output only single word.

        Example 1:
        Input: "The kingdom of Avalon was vast and beautiful, filled with green pastures."
        Output: "Avalon"

        Example 2:
        Input: "She walked through the bustling city streets, admiring the architecture."
        Output: "False"

        Example 3:
        Input: "The conference room was filled with people discussing the project."
        Output: False

        Example 4:
        Input: "They explored the dense forest of Eldergrove, where ancient trees stood tall."
        Output: "Eldergrove"

        Example 5:
        Input: "{input_text}"
        Output:
        """

        # Fill the prompt with the actual input
        filled_prompt = multi_shot_prompt.format(input_text=message_content)

        # Call the LLM to generate the output
        completion = llm_client.chat.completions.create(
            model="gemma-7b-it",
            messages=[{"role": "system", "content": filled_prompt}],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )

        # Extract the generated output
        env_name = ""
        for chunk in completion:
            env_name += chunk.choices[0].delta.content or ""

        # Process the result
        env_name = env_name.strip().replace('"', '')
        #print(env_name)
        return env_name if env_name.lower() != "false" else False

    
    def _store_environment(self, env_name, description, is_update=False):
        """
        Store or update the environment in the collection.
        
        Args:
            env_name (str): The name of the environment.
            description (str): The description of the environment.
            is_update (bool): If True, store the description as 'description_updated', otherwise 'description_original'.
        """
        update_field = "description_updated" if is_update else "description_original"
        existing_env = self.environments_collection.find_one({"env_name": env_name})
        
        if existing_env:
            self.environments_collection.update_one(
                {"env_name": env_name},
                {"$set": {update_field: description, "timestamp": datetime.utcnow()}}
            )
        else:
            env_data = {
                "env_name": env_name,
                update_field: description,
                "timestamp": datetime.utcnow()
            }
            self.environments_collection.insert_one(env_data)

    def process_latest_environment_description(self):
        """
        Process the latest message to determine if it describes an environment and store or update the environment.
        """
        latest_message = self._retrieve_latest_message()
        if not latest_message:
            return
        
        #print(latest_message)
        env_name = self._is_environment_description(latest_message["content"])

        if env_name != False:
            existing_env = self.environments_collection.find_one({"env_name": env_name})
            if existing_env:
                pass
            else:
                self._store_environment(env_name, latest_message["content"], is_update=False)