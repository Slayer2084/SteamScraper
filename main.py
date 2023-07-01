from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from scrapy import signals

from scraper import SteamSpider


def print_(item):
    print(item)


def main():
    crawler = CrawlerProcess()
    dispatcher.connect(print_, signal=signals.item_passed)
    crawler.crawl(SteamSpider, "climate+change")
    crawler.start()


if __name__ == "__main__":
    main()
