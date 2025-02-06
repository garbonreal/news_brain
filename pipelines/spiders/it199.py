import datetime
from pipelines.items import GameItem
import scrapy
import pymysql
import re
from scrapy.utils.project import get_project_settings


class It199Spider(scrapy.Spider):
    name = "it199"
    start_urls = ["http://www.199it.com/archives/category/dataindustry",
                  "http://www.199it.com/archives/category/emerging",
                  "http://www.199it.com/archives/category/fintech"]

    tag = {'dataindustry': '数据行业', 'emerging': "战略新兴产业", "fintech": '金融科技'}

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
        col = curr_url.split("/")[-1]
        print(curr_url, col)
        div_list = response.xpath("//div[@class='entry-content']")
        for div in div_list:
            news_title = div.xpath("./h2[@class='entry-title']/a/text()").extract_first()
            news_time = div.xpath(".//time[@class='entry-date']/text()").extract_first()
            news_link = "http:" + div.xpath("./h2[@class='entry-title']/a/@href").extract_first()
            formate_time = datetime.datetime.now()
            if news_time is not None:
                # 将原日期字符串转换为datetime对象
                date_obj = datetime.datetime.strptime(news_time, '%Y年%m月%d日')
                # 将datetime对象转换为目标格式的字符串
                formate_time = date_obj.strftime('%Y-%m-%d %H:%M:%S')
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
            item["formate_time"] = formate_time
            item["news_link"] = news_link
            item["source"] = "互联网数据咨讯中心-" + self.tag[col]
            yield item

        new_url = curr_url + "/page/2"
        yield scrapy.Request(url=new_url, callback=self.parse_next, meta={'page': 2})

    def parse_next(self, response):
        curr_url = response.request.url
        col = curr_url.split("/")[-3]
        print(curr_url, col)
        div_list = response.xpath("//div[@class='entry-content']")
        for div in div_list:
            news_title = div.xpath("./h2[@class='entry-title']/a/text()").extract_first()
            news_time = div.xpath(".//time[@class='entry-date']/text()").extract_first()
            news_link = "http:" + div.xpath("./h2[@class='entry-title']/a/@href").extract_first()
            formate_time = datetime.datetime.now()
            print(news_title, news_link, news_time)
            if news_time is not None:
                # 将原日期字符串转换为datetime对象
                date_obj = datetime.datetime.strptime(news_time, '%Y年%m月%d日')
                # 将datetime对象转换为目标格式的字符串
                formate_time = date_obj.strftime('%Y-%m-%d %H:%M:%S')
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
            item["formate_time"] = formate_time
            item["news_link"] = news_link
            item["source"] = "互联网数据咨讯中心-" + self.tag[col]
            yield item

        curr_url = re.sub(r'/\d+$', '/', curr_url)
        page = response.meta['page'] + 1
        new_url = curr_url + str(page)
        print(new_url)
        yield scrapy.Request(url=new_url, callback=self.parse_next, meta={'page': page})
