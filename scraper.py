import scrapy
import re


class SteamSpider(scrapy.Spider):
    """Spider to scrape Steam forums.

    """
    name = 'Steam'

    allowed_domains = ["steamcommunity.com"]
    start_urls = []
    custom_settings = {
        'LOG_LEVEL': 'WARN',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 '
                      'Safari/537.1',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 6,
        # 'JOBDIR': './News/CNBCJobs',
        'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
        },
        'RANDOM_UA_TYPE': "random",
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 5,
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
    }

    def __init__(self, query: str = "climate+change", **kwargs):
        self.url_stream = f"https://steamcommunity.com/discussions/forum/search/?q={query}&sort=time&p="
        super().__init__(**kwargs)

    def start_requests(self):
        yield scrapy.Request(self.url_stream + "1&start=pages", callback=self.request_all_pages)

    def request_all_pages(self, response):
        max_pages = int(response.css(".discussion_search_pagingcontrols ::text").getall()[-1].replace(",", "").
                        split(" ")[-2])
        yield scrapy.Request(self.url_stream + "1", callback=self.parse_page)
        # for page in range(1, max_pages + 1):
        #     yield scrapy.Request(self.url_stream + str(page), callback=self.parse_page)

    def parse_page(self, response):
        body_urls = response.css(".post_searchresult_simplereply ::attr(href)").getall()
        for url in body_urls:
            id_ = re.search("/#c.*", url)
            if id_:
                id_ = id_.group(0).replace("/#c", "")
            else:
                id_ = "op"
            url = re.split("#c.*", url)[0]
            yield scrapy.Request(url, callback=self.parse_post, meta={"id": id_, "base_url": url, "page": 1})

    def find_comments_page(self, response):
        id_ = response.meta["id"]
        url = response.meta["base_url"]
        page = response.meta["page"]
        if id_ == "op":
            yield scrapy.Request(url, callback=self.parse_post, meta={"id": id_})
        else:
            div_id = "comment_" + id_
            post = response.xpath(f'//div[@id="{div_id}"]')
            if post is None:
                yield scrapy.Request(f"{url}?ctp={page + 1}", callback=self.find_comments_page,
                                     meta={"id": id_, "base_url": url, "page": page})
            else:
                yield scrapy.Request(f"{url}?ctp={page}&success=True", callback=self.parse_post, meta={"id": id_})

    @staticmethod
    def parse_post(response):
        op = False
        meta = response.meta
        id_ = meta["id"]
        if id_ == "op":
            op = True
        if op:
            post = response.css(".forum_op")
        else:
            id_ = "comment_" + id_
            post = response.xpath(f'//div[@id="{id_}"]')
        if op:
            author = post.css(".forum_op_author ::text").get()
            author_url = post.css(".forum_op_author ::attr(href)").get()
            body = post.css(".forum_op .content ::text").get()
            time = post.css(".date ::attr(data-timestamp)").get()
        else:
            author = post.css(".commentthread_author_link ::text").get()
            author_url = post.css(".commentthread_author_link ::attr(href)").get()
            body = post.css(".commentthread_comment_text ::text").get()
            time = post.css(".commentthread_comment_timestamp ::attr(data-timestamp)").get()
        forum = response.css(".discussions_breadcrumbs a~ a+ a ::text").get()
        body_url = response.url
        yield {
            "forum": forum,
            "author": author,
            "author_url": author_url,
            "body": body,
            "body_url": body_url,
            "post_id": id_,
            "time": time,
        }
