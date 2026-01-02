import os
from config.env_loader import load_env  

load_env()  

# POC Mode: Only require essential environment variables
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",      # Required for OpenAI Realtime API
    "MONGO_URI",           # Required for session storage
    "GOOGLE_API_KEY",      # Required for session middleware
]

def validate_required_env_vars() -> None:
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

