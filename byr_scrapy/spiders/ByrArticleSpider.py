import re

import scrapy

from .mysql import MySQL


class ByrArticleSpider(scrapy.Spider):
    name = "byr-article"
    allowed_domains = ["bbs.byr.cn"]
    cookiejar = {}
    db = None
    headers = {'User-Agent': 'Mozilla/5.0', 'Host': 'bbs.byr.cn',
               'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive'}
    pat = r'href=\"(.*?)\" title=\"(.*?)\"'
    article_contents_url_pat = r'article/'
    article_list_url_pat = r'board/'

    def parse(self, response):
        cur_page_url = response._get_url()
        if re.search(self.article_list_url_pat, cur_page_url, re.I):
            return self.parse_article_list(response)

        elif re.search(self.article_contents_url_pat, cur_page_url, re.I):
            return self.parse_article_contents(response)
        else:
            print('pass this page')

    def parse_article_list(self, response):
        cur_page_url = response._get_url()
        sel_article = response.css('div.b-content tbody tr')
        sel_article_a = sel_article.css('td.title_9 >a')
        article_url = sel_article_a.css('::attr(href)').extract()
        article_title = sel_article_a.css('::text').extract()
        article_time = sel_article.css('td.title_10::text').extract()
        article_author = sel_article.css('td.title_12 >a::text').extract()
        article_hot = sel_article.css('td.title_11::text').extract()

        sel_page = response.css('ul.pagination li ol')
        cur_page_num = sel_page.css('li.page-select > a::text').extract()
        page_list_num = sel_page.css('li.page-normal > a::text').extract()
        page_list_url = sel_page.css(
            'li.page-normal > a::attr(href)').extract()
        for index, url in enumerate(article_url):
            next_url = response.urljoin(article_url[index])
            self.store_data({'uptime': article_time[index], 'hot': article_hot[index],
                             'title': article_title[index], 'author': article_author[index * 2],
                             'url': next_url, 'table': 'article_list'})
            yield scrapy.Request(next_url, meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.parse)

        print('cur page is %s' % cur_page_num[0])
        if len(page_list_url) > len(page_list_num):
            pre_page_num = '%d' % (int(cur_page_num[0]) - 1)
            page_list_num.insert(0, pre_page_num)
        for index, num in enumerate(page_list_num):
            if page_list_num[index] == '>>':
                next_url = response.urljoin(page_list_url[index])
                yield scrapy.Request(next_url, meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.parse)

    def parse_article_contents(self, response):
        cur_page_url = response._get_url()
        text = response.css(
            'div.b-content table.article div.a-content-wrap ::text').extract()
        self.store_data(
            {'text': text, 'url': cur_page_url, 'table': 'article'})
#         ##
#         sel_page = response.css('div.t-pre ul.pagination li ol')
#         cur_page_num = sel_page.css('li.page-select > a::text').extract()
#         page_list_num = sel_page.css('li.page-normal > a::text').extract()
#         page_list_url = sel_page.css(
#             'li.page-normal > a::attr(href)').extract()
#         print('cur page is %s' % cur_page_num[0])
#         if len(page_list_url) > len(page_list_num):
#             pre_page_num = '%d' % (int(cur_page_num[0]) - 1)
#             page_list_num.insert(0, pre_page_num)
#         for index, num in enumerate(page_list_num):
#             print('%d,%s,%s' %
#                   (index, page_list_num[index], page_list_url[index]))
#             if page_list_num[index] == '>>':
#                 next_url = response.urljoin(page_list_url[index])
#                 print('crawl next article page [%s]' % next_url)
# yield scrapy.Request(next_url, meta={'cookiejar':
# response.meta['cookiejar']}, headers=self.headers, callback=self.parse)

    def start_requests(self):
        self.db = MySQL(
            '127.0.0.1', '******', '******', 'byr', 3306, 'utf8', 5, '')
        return [scrapy.FormRequest("http://bbs.byr.cn/user/ajax_login.json",
                                   formdata={
                                       'id': '******', 'passwd': '******', 'mode': '0', 'CookieDate': '0'},
                                   meta={'cookiejar': 1},
                                   headers=self.headers,
                                   callback=self.logged_in)]

    def logged_in(self, response):
        #         print('\n\n', response.body_as_unicode(), '\n\n')
        self.cookiejar = response.meta['cookiejar']
        self.start_urls = self.load_start_url()
        for url in self.start_urls:
            yield scrapy.Request(url, meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.parse)

    def store_data(self, data):
        if data['table'] == 'article_list':
            sql = "insert into article_list(uptime, hot, author, title, url) values ('%s',%s,'%s','%s','%s')" % (
                data['uptime'], data['hot'], data['author'], data['title'], data['url'])
        else:
            sql = "insert into article(url,text) values ('%s', '%s')" % (
                data['url'], data['text'])
        # print 'sql is [%s]' % sql;
        try:
            self.db.update(sql)
        except:
            print('update failed')

    def load_start_url(self):
        sql = 'select url from section'
        rows = self.db.query(sql)
        for row in rows:
            yield 'http://bbs.byr.cn' + row[0]
