import scrapy
import re


def get_cookies_for_forum(forum_id: str) -> dict:
    cookies = {"wants_mature_content_apps": forum_id}
    return cookies


class SteamSpider(scrapy.Spider):
    """Spider to scrape Steam forums.

    """
    name = 'Steam'

    allowed_domains = ["steamcommunity.com"]
    start_urls = []
    custom_settings = {
        'LOG_LEVEL': 'WARN',
        'COOKIES_DEBUG': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 '
                      'Safari/537.1',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1,
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
        'FEEDS': {"data.json": {'format': 'json', "encoding": "utf-8"}}
    }

    def __init__(self, query, **kwargs):
        self.url_stream = f"https://steamcommunity.com/discussions/forum/search/?q={query}&sort=time&p="
        super().__init__(**kwargs)

    def start_requests(self):
        yield scrapy.Request(self.url_stream + "1&start=pages", callback=self.request_all_pages)

    def request_all_pages(self, response):
        max_pages = int(response.css(".discussion_search_pagingcontrols ::text").getall()[-1].replace(",", "").
                        split(" ")[-2])
        for page in range(1, max_pages + 1):
            yield scrapy.Request(self.url_stream + str(page), callback=self.parse_page)

    def parse_page(self, response):
        body_urls = response.css(".post_searchresult_simplereply ::attr(href)").getall()
        for url in body_urls:
            id_ = re.search("/#c.*", url)
            if id_:
                id_ = id_.group(0).replace("/#c", "")
            else:
                id_ = "op"
            forum_id = re.search("app/.*", url)
            if forum_id is None:
                forum_id = ""
            else:
                forum_id = forum_id.group(0).replace("app/", "").split("/")[0]
            url = re.split("#c.*", url)[0]
            cookies = get_cookies_for_forum(forum_id)
            yield scrapy.Request(url, cookies=cookies, callback=self.find_comments_page,
                                 meta={"id": id_, "base_url": url, "page": 1, "forum_id": forum_id})

    def find_comments_page(self, response):
        url = response.url
        id_ = response.meta["id"]
        base_url = response.meta["base_url"]
        page = response.meta["page"]
        forum_id = response.meta["forum_id"]
        cookies = get_cookies_for_forum(forum_id)
        if id_ == "op":
            yield scrapy.Request(base_url, cookies=cookies,
                                 callback=self.parse_post, meta={"id": id_})
        else:
            div_id = "comment_" + id_
            post = response.xpath(f'//div[@id="{div_id}"]').get()
            new_page = page + 1
            if not post:
                yield scrapy.Request(f"{base_url}?ctp={new_page}", cookies=cookies,
                                     callback=self.find_comments_page,
                                     meta={"id": id_, "base_url": base_url, "page": new_page, "forum_id": forum_id})
            else:
                yield scrapy.Request(f"{base_url}?ctp={page}&success=True", cookies=cookies,
                                     callback=self.parse_post, meta={"id": id_})

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
            author = post.css(".forum_op_author ::text").getall()[-1]
            author_url = post.css(".forum_op_author ::attr(href)").get()
            body = post.css(".forum_op .content ::text").getall()
            time = post.css(".date ::attr(data-timestamp)").get()
        else:
            author = post.css(".commentthread_author_link ::text").getall()[1]
            author_url = post.css(".commentthread_author_link ::attr(href)").get()
            body = post.css(".commentthread_comment_text ::text").getall()
            time = post.css(".commentthread_comment_timestamp ::attr(data-timestamp)").get()
        forum = response.css(".breadcrumbs a:nth-child(1) ::text").get()
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
