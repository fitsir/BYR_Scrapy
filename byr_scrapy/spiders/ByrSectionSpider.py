import re

import scrapy
from .mysql import MySQL


class ByrSectionSpider(scrapy.Spider):
    name = "byr-section"
    allowed_domains = ["bbs.byr.cn"]
    cookiejar = {}
    db = None
    headers = {'User-Agent': 'Mozilla/5.0', 'Host': 'bbs.byr.cn',
               'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive'}
    pat = r'href=\"(.*?)\" title=\"(.*?)\"'
    section_pat = r'^/section/(.*?)$'

    start_urls = ['http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-0',
                  'http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-1',
                  'http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-2',
                  'http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-3',
                  'http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-4',
                  'http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-5',
                  'http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-6',
                  'http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-7',
                  'http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-8',
                  'http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-9']

    def parse(self, response):
        body = response.body_as_unicode()
        try:
            data = body.replace(r'\"', '"')
            results = re.findall(self.pat, data, re.I)
            for result in results:
                url = result[0]
                title = result[1]
                print('url [%s], title [%s]' % (url, title))
                rs = re.findall(self.section_pat, url, re.I)
                if rs:
                    nurl = 'http://bbs.byr.cn/section/ajax_list.json?uid=ae&root=sec-%s' % rs[
                        0]
                    print(nurl)
                    yield scrapy.Request(nurl, meta={'cookiejar': self.cookiejar}, headers=self.headers, callback=self.parse)
                else:
                    self.store_data({'url': url, 'name': title})
        except:
            print('parse json [%s] failed' % body)

    def parse_content(self, response):
        pass

    def start_requests(self):
        self.db = MySQL(
            '127.0.0.1', 'fitsir', '870606', 'byr', 3306, 'utf8', 5, '')
        return [scrapy.FormRequest("http://bbs.byr.cn/user/ajax_login.json",
                                   formdata={
                                       'id': 'ae', 'passwd': '870606', 'mode': '0', 'CookieDate': '0'},
                                   meta={'cookiejar': 1},
                                   headers=self.headers,
                                   callback=self.logged_in)]

    def logged_in(self, response):
        print('\n\n', response.body_as_unicode(), '\n\n')
        self.cookiejar = response.meta['cookiejar']
        for url in self.start_urls:
            yield scrapy.Request(url, meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.parse)

    def store_data(self, data):
        sql = "insert into section(url, name) values ('%s', '%s')" % (
            data['url'], data['name'])
        self.db.update(sql)
