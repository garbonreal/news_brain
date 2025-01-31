import datetime
from game.items import GameItem
import scrapy
import pymysql
import re
from scrapy.utils.project import get_project_settings


class GkzhanSpider(scrapy.Spider):
    name = "gkzhan"
    start_urls = ["https://www.gkzhan.com/news/t11/list.html",
                  "https://www.gkzhan.com/news/t15/list.html",
                  "https://www.gkzhan.com/news/t1358/list.html"]

    tag = {'t11': '政策法规', 't15': '行业动态', "t1358": '企业动态'}

    base_url = 'https://www.gkzhan.com/news/{}/list_p{}.html'

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
        col = curr_url.split("/")[-2]
        print(curr_url, col)
        div_list = response.xpath("//div[@class='leftBox']")
        for div in div_list:
            news_title = div.xpath("./h3/a/text()").extract_first()
            news_time = div.xpath(".//span[@class='time']/text()").extract_first()
            news_link = div.xpath("./h3/a/@href").extract_first()
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
            item["source"] = "中国智能制造网-" + self.tag[col]
            yield item

        new_url = curr_url.replace("list", "list_p2")
        yield scrapy.Request(url=new_url, callback=self.parse_next, meta={'page': 2})

    def parse_next(self, response):
        curr_url = response.request.url
        col = curr_url.split("/")[-2]
        div_list = response.xpath("//div[@class='leftBox']")
        for div in div_list:
            news_title = div.xpath("./h3/a/text()").extract_first()
            news_time = div.xpath(".//span[@class='time']/text()").extract_first()
            news_link = div.xpath("./h3/a/@href").extract_first()
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
            item["source"] = "中国智能制造网-" + self.tag[col]
            yield item

        page = response.meta['page'] + 1
        new_url = self.base_url.format(col, page)
        yield scrapy.Request(url=new_url, callback=self.parse_next, meta={'page': page})
