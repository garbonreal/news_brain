from flask import Blueprint, request, session, redirect, make_response, render_template
from model import AllReport, Report, WebsiteUrl

# 对应了展示周报页面的路由

all_report = Blueprint('all_report', __name__, template_folder='templates')


@all_report.route("/")
def index():
    if session.get('isLogin') != 'true':
        from_url = request.args.get('from')
        if from_url is None:
            from_url = '/'
        return render_template('login.html', from_url=from_url)

    # 查询数据库
    auth = session.get('username')
    weekly_report = AllReport.get_report_by_auth(auth)
    weekly_report = list(weekly_report)
    return render_template("index.html", weekly_report=weekly_report, len=len(weekly_report))


# 创建周报
@all_report.route("/create_weekly_report", methods=["GET", "POST"])
def create():
    if session.get('isLogin') != 'true':
        from_url = request.args.get('from')
        if from_url is None:
            from_url = '/'
        return render_template('login.html', from_url=from_url)

    auth = session.get('username')
    # 为周报草稿创建表
    table_name = Report.create_weekly_report_table(auth)
    # 将周报草稿添加到整体记录中
    AllReport.add_all_report(table_name, auth)
    state = AllReport.get_search_state(table_name)
    query = {
        "table_name": table_name,
        "report_state": state,
        "page_count": 0,
        "curr_page": 0
    }
    return render_template("search.html", query=query)


# 删除总表中的周报数据
@all_report.route("/delete_report", methods=["GET", "POST"])
def delete_report():
    # 获取请求参数
    data = request.get_json()
    table_name = data["table_name"]
    AllReport.delete_summary_report(table_name)
    Report.delete_weekly_report_table(table_name)
    return "success"