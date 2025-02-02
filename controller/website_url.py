from flask import Blueprint, request, session, redirect, make_response, render_template
from model import AllReport, Report, WebsiteUrl
from sqlalchemy import or_, and_
from math import ceil
import re

# the route of the news filtering page
website_url = Blueprint('website_url', __name__, template_folder='templates')


# go back to the first filter page
@website_url.route("/filter_weekly_report/<table_name>")
def filter_weekly_report(table_name):
    state = AllReport.get_search_state(table_name)
    caught_num = Report.get_weekly_report_data_count(table_name)
    start_time = state.start_time
    end_time = state.end_time
    report_name = state.weekly_report_name
    report_auth = state.principal
    report_time = state.create_time.strftime('%Y-%m-%d %H:%M:%S')
    if state.start_time is None or state.end_time is None:
        query = {
            "table_name": table_name,
            "report_name": report_name,
            "report_auth": report_auth,
            "report_time": report_time,
            "page_count": 0,
            "curr_page": 0,
            "caught_num": 0
        }
        return render_template("search.html", query=query)

    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

    if state.search_key is None:
        key_list = []
    else:
        key_list = state.search_key.split(" ")
        key_list = [k for k in key_list if k != "" and k != " "]

    if state.filter_key is None:
        bad_key_list = []
    else:
        bad_key_list = state.filter_key.split(" ")
        bad_key_list = [b for b in bad_key_list if b != "" and b != " "]

    news_link = []
    if state.start_time != 'undefined':
        # Query the database by time range
        r_news_link = WebsiteUrl.get_news_by_date(state.start_time, state.end_time)

        # Filter news that contains any keyword in the key_list in the title
        filters = []
        for k in key_list:
            filters.append(WebsiteUrl.title.contains(k))
        r_news_link = r_news_link.filter(or_(*filters))

        # Filter news that contains any keyword from bad_key_list in the title
        bad_filters = []
        for b in bad_key_list:
            bad_filters.append(WebsiteUrl.title.contains(b))
        r_news_link = r_news_link.filter(and_(*[~f for f in bad_filters]))

        # Edit returned data
        news_link = list(r_news_link)

    page_size = 50
    if len(news_link) > 0:
        news_link = [news_link[i:i + page_size] for i in range(0, len(news_link), page_size)][int(state.curr_page) - 1]

    query = {
        "start_time": start_time,
        "end_time": end_time,
        "table_name": table_name,
        "page_count": int(state.page_count),
        "length": int(state.length),
        "curr_page": int(state.curr_page),
        "key": state.search_key,
        "bad_key": state.filter_key,
        "caught_num": caught_num,
        "report_name": report_name,
        "report_auth": report_auth,
        "report_time": report_time
    }
    print(query)

    return render_template("search.html", news_link=news_link, query=query)


# News first round filtering
@website_url.route("/search_url", methods=["GET", "POST"])
def search_url():
    start_time = request.form.get("start_time")
    print(type(start_time))
    end_time = request.form.get("end_time")
    key = request.form.get("key")
    bad_key = request.form.get("bad_key")
    table_name = request.form.get("table_name")
    curr_page = request.form.get("curr_page")
    print(type(start_time))
    print(start_time, end_time, key, bad_key, table_name, curr_page)

    state = AllReport.get_search_state(table_name)
    report_name = state.weekly_report_name
    report_auth = state.principal
    report_time = state.create_time.strftime('%Y-%m-%d %H:%M:%S')
    if start_time is None or end_time is None:
        query = {
            "table_name": table_name,
            "page_count": 0,
            "curr_page": 0,
            "caught_num": 0,
            "report_name": report_name,
            "report_auth": report_auth,
            "report_time": report_time
        }
        return render_template("search.html", query=query)

    if "not edited" in report_name:
        report_name = report_name.split("(")[0]
        print(report_name)
        new_name = report_name + '(' + start_time.replace("-", "") + '-' + end_time.replace("-", "") + ')'
        AllReport.change_weekly_report_name(table_name, new_name)
        state = AllReport.get_search_state(table_name)

    caught_num = Report.get_weekly_report_data_count(table_name)

    # Added when end_time does not contain 23:59:59
    if end_time[-8:] != "23:59:59":
        end_time = end_time + " 23:59:59"

    page_size = 50
    news_link = []
    key_list = []
    bad_key_list = []
    length = 0
    page_count = 0

    if key is None:
        key = ""
    else:
        key_list = key.split(" ")
        key_list = [k for k in key_list if k != "" and k != " "]
    if bad_key is None:
        bad_key = ""
    else:
        bad_key_list = bad_key.split(" ")
        bad_key_list = [b for b in bad_key_list if b != "" and b != " "]

    if start_time != 'undefined':
        r_news_link = WebsiteUrl.get_news_by_date(start_time, end_time)

        filters = []
        for k in key_list:
            filters.append(WebsiteUrl.title.contains(k))
        r_news_link = r_news_link.filter(or_(*filters))

        bad_filters = []
        for b in bad_key_list:
            bad_filters.append(WebsiteUrl.title.contains(b))
        r_news_link = r_news_link.filter(and_(*[~f for f in bad_filters]))

        news_link = list(r_news_link)
        length = len(news_link)
        page_count = ceil(len(news_link) / page_size)

    if len(news_link) > 0:
        news_link = [news_link[i:i + page_size] for i in range(0, len(news_link), page_size)][int(curr_page) - 1]

    query = {
        "start_time": start_time,
        "end_time": end_time,
        "key": key,
        "bad_key": bad_key,
        "table_name": table_name,
        "curr_page": int(curr_page),
        "page_count": page_count,
        "length": length,
        "caught_num": caught_num,
        "report_name": report_name,
        "report_auth": report_auth,
        "report_time": report_time
    }
    print(query)

    AllReport.update_search_state(table_name, start_time, end_time, key, bad_key, curr_page, page_count, length)

    return render_template("search.html", news_link=news_link, query=query)


# add news to the weekly report summary
@website_url.route("/choose_news", methods=["GET", "POST"])
def choose_news():
    data = request.get_json()
    news_id = data["news_id"]
    table_name = data["table_name"]
    bton = data["bton"]
    print(news_id, table_name, bton)
    # query the database
    news_link = WebsiteUrl.get_news_by_id(news_id)
    title = news_link.title
    time = news_link.time
    source = news_link.source
    if bton == "first select":
        Report.add_filter_news_to_weekly_report(table_name, title, time, news_id, source)
    if bton == "cancel":
        Report.delete_filter_news_to_weekly_report(table_name, news_id)
    AllReport.change_report_status(table_name)
    return "success"
