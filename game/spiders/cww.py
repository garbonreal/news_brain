import datetime
from game.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings
import json
import time
import datetime
import re


class CwwSpider(scrapy.Spider):
    name = "cww"

    def __init__(self):
        super().__init__()
        settings = get_project_settings()
        self.conn = pymysql.connect(
            host=settings['MYSQL_HOST'],
            port=settings['MYSQL_PORT'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            db=settings['MYSQL_DATABASE'],
            charset='utf8mb4',
        )
        self.cursor = self.conn.cursor()

    def start_requests(self):
        for index in range(1, 5):
            url = 'http://www.cww.net.cn/web/news/articleinfo/selctArticleListBycolumnId.json?' \
                  'columnId=8102&page={}&size=30'.format(index)
            yield scrapy.Request(
                url=url,
                callback=self.parse
            )

    def parse(self, response):
        if response.status == 200:
            data = json.loads(response.body)
            data = data["data"]["rows"]
            news_title = ''
            news_link = ''
            news_time = None

            for news in data:
                news_title = news['articleTitle']
                news_link = "http://www.cww.net.cn/article?id=" + str(news["idno"])
                news_time = news['entryDate']
                # 将秒数转化为时间
                if news_time is not None:
                    news_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(news_time / 1000))

                # 取得当前时间往前一个月的时间
                now = datetime.datetime.now()
                month = now - datetime.timedelta(days=30)
                month = month.strftime('%Y-%m-%d %H:%M:%S')
                if news_time < month:
                    return

                sql = "select * from `website_link` where url='%s'" % news_link
                self.cursor.execute(sql)
                result = self.cursor.fetchone()
                if result:
                    print("该数据已经存在")
                    return

                item = GameItem()
                item["news_title"] = news_title
                item["formate_time"] = news_time
                item["news_link"] = news_link
                item["source"] = '通信世界网'
                yield item

        else:
            print('请求失败')