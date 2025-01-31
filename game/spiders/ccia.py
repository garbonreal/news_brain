import datetime
from game.items import GameItem
import scrapy
import pymysql
import re
from scrapy.utils.project import get_project_settings


class CciaSpider(scrapy.Spider):
    name = "ccia"
    start_urls = ["http://www.ccia.org.cn/zixun.php",
                  "http://www.ccia.org.cn/news.php"]

    tag = {'zixun': '业界资讯', "news": '热点新闻'}

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

    def parse(self, response):
        curr_url = response.request.url
        col = curr_url.split("/")[-1].replace(".php", "")
        table = response.xpath("//table[@class='Anewslist']//tr")
        for tr in table:
            news_title = tr.xpath(".//td[@class='newsfont']/a/text()").extract_first().replace("·", "")
            news_time = tr.xpath(".//td[@class='font4e4e4e']/text()").extract_first() + " 00:00:00"
            news_link = "http://www.ccia.org.cn" + tr.xpath(".//td[@class='newsfont']/a/@href").extract_first()
            # 取得当前时间往前一个月的时间
            now = datetime.datetime.now()
            month = now - datetime.timedelta(days=30)
            month = month.strftime('%Y-%m-%d %H:%M:%S')
            if news_time < month:
                return
            # 判断数据库中是否已经存在该数据
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
            item["source"] = "中国通信工业协会-" + self.tag[col]
            yield item
