import os
from dotenv import load_dotenv
import boto3
import newspaper
import logging
from pymongo import MongoClient
from datetime import datetime
import itertools


logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

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


def extract_news_content(url):
    """Scrape full article content using newspaper3k."""
    try:
        article = newspaper.Article(url)
        article.download()
        article.parse()
        return article.text.strip()
    except Exception as e:
        logging.info(f"Failed to load article content: {e}")
        return None


def load_to_s3(content, article_id):
    """Upload scraped content to S3 and return the S3 URL."""
    filename = f"{article_id}.txt"
    
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=filename,
            Body=content,
            ContentType="text/plain"
        )
        return f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{filename}"
    except Exception as e:
        logging.info(f"Failed to upload to S3: {e}")
        return None


def delete_s3_and_mongo(start_date, end_date):
    """
    Deletes S3 files and removes s3_url from MongoDB for documents within a date range.
    
    :param start_date: Start date (YYYY-MM-DD)
    :param end_date: End date (YYYY-MM-DD)
    """
    # Convert to datetime format
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Find all documents within the date range
    articles = collection.find({"publishedAt": {"$gte": start_dt, "$lte": end_dt}, "s3_url": {"$exists": True}})

    for article in list(articles):
        s3_url = article["s3_url"]
        file_name = s3_url.split("/")[-1]  # Extract file name from S3 URL

        try:
            # Delete file from S3
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file_name)
            logging.info(f"Deleted S3 file: {file_name}")
        except Exception as e:
            logging.info(f"Failed to delete S3 file {file_name}: {e}")
            continue

        try:
            # Remove s3_url from MongoDB document
            collection.update_one({"_id": article["_id"]}, {"$unset": {"s3_url": ""}})
            logging.info(f"Removed s3_url from MongoDB for: {article['_id']}")
        except Exception as e:
            logging.info(f"Failed to update MongoDB document {article['_id']}: {e}")


def process_and_store_articles(start_date, end_date):
    """Extract a news URL, scrape content, store in S3, and update MongoDB."""
    # Convert to datetime format
    num = 0
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    articles = collection.find({"publishedAt": {"$gte": start_dt, "$lte": end_dt}, 
                                "s3_url": {"$exists": False}})  # Process only articles without S3 URL

    for article in articles:
        url = article["url"]
        article_id = str(article["_id"])  # Use MongoDB ObjectId as filename
        print(url)
        
        logging.info(f"Processing article: {url}")

        # Scrape article content
        full_text = extract_news_content(url)
        if not full_text or len(full_text) < 1000:
            logging.info(f"Failed to scrape article content: {url}")
            continue
        
        # Upload to S3
        s3_url = load_to_s3(full_text, article_id)
        if not s3_url:
            logging.info(f"Failed to store article in S3: {url}")
            continue
        
        collection.update_one(
            {"_id": article["_id"]}, 
            {"$set": {"s3_url": s3_url}}
        )

        num += 1

        logging.info(f"Article processed and stored in S3: {s3_url}")

    logging.info(f"Processed and stored {num} articles in S3.")

# Run the pipeline
# delete_s3_and_mongo("2025-02-01", "2025-02-06")
process_and_store_articles("2025-02-01", "2025-02-06")