from utils.imports import *

class CharacterAgent:
    def __init__(self, db_name, collection_name, conversation_id):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.conversation_id = conversation_id
        self.characters_collection = self.db[f"characters_{collection_name}"]

    def _retrieve_latest_message(self):
        """
        Retrieve the latest message from the collection where the role is either 'assistant' or 'user'.
        
        Returns:
            dict: The latest message document, or None if no messages are found.
        """

        conversation = self.collection.find_one({"conversation_id": self.conversation_id})

        latest_message = conversation["messages"][-1]

        return latest_message
    
    def _is_character(self, message_content):
        """
        You will act as a part of a complex system, where your specific task is to write down names in the form of list.
        
        Args:
            message_content (str): The content of the message.
        
        Returns:
            list: A list of names identified as characters, or an empty list if no names are found.
        """
        multi_shot_prompt = """
        You are an expert in identifying names of characters, such as people or animals, in a text.
        Description is mandatory, short and sweet.
        Only output names as list as mentioned

        Example 1:
        Input: "John and his dog Max walked through the forest."
        Output: [{
            "name": "John",
            "titles": [],
            "race": "Human",
            "role": null,
            "owner": null,
            "description": "Main character in the story."
        },
        {
            "_id": ObjectId("..."),
            "name": "Max",
            "titles": [],
            "race": "Dog",
            "role": null,
            "owner": "John",
            "description": "John's faithful dog."
        }]

        Example 2:
        Input: "The kingdom of Avalon was ruled by Queen Elaine, who had a fierce tiger named Rajah."
        Output: [{
            "name": "Elaine",
            "titles": [],
            "race": "Human",
            "role": "Queen of Avalon",
            "owner": null,
            "description": "Ruler of the kingdom of Avalon."
        },
        {
            "name": "Rajah",
            "titles": [],
            "race": "Tiger",
            "role": null,
            "owner": "Elaine",
            "description": "Elaine's fierce tiger."
        }]


        Example 3:
        Input: "The Night Killer, The Archangel, Weilder of Susanoo, Sasonki, is the heavenly King of Eden."
        Output: [{
            "name": "Sasonki",
            "titles": ["The Night Killer", "The Archangel", "Weilder of Susanoo"],
            "race": "Angel",
            "role": "King of Eden.",
            "owner": null,
            "description": "Sasonki, known by many titles including The Night Killer, The Archangel, and Weilder of Susanoo, is the heavenly King of Eden."
        }]

        Example 4:
        Input: "The city streets were bustling with people, but none stood out."
        Output: []

        """

        # Fill the prompt with the actual input
        #filled_prompt = multi_shot_prompt.format()

        # Call the LLM to generate the output
        completion = llm_client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[{"role": "system", "content": multi_shot_prompt},
                      {"role": "user", "content": message_content}],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )

        char_data = ""
        for chunk in completion:
            char_data += chunk.choices[0].delta.content or ""

        #print(char_data)
        char_data = json.loads(char_data)
        return char_data

    def process_latest_message_for_characters(self):
        """
        Process the latest message to determine if it contains character names and store them in the characters collection.
        """
        latest_message = self._retrieve_latest_message()
        if not latest_message:
            return
        
        character_datas = self._is_character(latest_message["content"])
        for character_data in character_datas:
            if not character_data:
                continue

            existing_character = self.characters_collection.find_one({
                "$or": [
                    {"name": character_data["name"]},
                    {"alternate_names": character_data["name"]}
                ]
            })

            if existing_character:
                continue
            
            new_character_data = {
                "conversation_id": self.conversation_id,
                "name": character_data["name"],
                "alternate_names": character_data.get("alternate_names", []),
                "race": character_data.get("race", ""),
                "role": character_data.get("role", ""),
                "owner": character_data.get("owner", ""),
                "description": character_data.get("description", ""),
                "timestamp": datetime.utcnow()
            }
            self.characters_collection.insert_one(new_character_data)

    
