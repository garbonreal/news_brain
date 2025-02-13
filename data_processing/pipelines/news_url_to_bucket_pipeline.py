import newspaper
import logging
from datetime import datetime
from utils.db_s3_utils import get_mongo_client, get_s3_client, get_bucket_name


logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")


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


def delete_s3_and_mongo(start_date, end_date):
    """
    Deletes S3 files and removes s3_url from MongoDB for documents within a date range.
    
    :param start_date: Start date (YYYY-MM-DD)
    :param end_date: End date (YYYY-MM-DD)
    """
    # Convert to datetime format
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    s3_client = get_s3_client()
    bucket_name = get_bucket_name()

    client = get_mongo_client()
    if client is None:
        return
    db = client["news_db"]
    collection = db["news_articles"]

    # Find all documents within the date range
    articles = collection.find({"publishedAt": {"$gte": start_dt, "$lte": end_dt}, "s3_url": {"$exists": True}})

    for article in list(articles):
        s3_url = article["s3_url"]
        file_name = s3_url.split("/")[-1]  # Extract file name from S3 URL

        try:
            # Delete file from S3
            s3_client.delete_object(Bucket=bucket_name, Key=file_name)
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

    s3_client = get_s3_client()
    bucket_name = get_bucket_name()

    client = get_mongo_client()
    if client is None:
        return
    db = client["news_db"]
    collection = db["news_articles"]
    
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
        filename = f"{article_id}.txt"
        
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=filename,
                Body=full_text,
                ContentType="text/plain"
            )
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
        except Exception as e:
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
if __name__ == "__main__":
    process_and_store_articles("2025-02-11", "2025-02-12")