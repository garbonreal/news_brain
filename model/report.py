from .database import Base, db, conn, engine
from sqlalchemy import text
import datetime
from common import type_map


class Report:

    # Get the content of the written news summary
    @ staticmethod
    def get_news_content(table_name, news_id):
        curs = conn.cursor()
        sql = "select headline,content,tag from `%s` where `news_id`='%s'" % (table_name, news_id)
        try:
            conn.ping(reconnect=True)
            curs.execute(sql)
            data = curs.fetchall()
            curs.close()
            conn.close()
            return data
        except Exception as e:
            print(e)
            conn.rollback()
            curs.close()

    # edit the news summary
    @staticmethod
    def edit_news_summary(table_name, news_id, headline, content, news_type):
        curs = conn.cursor()
        print(type_map[int(news_type)])
        if int(news_type) < 0:
            sql = "update `%s` set `headline` = '%s', `content` = '%s', `is_edit` = 1 where news_id = '%d'" \
                    % (table_name, headline, content, int(news_id))
        else:
            sql = "update `%s` set `headline` = '%s', `content` = '%s', `is_edit` = 1, " \
                  "`tag` = '%s' where news_id = '%d'" \
                    % (table_name, headline, content, type_map[int(news_type)], int(news_id))
        try:
            conn.ping(reconnect=True)
            curs.execute(sql)
            conn.commit()
        except Exception as e:
            print(e)
            conn.rollback()
        curs.close()

    @staticmethod
    def add_selected_news_to_weekly_report(table_name, news_id):
        with conn.cursor() as cursor:
            sql = "update `%s` set `is_second_filter` = 1 where news_id = '%d'" % (table_name, news_id)
            try:
                conn.ping(reconnect=True)
                cursor.execute(sql)
                conn.commit()
            except Exception as e:
                print(e)
                conn.rollback()

    @staticmethod
    def delete_selected_news_to_weekly_report(table_name, news_id):
        with conn.cursor() as cursor:
            sql = "update `%s` set `is_second_filter` = 0 where news_id = '%d'" % (table_name, news_id)
            try:
                conn.ping(reconnect=True)
                cursor.execute(sql)
                conn.commit()
            except Exception as e:
                print(e)
                conn.rollback()

    # Get the number of pieces of data in the draft weekly report
    @staticmethod
    def get_weekly_report_data_count(table_name):
        curs = conn.cursor()
        sql = "select count(*) from `%s`" % table_name
        try:
            conn.ping(reconnect=True)
            curs.execute(sql)
            data = curs.fetchone()
            conn.commit()
            curs.close()
            return data[0]
        except Exception as e:
            print(e)
            conn.rollback()
            curs.close()

    # Get all the data in the weekly report draft
    @staticmethod
    def get_weekly_report_data(table_name):
        curs = conn.cursor()
        sql = "select * from `%s` " % table_name
        try:
            conn.ping(reconnect=True)
            curs.execute(sql)
            data = curs.fetchall()
            conn.commit()
            curs.close()
            return data
        except Exception as e:
            print(e)
            conn.rollback()
            curs.close()

    # Get all the selected data in the weekly report draft
    @staticmethod
    def get_weekly_report_selected_data(table_name):
        curs = conn.cursor()
        sql = "select * from `%s` where `is_second_filter` = 1" % table_name
        try:
            conn.ping(reconnect=True)
            curs.execute(sql)
            data = curs.fetchall()
            conn.commit()
            curs.close()
            return data
        except Exception as e:
            print(e)
            conn.rollback()
            curs.close()

    # Add first select data to the weekly draft
    @staticmethod
    def add_filter_news_to_weekly_report(table_name, title, time, news_id, source):
        curs = conn.cursor()
        print(table_name)
        sql = "replace into `%s` (`title`, `time`, `is_first_filter`, `is_second_filter`, `is_edit`, `news_id`, `source`) \
               values('%s','%s','%d','%d','%d','%s','%s') " \
              "" % (table_name, title, time, 1, 0, 0, news_id, source)
        try:
            conn.ping(reconnect=True)
            curs.execute(sql)
            conn.commit()
        except Exception as e:
            print(e)
            conn.rollback()
        curs.close()
        return "News added successfully"

    # Remove first select data from weekly draft reports
    @staticmethod
    def delete_filter_news_to_weekly_report(table_name, news_id):
        curs = conn.cursor()
        print(table_name)
        sql = "delete from `%s` where news_id = '%s'" % (table_name, news_id)
        try:
            conn.ping(reconnect=True)
            curs.execute(sql)
            conn.commit()
        except Exception as e:
            print(e)
            conn.rollback()
        curs.close()
        return "News added successfully"

    # delete the weekly report database table
    @staticmethod
    def delete_weekly_report_table(table_name):
        curs = conn.cursor()
        # delete table
        sql = '''DROP TABLE `%s`''' % table_name
        try:
            conn.ping(reconnect=True)
            curs.execute(sql)
            conn.commit()
        except Exception as e:
            print(e)
            conn.rollback()
        print("Delete "+table_name+" successfully!")

    # Collect the number of tags in the total table
    @staticmethod
    def get_tag_num(table_name):
        curs = conn.cursor()
        # delete table
        sql = '''SELECT `tag`, COUNT(*) AS `tag_count` FROM `%s` GROUP BY `tag`''' % table_name
        try:
            conn.ping(reconnect=True)
            curs.execute(sql)
            data = curs.fetchall()
            conn.commit()
            conn.close()
            return data
        except Exception as e:
            print(e)
            conn.rollback()
            conn.close()

    # create a new weekly report database table
    @staticmethod
    def create_weekly_report_table(auth):
        curs = conn.cursor()
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        table_name = 'weekly_report_' + curr_time + "_" + auth
        # create table
        sql = '''CREATE TABLE `%s` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `title` VARCHAR(100) NOT NULL UNIQUE,
          `time` DATETIME NOT NULL,
          `is_first_filter` TINYINT(1) NOT NULL,
          `is_second_filter` TINYINT(1) NOT NULL,
          `is_edit` TINYINT(1) NOT NULL,
          `content` TEXT,
          `news_id` INT NOT NULL,
          `headline` TEXT,
          `tag` VARCHAR(100),
          `source` VARCHAR(100),
          PRIMARY KEY (`id`),
          FOREIGN KEY(news_id) REFERENCES website_link(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        ''' % table_name
        try:
            conn.ping(reconnect=True)
            curs.execute(sql)
            conn.commit()
        except Exception as e:
            print(e)
            conn.rollback()
        curs.close()
        return table_name