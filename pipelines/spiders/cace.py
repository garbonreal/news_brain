import datetime
from pipelines.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings
import json
import time


class CaceSpider(scrapy.Spider):
    name = "cace"

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
        url = "https://www.cace.org.cn/News/GetMsgList?page=1&limit=20&tp=33"
        yield scrapy.Request(url=url, callback=self.parse, meta={'page': 1})

    def parse(self, response):
        page = response.meta['page'] + 1
        data = json.loads(response.body)
        data = data['data']

        news_title = ''
        news_link = ''
        news_time = None

        for news in data:
            news_title = news['TITLE']
            news_link = "https://www.cace.org.cn/NEWS/COUNT?a=" + str(news["ID"])
            news_time = news['PTIME'].replace("/Date(", "").replace(")/", "")
            if news_time is not None:
                news_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(news_time) / 1000))
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
            item["source"] = "中国通信企业协会"
            yield item

        # 发送ajax请求，进入下一页
        next_url = "https://www.cace.org.cn/News/GetMsgList?page={}&limit=20&tp=33"
        # 将param拼接到next_url中
        next_url = next_url.format(page)
        yield scrapy.Request(url=next_url, callback=self.parse, meta={'page': page})