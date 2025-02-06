import datetime
from pipelines.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings
import datetime
import re
import json
import html


def timestamp_to_date(timestamp):
    date = datetime.datetime.fromtimestamp(timestamp/1000.0).strftime('%Y-%m-%d %H:%M:%S')
    return date


class ChinagazelleSpider(scrapy.Spider):
    name = "chinagazelle"
    start_urls = ["https://www.chinagazelle.cn/product/dynamic/latested/59?paperid=",
                  "https://www.chinagazelle.cn/product/dynamic/latested/7?paperid=",
                  "https://www.chinagazelle.cn/product/dynamic/latested/1?paperid=",
                  "https://www.chinagazelle.cn/product/dynamic/latested/5?paperid="]

    post_params = {'1': ['高新区动态'], '5': ['人工智能动态'], '7': ['独角兽动态'], '59': ['城市创新动态']} #, 'm2m': (2488, '物联网'), 'anfang': (4324, '安防'), "cloud": (4049, '云计算')}

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
        category = response.request.url.split("/")[-1].split("?")[-2]
        print(category)
        total_data = response.json()
        if category == "7":
            data = []
            if '独角兽企业新闻' in total_data:
                data += total_data.get('独角兽企业新闻')
            if '独角兽资本动态' in total_data:
                data += total_data.get('独角兽资本动态')
        elif category == "59":
            data = []
            if '城市大会' in total_data:
                data += total_data.get('城市大会')
            if '权威榜单' in total_data:
                data += total_data.get('权威榜单')
            if '重大政策' in total_data:
                data += total_data.get('重大政策')
            if '重大项目' in total_data:
                data += total_data.get('重大项目')
        else:
            data = response.json()['no_set_column']
        if response.request.url.split("?")[-1] == "paperid=":
            next_url = response.request.url + str(data[0]['prePaperid'])
        else:
            next_url = response.request.url.split("?")[0] + "?paperid=" + str(data[0]['prePaperid'])
        print(next_url)
        # 将new_list数据写入到文件中
        for div in data:
            news_title = div['title']
            news_link = "https://www.chinagazelle.cn/periodical/outerLog?from=gazelle&id="\
                        + str(div['dynamicid']) + "&paperInfoId" + str(div['id'])
            news_time = div['createtime']
            news_time = timestamp_to_date(news_time)
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
            item["source"] = "瞪羚云-" + self.post_params[category][0]
            yield item

        yield scrapy.Request(url=next_url, callback=self.parse)
