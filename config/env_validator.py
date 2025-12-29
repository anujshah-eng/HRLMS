import os
from config.env_loader import load_env  

load_env()  
REQUIRED_ENV_VARS = [
    "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT",
    "DB_URL",
    "GOOGLE_API_KEY", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET",
    "JWT_SECRET_KEY", "JWT_ALGORITHM",
    "SENDER_EMAIL", "BREVO_API_KEY"
]

def validate_required_env_vars() -> None:
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
