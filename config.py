import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SLIM_URL = os.getenv("SLIM_URL", "http://localhost:46357")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # App Settings
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
