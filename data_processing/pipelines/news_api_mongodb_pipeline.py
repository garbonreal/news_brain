from newsapi.newsapi_client import NewsApiClient
import pandas as pd
from datetime import date, datetime, timedelta
import logging
from utils.db_s3_utils import get_mongo_client, get_news_api_key


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_top_news_data(
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

    client = get_mongo_client()
    if client is None:
        return
    
    db = client["news_db"]
    collection = db["news_articles"]  # Target collection

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
    
    client.close()


# Execution Flow
def process_news_data(start_date, end_date):
    """
    Fetch, filter, transform, and load news data within the given date range.
    :param start_date: Start date (inclusive) in 'YYYY-MM-DD' format
    :param end_date: End date (inclusive) in 'YYYY-MM-DD' format
    """

    total_results, articles = fetch_top_news_data(get_news_api_key())
    
    if total_results == 0:
        logging.error("No news data fetched.")
        return
    
    logging.info(f"Successfully fetched {total_results} news articles.")
    
    # Convert start_date and end_date to datetime objects
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Filter articles based on publishedAt date range
    filtered_articles = []
    for article in articles:
        published_at = article.get("publishedAt")
        if published_at:
            try:
                pub_date = datetime.strptime(published_at[:10], "%Y-%m-%d")  # Extract only YYYY-MM-DD
                if start_dt <= pub_date < end_dt:
                    filtered_articles.append(article)
            except ValueError:
                logging.warning(f"Invalid date format in article: {published_at}")
    
    if not filtered_articles:
        logging.warning("No articles found within the specified date range.")
        return
    
    df = transform_news_data(filtered_articles)
    load_news_data(df)
    logging.info(f"Successfully processed {len(filtered_articles)} filtered news articles.")


if __name__ == "__main__":
    process_news_data("2025-02-11", "2025-02-12")