from .database import Base, db, conn
import datetime


class AllReport(db.Model):
    __tablename__ = 'all_report'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 表格名
    title = db.Column(db.String(100), nullable=False)
    # 创建时间
    create_time = db.Column(db.DateTime, nullable=False)
    # 负责人
    principal = db.Column(db.String(20), nullable=False)
    # 进入初选的新闻个数
    news_count = db.Column(db.Integer, nullable=False)
    # 进入周报的新闻个数
    weekly_report_count = db.Column(db.Integer, nullable=False)
    # 是否发布 两种状态：已发布、未发布
    is_publish = db.Column(db.String(20), nullable=False)
    # 是否编辑过总结 两种状态：已编辑、未编辑
    is_edit = db.Column(db.String(20), nullable=False)
    # 总结标题
    content_title = db.Column(db.String(100))
    # 总结内容
    content = db.Column(db.Text)
    # 周报名称
    weekly_report_name = db.Column(db.String(100))
    # 搜索开始时间
    start_time = db.Column(db.DateTime)
    # 搜索结束时间
    end_time = db.Column(db.DateTime)
    # 搜索关键词
    search_key = db.Column(db.String(100))
    # 过滤关键词
    filter_key = db.Column(db.String(100))
    # 当前页数
    curr_page = db.Column(db.Integer)
    # 总页数
    page_count = db.Column(db.Integer)
    # 新闻总条数
    length = db.Column(db.Integer)
    # 已初选新闻条数
    first_filter_length = db.Column(db.Integer)

    # 编辑周报评论
    @staticmethod
    def edit_comment(table_name, headline, content):
        all_report = AllReport.query.filter(AllReport.title == table_name).first()
        all_report.content_title = headline
        all_report.content = content
        db.session.commit()

    # 获取周报数据搜索状态
    @staticmethod
    def get_search_state(table_name):
        all_report = AllReport.query.filter(AllReport.title == table_name).first()
        return all_report

    # 更新周报数据搜索状态
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

    # 获得表名
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
                               weekly_report_count=0, is_publish='未发布', is_edit='未编辑',
                               weekly_report_name='数字经济与科技创新动态（未编辑）')
        db.session.add(all_report)
        db.session.commit()
        return "新周报草稿创建成功"

    # 改变周报名称
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

    # 总表中的周报改为已发布
    @staticmethod
    def report_edited(table_name):
        all_report = AllReport.query.filter(AllReport.title == table_name).first()
        all_report.is_publish = '已发布'
        db.session.commit()

    # 更改总表中的信息
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
