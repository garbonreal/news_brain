import datetime
from game.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings
import datetime
import re
import json
import html


def convert_date(date_str):
    date = datetime.datetime.strptime(date_str, '%m/%d')
    year = datetime.datetime.now().year
    return datetime.datetime(year, date.month, date.day).strftime('%Y-%m-%d %H:%M:%S')


class C114Spider(scrapy.Spider):
    name = "c114"
    start_urls = ["http://www.c114.com.cn/ai/",
                  "http://www.c114.com.cn/m2m/",
                  "http://www.c114.com.cn/anfang/",
                  "http://www.c114.com.cn/cloud/"]

    post_params = {'ai': (5339, '人工智能'), 'm2m': (2488, '物联网'), 'anfang': (4324, '安防'), "cloud": (4049, '云计算')}

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
        div_list = response.xpath("//div[@class='new_list_c']")
        # 将new_list数据写入到文件中
        for div in div_list:
            news_title = div.xpath("./h6/a/text()").extract_first()
            news_link = div.xpath("./h6/a/@href").extract_first()
            news_time = div.xpath("./div[@class='new_list_c_bot']/div[@class='new_list_time fl']/span/text()").extract_first()
            news_time = convert_date(news_time)
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
            item["source"] = "C114通信网-" + self.post_params[category][1]
            yield item
        # 发送ajax请求，进入下一页
        # "http://www.c114.com.cn/api/ajax/aj_1805_2.asp?p=3&idn=5339"
        next_url = "http://www.c114.com.cn/api/ajax/aj_1805_2.asp?p={}&idn={}"
        param = {
            'p': 2,
            'idn': self.post_params[category][0]
        }
        # 将param拼接到next_url中
        next_url = next_url.format(param['p'], param['idn'])
        yield scrapy.Request(url=next_url, callback=self.parse_next, meta={'category': category, 'page': 2})

    def parse_next(self, response):
        print(response.request.url)
        category = response.meta['category']
        page = response.meta['page'] + 1
        news_list = response.xpath('//div[@class="new_list_c"]')
        for news in news_list:
            # 提取新闻标题和链接
            news_title = news.xpath('./h6/a/text()').get()
            news_link = news.xpath('./h6/a/@href').get()
            # 提取新闻时间
            time = news.xpath('./div[@class="new_list_c_bot"]/div[@class="new_list_time fl"]/span/text()').get()
            news_time = convert_date(time)

            # 取得当前时间往前一个月的时间
            now = datetime.datetime.now()
            month = now - datetime.timedelta(days=30)
            month = month.strftime('%Y-%m-%d %H:%M:%S')
            if news_time < month:
                return
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
            item["source"] = "C114通信网-" + self.post_params[category][1]
            yield item

        # 发送ajax请求，进入下一页
        next_url = "http://www.c114.com.cn/api/ajax/aj_1805_2.asp?p={}&idn={}"
        param = {
            'p': page,
            'idn': self.post_params[category][0]
        }
        # 将param拼接到next_url中
        next_url = next_url.format(param['p'], param['idn'])
        yield scrapy.Request(url=next_url, callback=self.parse_next, meta={'category': category, 'page': page})
