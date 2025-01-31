from flask import Blueprint, request, session, redirect, make_response, render_template, send_from_directory
from model import AllReport, Report, WebsiteUrl
from common import type_map
from common import get_summary
from docxtpl import DocxTemplate
from datetime import datetime

# 对应了新闻编辑页面的路由


report = Blueprint('report', __name__, template_folder='templates')


# 进入周报编辑
@report.route("/edit_weekly_report/<table_name>")
def edit_weekly_report(table_name):
    news_link = []
    first_filter_news = Report.get_weekly_report_data(table_name)
    first_filter_news = list(first_filter_news)
    for news in first_filter_news:
        news_id = news[7]
        news_link.append(WebsiteUrl.get_news_by_id(news_id))
    lists = zip(news_link, first_filter_news)
    state = AllReport.get_search_state(table_name)
    tags = Report.get_tag_num(table_name)
    length = Report.get_weekly_report_data_count(table_name)
    return render_template("edit_report.html",
                           news_link=lists,
                           tags=tags,
                           table_name=table_name,
                           report_state=state,
                           length=length)


# 周报草稿中添加初选新闻
@report.route("/add_news", methods=["GET", "POST"])
def add_news():
    # 获取请求参数
    data = request.get_json()
    news_id = data["news_id"]
    table_name = data["table_name"]
    print(news_id, table_name)
    bton = data["bton"]
    if bton == "入选周报":
        Report.add_selected_news_to_weekly_report(table_name, news_id)
    if bton == "取消加入":
        Report.delete_selected_news_to_weekly_report(table_name, news_id)
    AllReport.change_report_status(table_name)
    return "success"


# 进入编辑周报新闻摘要界面
@report.route("/editor_news", methods=["GET", "POST"])
def editor_news():
    # 获取请求参数
    table_name = request.form.get("table_name")
    news_id = request.form.get("news_id")
    print(table_name, news_id)
    news_data = WebsiteUrl.get_news_by_id(news_id)
    news_title = news_data.title
    news_link = news_data.url
    data = Report.get_news_content(table_name, news_id)[0]
    news_headline = data[0]
    news_content = data[1]
    if data[1] is None:
        news_content = get_summary(news_link)
        # 把文本转换为 JavaScript 字符串的 Unicode 转义格式，以确保它不会破坏 JavaScript 代码的结构
        news_content = news_content.encode("unicode_escape").decode()
    news_tag = data[2]
    print(news_content)
    return render_template("editor.html",
                           msg_type=type_map,
                           news_tag=news_tag,
                           table_name=table_name,
                           news_id=news_id,
                           news_title=news_title,
                           news_link=news_link,
                           news_headline=news_headline,
                           news_content=news_content)


# 进入编辑周报评论界面
@report.route("/editor_comment/<table_name>", methods=["GET", "POST"])
def editor_comment(table_name):
    # 获取请求参数
    state = AllReport.get_search_state(table_name)
    comment_headline = state.content_title
    comment_content = state.content
    tag = '数经评论'
    return render_template("editor_comment.html",
                           msg_type=type_map,
                           tag=tag,
                           table_name=table_name,
                           comment_headline=comment_headline,
                           comment_content=comment_content)


# 将编辑好的摘要储存到数据库
@report.route('/get_comment', methods=['POST', 'PUT'])
def get_comment():
    headline = request.form.get('headline')
    content = request.form.get('content')
    content = content.replace('<p>', '').replace('</p>', '').replace('<br>', '').replace('</br>', '')
    table_name = request.form.get('table_name')
    print(headline, content, table_name)
    # 进行相应表单的修改
    AllReport.edit_comment(table_name, headline, content)
    return 'success'


# 将编辑好的评论储存到数据库
@report.route('/get_message', methods=['POST', 'PUT'])
def get_message():
    headline = request.form.get('headline')
    content = request.form.get('content')
    content = content.replace('<p>', '').replace('</p>', '').replace('<br>', '').replace('</br>', '')
    table_name = request.form.get('table_name')
    news_id = request.form.get('news_id')
    news_type = request.form.get('news_type')
    print(headline, content, table_name, news_id, news_type)
    # 进行相应表单的修改
    Report.edit_news_summary(table_name, news_id, headline, content, news_type)
    return 'success'


