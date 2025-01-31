import datetime
from game.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings
import re


class Cto51Spider(scrapy.Spider):
    name = "cto51"
    start_urls = ["https://www.51cto.com/bigdata/p1",
                  "https://www.51cto.com/blockchain/p1",
                  "https://www.51cto.com/iot/p1",
                  "https://www.51cto.com/ai/p1"]

    tag = {'bigdata': '大数据', 'blockchain': '区块链', "iot": '物联网', 'ai': '人工智能'}

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
        old_url = response.request.url
        page_num = int(re.findall(r'\d+$', old_url)[0]) + 1
        print(page_num)

        div_list = response.xpath("//div[@class='article-irl-c split-left-l']")
        # 将new_list数据写入到文件中

        for div in div_list:
            news_title = div.xpath(".//div[@class='article-irl-ct']/a/text()").extract_first()
            news_link = div.xpath(".//div[@class='article-irl-ct']/a/@href").extract_first()
            news_time = div.xpath("./div[@class='article-irl-cb']/p/text()").extract_first()
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
            item["source"] = "51CTO-" + self.tag[category]
            yield item

        if page_num < 10:
            new_url = old_url.replace('p'+str(page_num-1), 'p{}'.format(page_num))
            yield scrapy.Request(url=new_url, callback=self.parse)
