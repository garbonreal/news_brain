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
    global progress
    progress = 10
    spider_names = ['c114', 'cace', 'ccia', 'ccidcom',
                    'cena', 'ciia', 'cinic', 'cnii',
                    'cto51', 'cww', 'echinagov', 'gkzhan',
                    'isc', 'sicgov', 'beijinggov',
                    'bjfgw', 'cqdsjj', 'cqjjxxw', 'cqkjj',
                    'cskjj', 'gzkjj', 'hzkjj', 'njkjj',
                    'shgov', 'suzhougxj', 'suzhoukjj', 'szgxj',
                    'szstic', 'whjxj', 'chinagazelle']

    futures = []
    with ThreadPoolExecutor() as executor:
        for spider_name in spider_names:
            future = executor.submit(run_spider, spider_name)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            progress += 3
            print('Progress: {}%'.format(progress))
            sse.publish({'progress': progress}, type='progress')

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

if __name__ == "__main__":
    app.app_context().push()
    init_db(app)

    app.register_blueprint(auth)
    app.register_blueprint(all_report)
    app.register_blueprint(website_url)
    app.register_blueprint(report)
    app.register_blueprint(profile)
    app.register_blueprint(sse, url_prefix='/stream')
    app.run(debug=True, host="0.0.0.0", port=5000)
