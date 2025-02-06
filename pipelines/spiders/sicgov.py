import datetime
from pipelines.items import GameItem
import scrapy
import pymysql
import re
from scrapy.utils.project import get_project_settings


class SicgovSpider(scrapy.Spider):
    name = "sicgov"
    start_urls = ["http://www.sic.gov.cn/Column/611/0.htm",
                  "http://www.sic.gov.cn/Column/609/0.htm",
                  "http://www.sic.gov.cn/Column/610/0.htm",
                  "http://www.sic.gov.cn/Column/612/0.htm",
                  "http://www.sic.gov.cn/Column/613/0.htm"]

    tag = {'611': '数字经济发展', "609": '行业政策研究', "610": '前沿技术动态', "612": '数字治理创新',
           '613': '数字社会应用'}

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
        print(self.tag[col])
        div_list = response.xpath("//div[@class='articleListNum2 articlList01 articlList02']/ul/li")
        for div in div_list:
            news_title = div.xpath(".//a/text()").extract_first().strip()
            news_time = div.xpath(".//span[@class='times']/text()").extract_first().strip() + " 00:00:00"
            news_link = "http://www.sic.gov.cn" + div.xpath(".//a/@href").extract_first().strip().replace("../..", "")
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
            item["source"] = "国家信息中心-" + self.tag[col]
            yield item
