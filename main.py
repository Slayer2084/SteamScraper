from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from scrapy import signals

from scraper import SteamSpider


def print_(item):
    print(item)


def main(search: str):
    crawler = CrawlerProcess()
    dispatcher.connect(print_, signal=signals.item_passed)
    crawler.crawl(SteamSpider, query=search)
    crawler.start()


if __name__ == "__main__":
    import os
    import sys

    if os.path.exists("data/data.json"):
        os.remove("data/data.json")

    if len(sys.argv) > 1:
        search_term = sys.argv[1]
    else:
        raise ValueError("Please provide a search term")

    main(search_term)
