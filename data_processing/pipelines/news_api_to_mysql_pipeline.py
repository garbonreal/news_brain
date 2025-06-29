import os
from dotenv import load_dotenv
from newsapi.newsapi_client import NewsApiClient
import pandas as pd
from datetime import date, datetime, timedelta
import pymysql
import logging
from data_processing.utils.db_s3_utils import get_news_api_key


# configuration log
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s") 

# prepare configuration
load_dotenv(override=False)

api_key = os.getenv("NEWS_API_KEY")

MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_PORT = int(os.getenv('MYSQL_PORT'))
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')

MYSQL_CONNECTION_PARAMETERS = {
		'host': MYSQL_HOST,
		'port': MYSQL_PORT,
		'user': MYSQL_USER,
		'password': MYSQL_PASSWORD,
		'database': MYSQL_DATABASE,
		'charset': 'utf8mb4'
}


def fetch_news_data(
	api_key,
	country="us",
	category="business",
	source=None,
	q=None,
	page_size=50,
	page=1
):
	""" Fetch news data from News API. """

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
		total_results = top_headlines.get('totalResults', 0)  # 避免 KeyError
		articles = top_headlines.get('articles', [])  # 确保 articles 为空列表
		return total_results, articles
	else:
		logging.error(f"News API request failed: {top_headlines}")
		return 0, []


def transform_news_data(articles):
	""" Transform and filter the articles data. """
	# prepare date
	today = date.today()
	last_week = today - timedelta(days = 7)

	df = pd.DataFrame(articles, columns=['source', 'title', 'publishedAt', 'author', 'url'])
	df['source'] = df['source'].apply(lambda x: x['name'] if pd.notna(x) and 'name' in x else None)
	df['publishedAt'] = pd.to_datetime(df['publishedAt'])
	df["title"] = df["title"].apply(lambda x: x.split(" - ")[0])
	df = df[(df['publishedAt'].dt.date >= last_week)]
	
	return df.copy()


def load_news_data(df):
	""" Load news data from file. """
	connection = pymysql.connect(**MYSQL_CONNECTION_PARAMETERS)
	cursor = connection.cursor()
	num = 0
	
	title = df['title']
	time = df['publishedAt']
	link = df['url']
	source = df['source']
	
	sql = '''REPLACE INTO `website_link` (title, url, source, time) VALUES (%s, %s, %s, %s)'''
	
	try:
		for _, row in df.iterrows():
				title = row['title']
				time = row['publishedAt']
				link = row['url']
				source = row['source']
				cursor.execute(sql, (title, link, source, time))
				connection.commit()
				num += 1
	except Exception as e:
		connection.rollback()
		logging.error("Failed to load news data.exc_info=%s", e)
	finally:
		logging.info("Successfully loaded news number: %s", num)
		cursor.close()
		connection.close()


def process_news_mysql(start_date, end_date):
    """
    Fetch, filter, transform, and load news data within the given date range.
    :param start_date: Start date (inclusive) in 'YYYY-MM-DD' format
    :param end_date: End date (inclusive) in 'YYYY-MM-DD' format
    """

    total_results, articles = fetch_news_data(get_news_api_key())
    
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


total_results, articles = fetch_news_data(api_key)
if total_results == 0:
	logging.error("No news data fetched.")
else:
	logging.info(f"Successfully fetched {total_results} news articles.")
	df = transform_news_data(articles)
	load_news_data(df)
	