from tqdm import tqdm
from groq import Groq
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from datetime import datetime
import json

load_dotenv()

groq_key = os.getenv('GROQ')
DATABASE_NAME = os.getenv('DATABASE_NAME')
COLLECTION_NAME = os.getenv('TEST_COLLECTION')
MONGO_URI = os.getenv("MONGO_URI")

llm_client = Groq(api_key=groq_key)
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
