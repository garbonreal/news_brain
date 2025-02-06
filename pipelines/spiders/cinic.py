import datetime
from pipelines.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings


class CinicSpider(scrapy.Spider):
    name = "cinic"
    start_urls = ["http://www.cinic.org.cn/xw/cjxw/index.html"]

    url = "http://www.cinic.org.cn/xw/cjxw/index_{}.html"
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
        li_list = response.xpath("//div[@class='col-l']/ul/li")
        # 将new_list数据写入到文件中

        for li in li_list:
            news_title = li.xpath(".//a/text()").extract_first()
            news_time = li.xpath(".//span[@class='sp2']/text()").extract_first()
            # formate_time为当前的时间
            formate_time = datetime.datetime.now()
            if news_time is not None:
                formate_time = datetime.datetime.strptime(news_time, "%Y-%m-%d")
            news_link = "http://www.cinic.org.cn/" + li.xpath(".//a/@href").extract_first()

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
            item["source"] = "中国产业经济信息网"
            yield item

        if self.page_num <= 5:
            new_url = format(self.url.format(self.page_num))
            self.page_num += 1
            yield scrapy.Request(url=new_url, callback=self.parse)
