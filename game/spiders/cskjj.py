import datetime
import time
from game.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings


class CsKjjSpider(scrapy.Spider):
    name = "cskjj"
    start_urls = ["http://kjj.changsha.gov.cn/zfxxgk/fdzdgk/qtfdxx/sjdt/index.html"
                  "http://kjj.changsha.gov.cn/zfxxgk/qxwdt/index.html",
                  "http://kjj.changsha.gov.cn/zfxxgk/yqdtai/index.html",
                  "http://kjj.changsha.gov.cn/zfxxgk/tzgg_27202/index.html"]
    tag = {"qxwdt": ["区县动态", 1], "yqdtai": ["园区动态", 1], "tzgg_27202": ["科技局通知公告", 1], "fdzdgk/qtfdxx/sjdt": ["市局动态", 1]}
    url = "http://kjj.changsha.gov.cn/zfxxgk/{}/index_{}.html"

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
        if category == "sjdt":
            category = response.request.url.split("/")[-4] + "/" + response.request.url.split("/")[-3] + "/" + response.request.url.split("/")[-2]
        print(category)
        if category == "fdzdgk/qtfdxx/sjdt":
            li_list = response.xpath("//div[@class='xxgk-list']/ul/li")
        else:
            li_list = response.xpath("//div[@class='list-box show']/ul/li")
        # 将new_list数据写入到文件中

        for li in li_list:
            news_title = li.xpath(".//a/text()").extract_first().strip()
            if category == "tzgg_27202":
                news_link = "http://kjj.changsha.gov.cn/zfxxgk/tzgg_27202" + li.xpath(".//a/@href").extract_first().strip().replace("./", "/")
                news_time = li.xpath(".//i/text()").extract_first().strip().replace("[", "").replace("]", "")
            elif category == "fdzdgk/qtfdxx/sjdt":
                news_link = "http://kjj.changsha.gov.cn/zfxxgk/fdzdgk/qtfdxx/sjdt" + li.xpath(".//a/@href").extract_first().strip().replace("./", "/")
                news_time = li.xpath(".//span/text()").extract_first()
            else:
                news_time = li.xpath(".//span/text()").extract_first()
                news_link = li.xpath(".//a/@href").extract_first().strip()
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
            item["source"] = "长沙市科学技术局-" + self.tag[category][0]
            yield item

        if self.tag[category][1] <= 2:
            new_url = format(self.url.format(category, self.tag[category][1]))
            self.tag[category][1] += 1
            yield scrapy.Request(url=new_url, callback=self.parse)
