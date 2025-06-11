from flask import Flask, session, request, render_template, redirect, send_from_directory, jsonify, Response
import config
from common import save_session, type_to_str, startsWithList, get_summary
from controller import auth, all_report, website_url, report, profile
from model import User, AllReport, WebsiteUrl, Report, init_db
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import subprocess
from concurrent.futures import ThreadPoolExecutor
import time
from flask_sse import sse
from threading import Lock
import concurrent.futures
import datetime
from data_processing import process_news_data, process_and_store_articles, analyze_news_data, process_news_mysql


# __name__: model name
app = Flask(__name__)
# load configuration
app.config.from_object(config)

progress = 0
progress_lock = Lock()

# with app.app_context():
#     db.create_all()


# routing: used to define individual web pages within a website
# defining a route: use the app.route() decorator to define routes
# accessing a route: visit the corresponding URL in a browser
# route return value: the return value of the associated view function is sent as the response body to the browser
@app.before_request
def auto_login():
    """automated login using cookie"""
    if session.get('isLogin') is None:
        username = request.cookies.get('username')
        password = request.cookies.get('password')
        if username is not None and password is not None:
            result = User.find_by_username(username)
            if len(result) == 1 and password == result[0].password:
                save_session(result[0])


@app.before_request
def verify_login():
    """verify requests that need login"""
    # ignore pages don't need login
    if not startsWithList(request.path, ['/profile']):
        return
    if session.get('isLogin') is None:  # redirect to login page
        return redirect('/login?from=' + request.path)


@app.route('/about')
def about():
    return render_template('about.html')


def run_spider(spider_name):
    global progress
    cmd = ['scrapy', 'crawl', spider_name]
    subprocess.run(cmd)


@app.route('/start_scrapy', methods=['POST', 'GET'])
def start_scrapy():
    today = datetime.datetime.utcnow().date()
    start_date = str(today - datetime.timedelta(days=2))
    end_date = str(today - datetime.timedelta(days=1))

    print(f"[INFO] Running news pipeline from {start_date} to {end_date}")
    process_news_mysql(start_date=start_date, end_date=end_date)

    # print("[1/3] Fetching news from API...")
    # process_news_data(start_date=start_date, end_date=end_date)

    # print("[2/3] Scraping news and storing to S3...")
    # process_and_store_articles(start_date=start_date, end_date=end_date)

    # print("[3/3] Analyzing news and storing results to MongoDB...")
    # analyze_news_data(start_date=start_date, end_date=end_date)

    # print("[DONE] News pipeline finished successfully.")

    return Response(status=204)


@app.route('/update_data', methods=['POST', 'GET'])
def update_data():
    for i in range(11):
        time.sleep(1)
        progress = (i + 1) * 10
        print('Progress: {}%'.format(progress))
        sse.publish({'progress': progress}, type='progress')
    return Response(status=204)


# 1. debug mode: when enabled, the server will automatically restart after code modifications
# 2. host parameter: the default value is 0.0.0.0, allowing external access via the local machine's IP
# 3. port parameter: the default value is 5000, specifying the port number

with app.app_context():
    init_db(app)

app.register_blueprint(auth)
app.register_blueprint(all_report)
app.register_blueprint(website_url)
app.register_blueprint(report)
app.register_blueprint(profile)
app.register_blueprint(sse, url_prefix='/stream')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
