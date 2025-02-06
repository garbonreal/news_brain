import datetime
from pipelines.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings


class EchinagovSpider(scrapy.Spider):
    name = "echinagov"
    start_urls = ["http://www.echinagov.com/news/"]

    url = "http://www.echinagov.com/node/110_{}/"
    page_num = 2

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
        div_list = response.xpath("//div[@class='news-item']")

        for div in div_list:
            news_title = div.xpath(".//a/h3/text()").extract_first()
            news_time = div.xpath(".//li[@class='ml20']/text()").extract_first()
            news_link = div.xpath(".//a/@href").extract_first()

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
            item["source"] = "国脉电子政务网"
            yield item

        new_url = format(self.url.format(self.page_num))
        self.page_num += 1
        yield scrapy.Request(url=new_url, callback=self.parse)
