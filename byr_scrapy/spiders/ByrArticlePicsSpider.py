import re
from urllib.request import urlretrieve
import scrapy

from .mysql import MySQL


class ByrArticleSpider(scrapy.Spider):
    name = "byr-article-pics"
    allowed_domains = ["bbs.byr.cn"]
    cookiejar = {}
    db = None
    headers = {'User-Agent': 'Mozilla/5.0', 'Host': 'bbs.byr.cn',
               'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive'}
    pat = r'href=\"(.*?)\" title=\"(.*?)\"'
    article_contents_url_pat = r'article/'
    article_list_url_pat = r'board/'

    start_urls = ['https://bbs.byr.cn/article/Picture/2866254']
    page = 0

    def parse(self, response):
        self.page += 1
        return self.parse_article_pics(response)

    def parse_article_pics(self, response):
        pic_urls = response.css(
            'div.b-content table.article div.a-content-wrap  img.resizeable::attr(src)').extract()
        pic_names = response.css(
            'div.b-content table.article div.a-content-wrap  img.resizeable::attr(alt)').extract()

        for index, pic_url in enumerate(pic_urls):
            url = 'https://bbs.byr.cn' + \
                pic_urls[index] + '/' + pic_names[index]
            print('downloading... ', url)
            urlretrieve(url, 'pics\\' +
                        str(self.page) + '-' + str(index) + '-' + pic_names[index])
            ##
        sel_page = response.css('div.t-pre ul.pagination li ol')
        cur_page_num = sel_page.css('li.page-select > a::text').extract()
        page_list_num = sel_page.css('li.page-normal > a::text').extract()
        page_list_url = sel_page.css(
            'li.page-normal > a::attr(href)').extract()
#         print('cur page is %s' % cur_page_num[0])
        if len(page_list_url) > len(page_list_num):
            pre_page_num = '%d' % (int(cur_page_num[0]) - 1)
            page_list_num.insert(0, pre_page_num)
        for idx, num in enumerate(page_list_num):
            #             print('%d,%s,%s' % (idx, page_list_num[idx], page_list_url[idx]))
            if page_list_num[idx] == '>>':
                next_url = response.urljoin(page_list_url[idx])
#                 print('crawl next article page [%s]' % next_url)
                yield scrapy.Request(next_url, meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.parse)

    def start_requests(self):
        return [scrapy.FormRequest("http://bbs.byr.cn/user/ajax_login.json",
                                   formdata={
                                       'id': '******', 'passwd': '******', 'mode': '0', 'CookieDate': '0'},
                                   meta={'cookiejar': 1},
                                   headers=self.headers,
                                   callback=self.logged_in)]

    def logged_in(self, response):
        self.cookiejar = response.meta['cookiejar']
        for url in self.start_urls:
            yield scrapy.Request(url, meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.parse)
