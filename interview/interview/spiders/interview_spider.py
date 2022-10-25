import scrapy
import re

SEARCH_WORD='colour'


class InterviewSpider(scrapy.Spider):
    name = "interview"
    start_urls =[f'https://www.merriam-webster.com/dictionary/{SEARCH_WORD}']
       
    def parse(self, response):
        
        cont = response.css('[id="dictionary-entry-1"]')
        british_word = None
        if 'class="cxt text-uppercase">' in cont.get():
            british_word = cont.css('a::text').get()
        
        yield {
            "American Word": SEARCH_WORD,
            "Spelling in British": british_word
        }