# 展示编辑好的周报
@report.route("/show_report/<table_name>", methods=["GET", "POST"])
def show_report(table_name):
    # 查询数据库
    second_filter_news = Report.get_weekly_report_selected_data(table_name)
    second_filter_news = list(second_filter_news)
    state = AllReport.get_search_state(table_name)
    # 初始化字典
    type_occurrence = []
    # 遍历新闻列表，检查每个类型是否出现
    for news in second_filter_news:
        if news[9] not in type_occurrence and news[9] is not None:
            type_occurrence.append(news[9])
    print(type_occurrence)

    return render_template("show_report.html",
                           news_type=type_map,
                           type_occurrence=type_occurrence,
                           second_filter_news=second_filter_news,
                           table_name=table_name,
                           report_state=state)


# 导出周报
@report.route("/export_report/<table_name>", methods=["GET", "POST"])
def export_report(table_name):
    tpl = DocxTemplate('./data/template_report.docx')
    AllReport.report_edited(table_name)
    # 查询数据库
    context = {
        'tags': [],
        'title': [],
        'data': [],
    }
    second_filter_news = Report.get_weekly_report_selected_data(table_name)

    state = AllReport.get_search_state(table_name)
    date_obj = state.create_time
    y = str(date_obj.year)
    m = str(date_obj.month).zfill(2).lstrip('0')
    d = str(date_obj.day).zfill(2).lstrip('0')
    context['time'] = {'y': y, 'm': m, 'd': d}

    if state.content_title is not None and state.content is not None:
        context['comment'] = {
            'headline': state.content_title,
            'content': state.content,
        }

    for t in type_map:
        temp = {
            'type': t,
            'news': []
        }
        for news in second_filter_news:
            if news[9] == t and news[6] is not None:
                temp['news'].append({
                    'title': news[1],
                    'headline': news[8],
                    'content': news[6],
                    'source': news[10],
                })
        if temp['news']:
            context['data'].append(temp)
            context['tags'].append(t)
    index = {}
    for t in type_map:
        index[t] = 2
    for news in second_filter_news:
        if news[9] is not None and index[news[9]] > 0 and news[6] is not None:
            context['title'].append(news[8])
            index[news[9]] -= 1

    print(context)

    tpl.render(context)
    path = AllReport.get_table_name(table_name) + '.docx'
    path1 = './data/' + path
    tpl.save(path1)

    return send_from_directory('./data', path)

# def export_report(table_name):
#     # 获取请求参数
#     AllReport.report_edited(table_name)
#
#     # 查询数据库
#     second_filter_news = Report.get_weekly_report_selected_data(table_name)
#
#     html = ""
#     if second_filter_news:
#         for type in type_map:
#             html += "<h2 style='text-align: center; color: black;'>" + type + "</h2>"
#             for news in second_filter_news:
#                 if news[9] == type:
#                     if news[8]:
#                         html += "<h3>" + news[8] + "</h3>"
#                     else:
#                         html += "<h3>" + news[1] + "</h3>"
#                     if news[6]:
#                         html += "<div>" + news[6] + "</div>"
#         html += "<h2 style='text-align: center; color: black;'>" + "无标签" + "</h2>"
#         for news in second_filter_news:
#             if news[9] is None:
#                 if news[8]:
#                     html += "<h3>" + news[8] + "</h3>"
#                 else:
#                     html += "<h3>" + news[1] + "</h3>"
#                 if news[6]:
#                     html += "<div>" + news[6] + "</div>"
#     print(html)
#
#     # Write HTML String to file.html
#     with open("./data/" + table_name + ".html", "w", encoding="utf-8") as file:
#         file.write(html)
#
#     pypandoc.convert_file("./data/" + table_name + ".html", 'docx',
#                           encoding='gbk',
#                           outputfile="./data/" + table_name + ".docx")
#
#     return send_from_directory("./data/", table_name + ".docx")
