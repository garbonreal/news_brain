from .database import Base, db, conn
import datetime


class AllReport(db.Model):
    __tablename__ = 'all_report'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # table name
    title = db.Column(db.String(100), nullable=False)
    # creation time
    create_time = db.Column(db.DateTime, nullable=False)
    # person in charge
    principal = db.Column(db.String(20), nullable=False)
    # number of news articles entering first select
    news_count = db.Column(db.Integer, nullable=False)
    # number of news articles entering the weekly report
    weekly_report_count = db.Column(db.Integer, nullable=False)
    # publication status: "published" or "unpublished"
    is_publish = db.Column(db.String(20), nullable=False)
    # summary edit status: "edited" or "unedited"
    is_edit = db.Column(db.String(20), nullable=False)
    # summary title
    content_title = db.Column(db.String(100))
    # summary content
    content = db.Column(db.Text)
    # weekly report name
    weekly_report_name = db.Column(db.String(100))
    # search start time
    start_time = db.Column(db.DateTime)
    # search end time
    end_time = db.Column(db.DateTime)
    # search keywords
    search_key = db.Column(db.String(100))
    # filter keywords
    filter_key = db.Column(db.String(100))
    # current page number
    curr_page = db.Column(db.Integer)
    # total number of pages
    page_count = db.Column(db.Integer)
    # total number of news articles
    length = db.Column(db.Integer)
    # number of news articles that passed first select
    first_filter_length = db.Column(db.Integer)

    # edit comment
    @staticmethod
    def edit_comment(table_name, headline, content):
        all_report = AllReport.query.filter(AllReport.title == table_name).first()
        all_report.content_title = headline
        all_report.content = content
        db.session.commit()

    # get the search status of weekly report data
    @staticmethod
    def get_search_state(table_name):
        all_report = AllReport.query.filter(AllReport.title == table_name).first()
        return all_report

    # update the status of weekly report data search
    @staticmethod
    def update_search_state(table_name, start_time, end_time, search_key, filter_key, curr_page, page_count, length):
        all_report = AllReport.query.filter(AllReport.title == table_name).first()
        all_report.start_time = start_time
        all_report.end_time = end_time
        all_report.search_key = search_key
        all_report.filter_key = filter_key
        all_report.curr_page = curr_page
        all_report.page_count = page_count
        all_report.length = length
        db.session.commit()

    # get table name
    @staticmethod
    def get_table_name(table_name):
        all_report = AllReport.query.filter(AllReport.title == table_name).first()
        return all_report.weekly_report_name

    @staticmethod
    def count_report_by_auth(auth):
        all_report = AllReport.query.filter_by(principal=auth).all()
        return len(all_report)

    @staticmethod
    def get_all_report():
        all_report = AllReport.query.filter_by().all()
        return all_report

    @staticmethod
    def add_all_report(title, auth):
        table_time = title.replace('weekly_report_', '').replace('_'+auth, '')
        time = datetime.datetime.strptime(table_time, "%Y%m%d-%H%M%S")
        all_report = AllReport(title=title, create_time=time, principal=auth, news_count=0,
                               weekly_report_count=0, is_publish='unpublished', is_edit='unedited',
                               weekly_report_name='Weekly report (unedited)')
        db.session.add(all_report)
        db.session.commit()
        return "New weekly report draft created successfully"

    # Change the name of the weekly report
    @staticmethod
    def change_weekly_report_name(table_name, weekly_report_name):
        all_report = AllReport.query.filter(AllReport.title == table_name).first()
        all_report.weekly_report_name = weekly_report_name
        db.session.commit()

    @staticmethod
    def get_report_by_auth(auth):
        all_report = AllReport.query.filter_by(principal=auth).all()
        return all_report

    # 删除总表中的周报
    @staticmethod
    def delete_summary_report(table_name):
        report = AllReport.query.filter(AllReport.title == table_name).first()
        db.session.delete(report)
        db.session.commit()

    # The weekly report in the summary table is changed to published
    @staticmethod
    def report_edited(table_name):
        all_report = AllReport.query.filter(AllReport.title == table_name).first()
        all_report.is_publish = 'published'
        db.session.commit()

    # Change the information in the summary table
    @staticmethod
    def change_report_status(table_name):
        all_report = AllReport.query.filter(AllReport.title == table_name).first()
        curs = conn.cursor()
        sql_1 = "select count(*) from `%s` where `is_first_filter`= 1" % table_name
        sql_2 = "select count(*) from `%s` where `is_second_filter`= 1" % table_name
        try:
            curs.execute(sql_1)
            data_first = curs.fetchone()
            curs.execute(sql_2)
            data_second = curs.fetchone()
            curs.close()
            conn.close()
            all_report.news_count = data_first[0]
            all_report.weekly_report_count = data_second[0]
            print(all_report.news_count, all_report.weekly_report_count)
            db.session.commit()
        except Exception as e:
            print(e)
            conn.rollback()
            curs.close()
