from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
import datetime
import logging
from pipelines.news_api_mongodb_pipeline import process_news_data as fetch_news_data
from pipelines.news_url_to_bucket_pipeline import process_and_store_articles
from pipelines.ml_analysis_to_mongodb_pipeline import process_news_data as analyze_news_data


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime.datetime(2025, 2, 10),
    "retries": 2,
    "retry_delay": datetime.timedelta(minutes=5),
}

# Use UTC time, 5 hours ahead of Eastern time
# So run at 6:00 AM UTC, which is 1:00 AM Eastern time
dag = DAG(
    "news_pipeline",
    default_args=default_args,
    description="Daily news data pipeline",
    schedule_interval="0 6 * * *",
    catchup=False,
)

# When filtering by date, we need to adjust the date to Eastern time
# However, since we only need day granularity, we can just use the UTC date
# UTC time is one day ahead, so start_date is 2 days ago and end_date is 1 day ago
start_date = "{{ macros.ds_add(ds, -2) }}"
end_date = "{{ macros.ds_add(ds, -1) }}"

fetch_news_task = PythonOperator(
    task_id="fetch_news_from_api",
    python_callable=fetch_news_data,
    op_kwargs={"start_date": start_date, "end_date": end_date},
    dag=dag,
)

scrape_news_task = PythonOperator(
    task_id="scrape_news_and_store_s3",
    python_callable=process_and_store_articles,
    op_kwargs={"start_date": start_date, "end_date": end_date},
    dag=dag,
)

analyze_news_task = PythonOperator(
    task_id="news_analysis",
    python_callable=analyze_news_data,
    op_kwargs={"start_date": start_date, "end_date": end_date},
    dag=dag,
)

fetch_news_task >> scrape_news_task >> analyze_news_task
