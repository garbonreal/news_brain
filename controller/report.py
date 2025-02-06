from flask import Blueprint, request, session, redirect, make_response, render_template, send_from_directory
from model import AllReport, Report, WebsiteUrl
from common import type_map
from common import get_summary
# from docxtpl import DocxTemplate
from datetime import datetime
# import pypandoc

# the route of the news editing page
report = Blueprint('report', __name__, template_folder='templates')


# start editing the weekly report
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


# add first filter news to the weekly report
@report.route("/add_news", methods=["GET", "POST"])
def add_news():
    # get request parameters
    data = request.get_json()
    news_id = data["news_id"]
    table_name = data["table_name"]
    print(news_id, table_name)
    bton = data["bton"]
    if bton == "join weekly report":
        Report.add_selected_news_to_weekly_report(table_name, news_id)
    if bton == "unjoin":
        Report.delete_selected_news_to_weekly_report(table_name, news_id)
    AllReport.change_report_status(table_name)
    return "success"


# enter the news editing page
@report.route("/editor_news", methods=["GET", "POST"])
def editor_news():
    # get request parameters
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
        # A Unicode escape format that converts text to a JavaScript string to ensure that it does not break the structure of JavaScript code
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


# Enter the page for editing weekly comments
@report.route("/editor_comment/<table_name>", methods=["GET", "POST"])
def editor_comment(table_name):
    # get request parameters
    state = AllReport.get_search_state(table_name)
    comment_headline = state.content_title
    comment_content = state.content
    tag = 'Digital Economy Review'
    return render_template("editor_comment.html",
                           msg_type=type_map,
                           tag=tag,
                           table_name=table_name,
                           comment_headline=comment_headline,
                           comment_content=comment_content)


# store the edited news to the database
@report.route('/get_comment', methods=['POST', 'PUT'])
def get_comment():
    headline = request.form.get('headline')
    content = request.form.get('content')
    content = content.replace('<p>', '').replace('</p>', '').replace('<br>', '').replace('</br>', '')
    table_name = request.form.get('table_name')
    print(headline, content, table_name)
    # edit the corresponding table
    AllReport.edit_comment(table_name, headline, content)
    return 'success'


# store the edited news to the database
@report.route('/get_message', methods=['POST', 'PUT'])
def get_message():
    headline = request.form.get('headline')
    content = request.form.get('content')
    content = content.replace('<p>', '').replace('</p>', '').replace('<br>', '').replace('</br>', '')
    table_name = request.form.get('table_name')
    news_id = request.form.get('news_id')
    news_type = request.form.get('news_type')
    print(headline, content, table_name, news_id, news_type)
    # change the corresponding table
    Report.edit_news_summary(table_name, news_id, headline, content, news_type)
    return 'success'


# show the weekly report
@report.route("/show_report/<table_name>", methods=["GET", "POST"])
def show_report(table_name):
    # query the database
    second_filter_news = Report.get_weekly_report_selected_data(table_name)
    second_filter_news = list(second_filter_news)
    state = AllReport.get_search_state(table_name)
    # initialize the list of news types
    type_occurrence = []
    # loop through the news and add the news type to the list
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


# export the weekly report
@report.route("/export_report/<table_name>", methods=["GET", "POST"])
def export_report(table_name):
    # get the request parameters
    AllReport.report_edited(table_name)

    # query the database
    second_filter_news = Report.get_weekly_report_selected_data(table_name)

    html = ""
    if second_filter_news:
        for type in type_map:
            html += "<h2 style='text-align: center; color: black;'>" + type + "</h2>"
            for news in second_filter_news:
                if news[9] == type:
                    if news[8]:
                        html += "<h3>" + news[8] + "</h3>"
                    else:
                        html += "<h3>" + news[1] + "</h3>"
                    if news[6]:
                        html += "<div>" + news[6] + "</div>"
        html += "<h2 style='text-align: center; color: black;'>" + "no tags" + "</h2>"
        for news in second_filter_news:
            if news[9] is None:
                if news[8]:
                    html += "<h3>" + news[8] + "</h3>"
                else:
                    html += "<h3>" + news[1] + "</h3>"
                if news[6]:
                    html += "<div>" + news[6] + "</div>"
    print(html)

    # Write HTML String to file.html
    with open("./data/" + table_name + ".html", "w", encoding="utf-8") as file:
        file.write(html)

    # pypandoc.convert_file("./data/" + table_name + ".html", 'docx',
    #                       encoding='gbk',
    #                       outputfile="./data/" + table_name + ".docx")

    return send_from_directory("./data/", table_name + ".html")


# # export the weekly report
# @report.route("/export_report/<table_name>", methods=["GET", "POST"])
# def export_report(table_name):
#     tpl = DocxTemplate('./data/template_report.docx')
#     AllReport.report_edited(table_name)
#     # query the database
#     context = {
#         'tags': [],
#         'title': [],
#         'data': [],
#     }
#     second_filter_news = Report.get_weekly_report_selected_data(table_name)

#     state = AllReport.get_search_state(table_name)
#     date_obj = state.create_time
#     y = str(date_obj.year)
#     m = str(date_obj.month).zfill(2).lstrip('0')
#     d = str(date_obj.day).zfill(2).lstrip('0')
#     context['time'] = {'y': y, 'm': m, 'd': d}

#     if state.content_title is not None and state.content is not None:
#         context['comment'] = {
#             'headline': state.content_title,
#             'content': state.content,
#         }

#     for t in type_map:
#         temp = {
#             'type': t,
#             'news': []
#         }
#         for news in second_filter_news:
#             if news[9] == t and news[6] is not None:
#                 temp['news'].append({
#                     'title': news[1],
#                     'headline': news[8],
#                     'content': news[6],
#                     'source': news[10],
#                 })
#         if temp['news']:
#             context['data'].append(temp)
#             context['tags'].append(t)
#     index = {}
#     for t in type_map:
#         index[t] = 2
#     for news in second_filter_news:
#         if news[9] is not None and index[news[9]] > 0 and news[6] is not None:
#             context['title'].append(news[8])
#             index[news[9]] -= 1

#     print(context)

#     tpl.render(context)
#     path = AllReport.get_table_name(table_name) + '.docx'
#     path1 = './data/' + path
#     tpl.save(path1)

#     return send_from_directory('./data', path)