import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
API_URL = os.getenv("API_BASE_URL")
