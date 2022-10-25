import scrapy

class LenoxSpider(scrapy.Spider):
    name = 'lenox'
    start_urls = ['https://www.lenoxtools.com/pages/home.aspx']

    def parse(self, response):
        