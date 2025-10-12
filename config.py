import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))
FLOWER_THRESHOLD = int(os.getenv("FLOWER_THRESHOLD", 500))
