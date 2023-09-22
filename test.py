from scrapy.http import HtmlResponse
import requests
import re
import time


def is_sorted(lst):
    return all(lst[i] <= lst[i+1] for i in range(len(lst)-1)) or all(lst[i] >= lst[i+1] for i in range(len(lst)-1))


def main():
    base_url = "https://steamcommunity.com/discussions/forum/24/537405286646015181/?ctp="
    result = []
    for i in range(1, 20):
        url = base_url + str(i)
        resp = requests.get(url)
        resp = HtmlResponse(url, body=resp.content)
        ids = resp.css(".commentthread_comment").getall()
        ids = [re.search("_[0-9]*", re.search('id="comment_[0-9]*', id_)[0])[0][1:] for id_ in ids]
        result += ids
        time.sleep(1)
    print(result)
    print(is_sorted(result))


if __name__ == "__main__":
    main()
