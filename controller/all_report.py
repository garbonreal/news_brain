from flask import Blueprint, request, session, redirect, make_response, render_template
from model import AllReport, Report, WebsiteUrl

# corresponding to the route that displays the weekly report

all_report = Blueprint('all_report', __name__, template_folder='templates')


@all_report.route("/")
def index():
    if session.get('isLogin') != 'true':
        from_url = request.args.get('from')
        if from_url is None:
            from_url = '/'
        return render_template('login.html', from_url=from_url)

    # query the database
    auth = session.get('username')
    weekly_report = AllReport.get_report_by_auth(auth)
    weekly_report = list(weekly_report)
    return render_template("index.html", weekly_report=weekly_report, len=len(weekly_report))


# create a new weekly report
@all_report.route("/create_weekly_report", methods=["GET", "POST"])
def create():
    if session.get('isLogin') != 'true':
        from_url = request.args.get('from')
        if from_url is None:
            from_url = '/'
        return render_template('login.html', from_url=from_url)

    auth = session.get('username')
    # create a table for the weekly report
    table_name = Report.create_weekly_report_table(auth)
    # add the summary report to all_report
    AllReport.add_all_report(table_name, auth)
    state = AllReport.get_search_state(table_name)
    query = {
        "table_name": table_name,
        "report_state": state,
        "page_count": 0,
        "curr_page": 0
    }
    return render_template("search.html", query=query)


# delete weekly report data from the summary table
@all_report.route("/delete_report", methods=["GET", "POST"])
def delete_report():
    # get request parameters
    data = request.get_json()
    table_name = data["table_name"]
    AllReport.delete_summary_report(table_name)
    Report.delete_weekly_report_table(table_name)
    return "success"