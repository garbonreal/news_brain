import datetime
import time
from pipelines.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings


class ShGovSpider(scrapy.Spider):
    name = "shgov"
    start_urls = ["https://www.sheitc.sh.gov.cn/xwfb/index.html",
                  "https://www.sheitc.sh.gov.cn/gydt/index.html"]

    url = "https://www.sheitc.sh.gov.cn/{}/index_{}.html"
    tag = {"xwfb": ["新闻发布", 2], "gydt": ["产业动态", 2]}

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

        li_list = response.xpath("//div[@class='secondary-wrap']/ul/li")
        # 将new_list数据写入到文件中

        for li in li_list:
            news_title = li.xpath(".//a/div/h2/text()").extract_first().strip()
            news_link = "https://www.sheitc.sh.gov.cn" + li.xpath(".//a/@href").extract_first().strip()
            news_time = li.xpath(".//span/text()").extract_first().strip()
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
            item["source"] = "上海市经济和信息化委员会-" + self.tag[category][0]
            yield item

        if self.tag[category][1] <= 5:
            new_url = format(self.url.format(category, self.tag[category][1]))
            self.tag[category][1] += 1
            yield scrapy.Request(url=new_url, callback=self.parse)
