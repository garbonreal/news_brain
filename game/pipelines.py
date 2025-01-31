# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import datetime

from itemadapter import ItemAdapter

import pymysql
from scrapy.utils.project import get_project_settings


class MySQLStatsPipeline:
    def __init__(self):
        self.item_count = 0
        # 新建一个字典，存放每个不同来源的item数量
        self.source_count = {}

    def process_item(self, item, spider):
        # 获取item的来源
        source = item['source']
        # 如果该来源已经在字典中，数量加1
        if source in self.source_count:
            self.source_count[source] += 1
        else:
            self.source_count[source] = 1
        self.item_count += 1
        return item

    def close_spider(self, spider):
        curr_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 不覆盖写入
        with open('mysql_stats.log', 'a+', encoding='utf-8') as f:
            f.seek(0, 2)
            f.write(f"[{curr_time}] {self.item_count} Items written to MySQL\n")
            # 遍历字典，将每个来源的item数量写入日志文件
            for source, count in self.source_count.items():
                f.write(f"  {source}: {count} Items from written to MySQL\n")


class GamePipeline:
    cursor = None
    conn = None

    def __init__(self):
        settings = get_project_settings()
        self.conn = pymysql.connect(
            host=settings['MYSQL_HOST'],
            port=settings['MYSQL_PORT'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            db=settings['MYSQL_DATABASE'],
            charset='utf8mb4',
        )

    # 重写父类的方法，该方法只在开始爬虫时被调用一次
    def open_spider(self, spider):
        print("start news spider……")

    # 处理数据的专用方法，item为数据，spider为爬虫对象
    def process_item(self, item, spider):
        news_title = item['news_title']
        formate_time = item['formate_time']
        news_link = item['news_link']
        source = item['source']
        print(source, news_title, formate_time, news_link)

        self.cursor = self.conn.cursor()
        sql = '''replace into `website_link`(title, url, source, time) values ('%s', '%s', '%s', '%s')''' \
              % (news_title, news_link, source, formate_time)
        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(e)

        return item

    # 重写父类的方法，该方法只在结束爬虫时被调用一次
    def close_spider(self, spider):
        if self.cursor is not None:
            self.cursor.close()
        self.conn.close()
        print("close news spider……")
