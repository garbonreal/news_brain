import multiprocessing
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def crawl(spider_name):
    process = CrawlerProcess(get_project_settings())
    print(get_project_settings().get('MYSQL_USER'))
    process.crawl(spider_name)
    process.start()


if __name__ == '__main__':
    spider_names = ['cinic', 'cena']
    pool = multiprocessing.Pool(processes=10)
    pool.map(crawl, spider_names)
    pool.close()
    pool.join()