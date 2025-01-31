import datetime
from game.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings

import datetime
import re

# 定义正则表达式模式
pattern_list = [
    r'(\d+) 分前',
    r'今天 (\d+:\d+)',
    r'昨天 (\d+:\d+)',
    r'前天 (\d+:\d+)',
    r'(\d{1,2}-\d{1,2} \d{1,2}:\d{1,2})',
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})'
]

# 定义日期格式
date_format = '%Y-%m-%d %H:%M'


# 定义一个函数，将不同格式的时间转换为标准格式的时间
def convert_time(time_str):
    for pattern in pattern_list:
        match = re.match(pattern, time_str)
        if match:
            if pattern == pattern_list[0]:
                # X 分前
                minutes_ago = int(match.group(1))
                time = datetime.datetime.now() - datetime.timedelta(minutes=minutes_ago)
            elif pattern == pattern_list[1]:
                # 今天 X:X
                time = datetime.datetime.now().replace(hour=int(match.group(1)[:2]), minute=int(match.group(1)[3:]))
            elif pattern == pattern_list[2]:
                # 昨天 X:X
                time = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=int(match.group(1)[:2]),
                                                                                      minute=int(match.group(1)[3:]))
            elif pattern == pattern_list[3]:
                # 前天 X:X
                time = (datetime.datetime.now() - datetime.timedelta(days=2)).replace(hour=int(match.group(1)[:2]),
                                                                                      minute=int(match.group(1)[3:]))
            elif pattern == pattern_list[4]:
                # XX-XX XX:XX
                date_str = match.group(1)
                current_year = datetime.datetime.now().year
                date_str_with_year = f"{current_year}-{date_str}"
                time = datetime.datetime.strptime(date_str_with_year, date_format)
            elif pattern == pattern_list[5]:
                # XXXX-XX-XX XX:XX
                date_str = match.group(1)
                date_str_with_year = f"{date_str}"
                time = datetime.datetime.strptime(date_str_with_year, date_format)

            return time.strftime(date_format)

    return datetime.datetime.now().strftime(date_format)


# 测试
time_list = [
    '5 分前',
    '半小时前',
    '今天 10:23',
    '昨天 23:45',
    '前天 14:30',
    '2022-04-10 16:12',
    '02-28 16:12'
]


# 主函数
if __name__ == '__main__':
    for time_str in time_list:
        print(convert_time(time_str))


class CenaSpider(scrapy.Spider):
    name = "cena"
    start_urls = ["http://www.cena.com.cn"]

    tag_list = [('smartt', '智能终端'), ('ssxw', '省市新闻'), ('infocom', '信息通信'), ('semi', '半导体')]
    url_cena = "http://www.cena.com.cn/{}/index_{}.html"

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
        for tag in self.tag_list:
            for index in range(1, 3):
                new_url = format(self.url_cena.format(tag[0], index))
                yield scrapy.Request(url=new_url, callback=self.parse_detail, meta={"tag": tag[1]})

    def parse_detail(self, response):
        tag = response.meta['tag']
        div_list = response.xpath("//div[@class='news_list clearfix']")
        for div in div_list:
            news_title = div.xpath(".//a/text()").extract_first()
            news_time = div.xpath(".//span[@class='time']/text()").extract_first()
            news_link = div.xpath(".//a/@href").extract_first()
            source = "电子信息产业网-{}".format(tag)

            # 处理时间格式，网站一共可能出现4种时间格式：X 分前，今天 X:X，昨天 X:X，前天 X:X, XX-XX XX:XX
            if news_time is not None:
                news_time = news_time.strip()
                news_time = convert_time(news_time) + ":00"

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
            item["source"] = source
            yield item
