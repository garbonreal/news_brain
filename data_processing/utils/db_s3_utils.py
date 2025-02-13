import os
from dotenv import load_dotenv
from pymongo import MongoClient
import boto3
import logging


# Load environment variables
load_dotenv(override=False)

# Fetch News API Key
def get_news_api_key():
    return os.getenv("NEWS_API_KEY")


def get_bucket_name():
    return os.getenv("S3_BUCKET_NAME")


def get_mongo_client():
    try:
        mongo_host = os.getenv('MONGO_HOST')
        mongo_port = os.getenv('MONGO_PORT')
        mongo_user = os.getenv('MONGO_USER')
        mongo_password = os.getenv('MONGO_PASSWORD')
        mongo_db = os.getenv('MONGO_DATABASE')

        if not all([mongo_host, mongo_port, mongo_user, mongo_password, mongo_db]):
            logging.error("MongoDB environment variables are missing.")
            return None

        mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}?authSource=admin"

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        client.server_info()
        
        logging.info(f"Successfully connected to MongoDB at {mongo_host}:{mongo_port}")
        return client
    except Exception as e:
        logging.error("MongoDB connection failed: %s", e)
        return None


def get_s3_client():
    try:
        aws_access_key = os.getenv("AWS_ACCESS_KEY")
        aws_secret_key = os.getenv("AWS_SECRET_KEY")

        if not aws_access_key or not aws_secret_key:
            logging.error("AWS credentials not found in environment variables.")
            return None

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        
        logging.info("Successfully initialized S3 client.")
        return s3_client
    except Exception as e:
        logging.error("S3 client initialization failed: %s", e)
        return None