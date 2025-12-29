import os
from pathlib import Path
from dotenv import load_dotenv

def load_env():

    if os.getenv('_ENV_INITIALIZED'):
        return

    env_type = os.getenv("ENV", "dev")

    # Get project root and point to envs folder
    project_root = Path(__file__).parent.parent
    env_file_path = project_root / "envs" / f".env.{env_type}"
    
    if not env_file_path.exists():
        raise FileNotFoundError(f"Environment file not found: {env_file_path}")
    
    load_dotenv(dotenv_path=env_file_path)
    os.environ['_ENV_INITIALIZED'] = 'true'
