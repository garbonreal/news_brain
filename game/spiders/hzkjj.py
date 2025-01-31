import datetime
import time
from game.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings
import re


class HzkjjSpider(scrapy.Spider):
    name = "hzkjj"
    start_urls = ["https://kj.hangzhou.gov.cn/col/col1693961/index.html",
                  "https://kj.hangzhou.gov.cn/col/col1228922127/index.html"]
    tag = {"col1693961": ["通知公告", 7862811, 2], "col1228922127": ["创新动态", 7859854, 2]}
    url = "https://kj.hangzhou.gov.cn/col/{}/index.html?uid={}&pageNum={}"

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
        temp = 2
        li_list = response.xpath("//div[@class='con w clearfix']/div[2]/div").extract_first()
        pattern = r'<a href="(.+)" target="_blank" title="(.+)">\s+.+\s+</a>' \
                  r'\s+<span style="float:right;color:#999">\s+(.+)\s+</span>'

        for match in re.findall(pattern, li_list):
            news_link, news_title, news_time = match
            news_link = "https://kj.hangzhou.gov.cn" + news_link
            news_time = news_time.strip() + " 00:00:00"
            # print(news_time, news_link, news_title)
            # 取得当前时间往前一个月的时间
            now = datetime.datetime.now()
            month = now - datetime.timedelta(days=30)
            month = month.strftime('%Y-%m-%d %H:%M:%S')
            if news_time < month:
                temp = temp - 1
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
            item["source"] = "杭州市科学技术局-" + self.tag[category][0]
            yield item

        if self.tag[category][2] <= 5:
            new_url = format(self.url.format(category, self.tag[category][1], self.tag[category][2]))
            self.tag[category][2] += 1
            yield scrapy.Request(url=new_url, callback=self.parse)
