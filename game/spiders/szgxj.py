import datetime
import time
from game.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings


class SzgxjSpider(scrapy.Spider):
    name = "szgxj"
    start_urls = ["http://gxj.sz.gov.cn/xxgk/xxgkml/qt/gzdt/index.html",
                  "http://gxj.sz.gov.cn/xxgk/xxgkml/qt/tzgg/index.html"]
    tag = {"gzdt": ["工作动态", 2], "tzgg": ["通知公告", 2]}
    url = "http://gxj.sz.gov.cn/xxgk/xxgkml/qt/{}/index_{}.html"

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
        category = response.request.url.split("/")[-2]
        print(category)
        li_list = response.xpath("//div[@class='ListconC']")
        # 将new_list数据写入到文件中

        for li in li_list:
            news_title = li.xpath(".//a/text()").extract_first().strip()
            news_link = li.xpath(".//a/@href").extract_first().replace("./", "/")
            news_time = li.xpath(".//span/text()").extract_first().strip().replace("[", "").replace("]", "")
            news_time = news_time + " 00:00:00"
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
            item["source"] = "深圳市工信局-" + self.tag[category][0]
            yield item

        if self.tag[category][1] <= 5:
            new_url = format(self.url.format(category, self.tag[category][1]))
            self.tag[category][1] += 1
            yield scrapy.Request(url=new_url, callback=self.parse)
