import boto3
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from ml_model.sentiment_analysis import get_sentiment

load_dotenv(override=False)

# Fetch News API Key
api_key = os.getenv("NEWS_API_KEY")

# AWS S3 connection
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# MongoDB Configuration
MONGO_HOST = os.getenv('MONGO_HOST')  # Default to localhost
MONGO_PORT = int(os.getenv('MONGO_PORT'))  # Default MongoDB port
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_DB = os.getenv('MONGO_DATABASE')

MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["news_articles"]

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)


def read_text_from_s3(s3_url):
    """
    Reads and returns the text content from an S3 file.
    """
    filename = s3_url.split("/")[-1]
    
    obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=filename)

    return obj["Body"].read().decode("utf-8")

read_text_from_s3()