import datetime
import time
from pipelines.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings


class CqdsjjSpider(scrapy.Spider):
    name = "cqdsjj"
    start_urls = ["https://dsjj.cq.gov.cn/sy_533/mtbd/index.html",
                  "https://dsjj.cq.gov.cn/sy_533/bmdt/sj/index.html",
                  "https://dsjj.cq.gov.cn/sy_533/bmdt/qx/index.html"]
    tag = {"mtbd": ["新闻报道", 1], "bmdt/sj": ["市局动态", 1], "bmdt/qx": ["区县动态", 1]}
    url = "https://dsjj.cq.gov.cn/sy_533/{}/index_{}.html"

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
        if category != "mtbd":
            more = response.request.url.split("/")[-3]
            category = more + "/" + category
        print(category)
        ul_list = response.xpath("//div[@class='p-rt rt']/ul")
        # 将new_list数据写入到文件中

        for ul in ul_list:
            li_list = ul.xpath(".//li")
            print("------------------")
            for li in li_list:
                news_title = li.xpath(".//a/text()").extract_first().strip()
                news_link = li.xpath(".//a/@href").extract_first()
                if not news_link.startswith("http"):
                    continue
                news_time = li.xpath(".//span/text()").extract_first().strip().replace("[", "").replace("]", "")
                news_time = news_time + " 00:00:00"
                # print(news_title, news_link, news_time)
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
                item["source"] = "重庆市大数据应用发展管理局-" + self.tag[category][0]
                yield item

        if self.tag[category][1] <= 5:
            new_url = format(self.url.format(category, self.tag[category][1]))
            self.tag[category][1] += 1
            yield scrapy.Request(url=new_url, callback=self.parse)
