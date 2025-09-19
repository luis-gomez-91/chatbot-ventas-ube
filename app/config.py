from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
TOKEN_LLAMA = os.getenv("TOKEN_LLAMA")
API_URL = os.getenv("API_BASE_URL")