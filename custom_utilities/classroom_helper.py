import random
import string
import os
from config.env_loader import load_env  

load_env()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")

def generate_class_code(length: int = 8) -> str:
    """
    Generates a random alphanumeric class code of given length.
    Example: 'A9C2D4E8'
    """
    letters_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choices(letters_digits, k=length))
