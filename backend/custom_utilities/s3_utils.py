import os
import aioboto3
from urllib.parse import urlparse
from dotenv import load_dotenv
from agents.ai_quiz.agents.topic_recommendation import TopicGenerator
import aioboto3

load_dotenv()

# Load environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = os.getenv("AWS_DEFAULT_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

async def download_txt_node(state: dict) -> dict:
    """Async S3 download"""
    s3_url = state.get("extracted_s3_url")
    
    parsed_url = urlparse(s3_url)
    bucket = parsed_url.netloc.split('.')[0]
    key = parsed_url.path.lstrip('/')
    
    session = aioboto3.Session()
    async with session.client('s3',
                             region_name=os.getenv("AWS_REGION_NAME"),
                             aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                             aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")) as s3:
        response = await s3.get_object(Bucket=bucket, Key=key)
        async with response['Body'] as stream:
            text_content = await stream.read()
    
    state["text_content"] = text_content.decode('utf-8')
    return state