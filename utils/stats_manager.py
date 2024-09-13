from utils.imports import *

class StatsGenerator:
    def __init__(self, db_name, collection_name):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[db_name]
        self.characters_collection = self.db[f"characters_{collection_name}"]
        self.stats_collection = self.db[f"stats_{collection_name}"]

    def _generate_stats_prompt(self, character_data, history=None):
        """
        Generate a prompt for creating character stats with both historical context and benchmark examples.

        Args:
            character_data (dict): Information about the character.
            history (list, optional): List of previously generated stats. Defaults to None.

        Returns:
            str: The generated prompt.
        """
        # Create history context with merged stats and character data
        history_context = ""
        if history:
            history_context = f"\nHere are some previously generated stats for reference:\n{json.dumps(history, indent=2)}\n"

        # Build the prompt with the examples included
        prompt = f"""
        You are an expert in creating character stats for a role-playing game. The stats should align with the character's race, role, and description. The stat values can range from 0 to 100,000, allowing for unlimited growth. Do not be generous with stat points. Stat points above 10,000 are overpowered in this universe

        {history_context}

        Character Details:
        Name: {character_data['name']}
        Alternate Names: {character_data.get('alternate_names', [])}
        Race: {character_data['race']}
        Role: {character_data['role']}
        Owner: {character_data.get('owner')}
        Description: {character_data['description']}

        Generate a dictionary with the following attributes:
        "strength": , "defense": , "agility": , "intelligence":, "magic":, "health":

        Output only the dictionary, nothing else. Examples:
        {{ "strength": number, "defense": number, "agility": number, "intelligence": number, "magic": number, "health": number }}
        
        
        plain output below"""

        return prompt



    def generate_initial_stats(self, character_data):
        """
        Generate initial stats for a character using a language model, taking into account the latest 3 existing stats.
        
        Args:
            character_data (dict): Information about the character for which stats are to be generated.
        
        Returns:
            dict: Generated stats for the character.
        """
        # Fetch the latest 3 stats from the stats collection, sorted by creation time in descending order
        previous_stats = list(
            self.stats_collection.find({}, {"name": 1, "stats": 1, "_id": 0})
            .sort("created_at", -1)  # Sort by 'created_at' in descending order
            .limit(3)  # Limit to the latest 3 documents
        )

        # Fetch character details for the names in previous stats
        character_names = [stat["name"] for stat in previous_stats]
        character_details = list(
            self.characters_collection.find({"name": {"$in": character_names}})
        )

        # Create a dictionary for quick lookup
        character_details_dict = {character["name"]: character for character in character_details}

        # Merge stats with character details
        merged_data = []
        for stat in previous_stats:
            name = stat["name"]
            character_info = character_details_dict.get(name, {})
            merged_entry = {**stat, **character_info}  # Merge the two dictionaries
            # Remove '_id' and 'timestamp' if present
            merged_entry.pop("_id", None)
            merged_entry.pop("timestamp", None)
            merged_data.append(merged_entry)

        
        # Generate a prompt using character data and merged history
        prompt = self._generate_stats_prompt(character_data, history=merged_data)

        # Request completion from the LLM
        completion = llm_client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=True
        )

        # Initialize an empty string to collect the streamed response
        stats_data = ""

        # Iterate over the streamed completion response and build the stats data
        for chunk in completion:
            stats_data += chunk.choices[0].delta.content or ""

        print(stats_data)
        # Return the generated stats as a dictionary
        return json.loads(stats_data)

    def check_for_new_characters(self):
        """
        Check for new characters that don't have stats generated yet and generate stats for them.
        """
        # Find characters whose names are not in the stats collection
        new_characters = self.characters_collection.find({
            "name": {"$nin": self.stats_collection.distinct("name")}
        })

        

        # Iterate over each new character and generate their initial stats
        for character in new_characters:
            stats = self.generate_initial_stats(character)
            # Insert the generated stats into the stats collection
            self.stats_collection.insert_one({
                "name": character["name"],
                "conversation_id": character["conversation_id"],
                "stats": stats,
                "created_at": datetime.utcnow()
        })


# Example usage
# stats_generator = StatsGenerator(db_name="game_db", collection_name="game_collection")
# stats_generator.check_for_new_characters()
