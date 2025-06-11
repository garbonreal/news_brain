from datetime import datetime
from data_processing.utils.sentiment_analysis import get_sentiment, init_sentiment_analysis
from data_processing.utils.news_summary import get_news_summary, init_summarization_model
import logging
from data_processing.utils.db_s3_utils import get_mongo_client, get_s3_client, get_bucket_name


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def read_text_from_s3(s3_url, s3_client, bucket_name):
    """
    Reads and returns the text content from an S3 file.
    """
    filename = s3_url.split("/")[-1]
    print(filename)
    obj = s3_client.get_object(Bucket=bucket_name, Key=filename)
    return obj["Body"].read().decode("utf-8")


def analyze_news_data(start_date, end_date):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    query = {
        "publishedAt": {"$gte": start_dt, "$lte": end_dt},
        "s3_url": {"$exists": True},
        "summary": {"$exists": False}
    }

    summary_model, summary_tokenizer = init_summarization_model()
    sentiment_model, sentiment_tokenizer = init_sentiment_analysis()

    s3_client = get_s3_client()
    bucket_name = get_bucket_name()

    client = get_mongo_client()
    if client is None:
        return
    db = client["news_db"]
    collection = db["news_articles"]

    news_items = collection.find(query)

    for news in news_items:
        news_id = news["_id"]
        s3_url = news["s3_url"]

        text = read_text_from_s3(s3_url, s3_client, bucket_name)
        if not text:
            continue

        # summarize news and analyze sentiment
        try:
            summary = get_news_summary(text, summary_model, summary_tokenizer, method="sliding_window")
        except Exception as e:
            logging.error(f"Failed to generate summary for news ID {news_id}: {e}")
            summary = None

        try:
            polarity, sentiment = get_sentiment(text, sentiment_model, sentiment_tokenizer)
        except Exception as e:
            logging.error(f"Failed to analyze sentiment for news ID {news_id}: {e}")
            polarity, sentiment = None, None

        update_data = {"$set": {}}
        if summary is not None:
            update_data["$set"]["summary"] = summary
        if sentiment is not None:
            update_data["$set"]["sentiment"] = sentiment
        if polarity is not None:
            update_data["$set"]["polarity"] = float(polarity)

        if update_data["$set"]:
            collection.update_one({"_id": news_id}, update_data)
            logging.info(f"News with ID {news_id} processed successfully.")
    
    client.close()
        
        
if __name__ == "__main__":
    start_date = "2025-02-11"
    end_date = "2025-02-12"
    analyze_news_data(start_date, end_date)