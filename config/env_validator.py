import os
from config.env_loader import load_env  

load_env()  


REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",      
    "MONGO_URI",
]

def validate_required_env_vars() -> None:
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

