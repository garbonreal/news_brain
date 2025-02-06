import datetime
import time
from pipelines.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings


class SuZhouGxjSpider(scrapy.Spider):
    name = "suzhougxj"
    start_urls = ["https://gxj.suzhou.gov.cn/szeic/szgxdt/common_list.shtml",
                  "https://gxj.suzhou.gov.cn/szeic/gzdt/common_list.shtml",
                  "https://gxj.suzhou.gov.cn/szeic/ggl/common_list.shtml"]
    tag = {"szgxdt": ["苏州工信动态", 2], "gzdt": ["工作动态", 2], "ggl": ["公告栏", 2]}
    url = "https://gxj.suzhou.gov.cn/szeic/{}/common_list_{}.shtml"

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
        temp = 5
        category = response.request.url.split("/")[-2]
        print(category)
        ul_list = response.xpath("//div[@class='pageList infoList listContent']")
        # 将new_list数据写入到文件中

        for ul in ul_list:
            li_list = ul.xpath(".//li")
            for li in li_list:
                news_title = li.xpath(".//a/@title").extract_first().strip()
                news_link = "https://gxj.suzhou.gov.cn" + li.xpath(".//a/@href").extract_first()
                news_time = li.xpath(".//span/text()").extract_first()
                news_time = news_time + " 00:00:00"
                # print(news_title, news_link, news_time)
                # 取得当前时间往前一个月的时间
                now = datetime.datetime.now()
                month = now - datetime.timedelta(days=30)
                month = month.strftime('%Y-%m-%d %H:%M:%S')
                if news_time < month:
                    temp = temp-1
                if temp == 0:
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
                item["source"] = "苏州市工信局-" + self.tag[category][0]
                yield item

        if self.tag[category][1] <= 2:
            new_url = format(self.url.format(category, self.tag[category][1]))
            self.tag[category][1] += 1
            yield scrapy.Request(url=new_url, callback=self.parse)
