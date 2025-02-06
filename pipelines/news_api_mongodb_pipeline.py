import os
from dotenv import load_dotenv
from newsapi.newsapi_client import NewsApiClient
import pandas as pd
from datetime import date, timedelta
from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv(override=False)

# Fetch News API Key
api_key = os.getenv("NEWS_API_KEY")

# MongoDB Configuration
MONGO_HOST = os.getenv('MONGO_HOST')  # Default to localhost
MONGO_PORT = int(os.getenv('MONGO_PORT'))  # Default MongoDB port
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_DB = os.getenv('MONGO_DATABASE')

MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"
print(MONGO_URI)

try:
    # Connect to MongoDB
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)  # Timeout in 5 seconds
    print(client.server_info())
    db = client["news_db"]
    collection = db["news_articles"]  # Target collection
    logging.info("Successfully connected to MongoDB.")
except Exception as e:
    logging.error("MongoDB connection failed due to: %s", e)

def fetch_news_data(
    api_key,
    country="us",
    category="business",
    source=None,
    q=None,
    page_size=100,
    page=1
):
    """ Fetch news data from NewsAPI """

    newsapi = NewsApiClient(api_key=api_key)
    params = {
        "country": country,
        "category": category,
        "page_size": page_size,
        "page": page
    }

    if q is not None:
        params["q"] = q
    if source is not None:
        params["sources"] = source

    top_headlines = newsapi.get_top_headlines(**params)

    status = top_headlines.get('status')
    if status == 'ok':
        total_results = top_headlines.get('totalResults', 0)  # Avoid KeyError
        articles = top_headlines.get('articles', [])  # Ensure articles is a list
        return total_results, articles
    else:
        logging.error(f"News API request failed: {top_headlines}")
        return 0, []


def transform_news_data(articles):
    """ Process and transform news data before storing in MongoDB """
    today = date.today()
    last_week = today - timedelta(days=7)

    df = pd.DataFrame(articles, columns=['source', 'title', 'publishedAt', 'author', 'url'])
    
    df['source'] = df['source'].apply(lambda x: x['name'] if pd.notna(x) and 'name' in x else None)
    df['publishedAt'] = pd.to_datetime(df['publishedAt'])
    df["title"] = df["title"].apply(lambda x: x.split(" - ")[0] if isinstance(x, str) else x)
    
    # Filter articles from the last 7 days
    df = df[df['publishedAt'].dt.date >= last_week]

    return df.copy()


def load_news_data(df):
    """ Load processed news data into MongoDB """
    num = 0
    news_list = df.to_dict(orient="records")  # Convert DataFrame to list of dictionaries

    try:
        # Insert or update data (using URL as a unique identifier)
        for news in news_list:
            result = collection.update_one(
                {"url": news["url"]},  # Unique identifier
                {"$set": news},  # Update if exists, insert otherwise
                upsert=True
            )
            num += 1
        logging.info(f"Successfully stored {num} news articles in MongoDB.")
    except Exception as e:
        logging.error("Failed to load news data: %s", e)


# Execution Flow
total_results, articles = fetch_news_data(api_key)
if total_results == 0:
    logging.error("No news data fetched.")
else:
    logging.info(f"Successfully fetched {total_results} news articles.")
    df = transform_news_data(articles)
    load_news_data(df)
