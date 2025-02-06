import datetime
from pipelines.items import GameItem
import scrapy
import pymysql
from scrapy.utils.project import get_project_settings
import datetime
import re
import json


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
    '02-28 16:12',
    '2022-04-10 16:12'
]


# 主函数
if __name__ == '__main__':
    for time_str in time_list:
        print(convert_time(time_str))


class CcidcomSpider(scrapy.Spider):
    name = "ccidcom"
    start_urls = ["http://www.ccidcom.com/gyhlw/index.html",
                  "http://www.ccidcom.com/jishu/index.html",
                  "http://www.ccidcom.com/hulianwang/index.html",
                  "http://www.ccidcom.com/wulianwang/index.html"]

    post_params = {'gyhlw': ('csrf6434db592123e', '821e6cac517db42f1e8612f4987293db', '工业互联网'),
                   'jishu': ('csrf6434db4be3343', '9a6143019a331c703e313c0e77d233f8', '技术'),
                   'hulianwang': ('csrf6434db4e242cb', 'f8f639179a9ca904d6e81d2d4241cd90', '互联网'),
                   'wulianwang': ('csrf6434db50087bf', 'b829c6fcb4334f0b0260d9f7ab38135d', '物联网')}

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
        div_list = response.xpath("//div[@class='article-item']")
        # 将new_list数据写入到文件中

        for div in div_list:
            news_title = div.xpath(".//div[@class='title']/a/font/text()").extract_first()
            news_link = "http://www.ccidcom.com" + div.xpath(".//div[@class='title']/a/@href").extract_first()
            news_time = div.xpath(".//div[@class='info']/span[@class='time']/text()").extract_first()
            news_time = convert_time(news_time)
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
            item["source"] = "通信产业网-" + self.post_params[category][2]
            yield item

        # 发送ajax请求，进入下一页
        next_url = "http://www.ccidcom.com/getcolumnarts.do"
        param = {
            'colnum_name': category,
            'start': 10,
            'page': 1,
            self.post_params[category][0]: self.post_params[category][1]
        }
        yield scrapy.Request(
            url=next_url,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(param),
            callback=self.parse_next,
            meta={'category': category, 'start': 10}
        )

    def parse_next(self, response):
        data = json.loads(response.body)
        data = data["arts"]
        category = response.meta['category']
        start = response.meta['start'] + 10
        news_title = ''
        news_link = ''
        news_time = None

        for news in data:
            news_title = news['title']
            news_link = "http://www.ccidcom.com" + str(news["art_url"])
            news_time = news['art_date']
            news_time = convert_time(news_time)
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
            item["source"] = "通信产业网-" + self.post_params[category][2]
            yield item

        # 发送ajax请求，进入下一页
        next_url = "http://www.ccidcom.com/getcolumnarts.do"
        param = {
            'colnum_name': category,
            'start': start,
            'page': 1,
            self.post_params[category][0]: self.post_params[category][1]
        }
        yield scrapy.Request(
            url=next_url,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(param),
            callback=self.parse_next,
            meta={'category': category, 'start': start}
        )