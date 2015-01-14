import scrapy
from moodle.items import MoodleItem
import re
import os

class moodleSpider(scrapy.Spider):
    name = "moodle"
    start_urls = [
            "http://10.1.1.242/moodle/login/index.php"
            ]

    def parse(self, response):
        username = raw_input('Enter Username: ')
        password = raw_input('Enter Password: ')
        return scrapy.FormRequest(
                'http://10.1.1.242/moodle/login/index.php',
                formdata={'username': username, 'password': password},
                callback=self.parseIndex)

    def parseIndex(self, response):
        # check login succeed before going on
        if "Invalid login" in response.body:
            self.log("Login failed", level=scrapy.log.ERROR)
            return
        print("Login Successful")
        print(response.xpath("//div[@class='course_title']/h2/a"))
        for sel in response.xpath("//div[@class='course_title']/h2/a"):
            #Clear cookies
            request = scrapy.http.Request(sel.xpath('@href').extract()[0], callback=self.parseCourse)
            request.meta['course']= sel.xpath('text()').extract()[0]
            if not os.path.exists(request.meta['course']):
                os.makedirs(request.meta['course'])
            yield request

    def parseCourse(self, response):
        #scrapy.shell.inspect_response(response)
        for sel in response.xpath("//li[contains(concat(' ',normalize-space(@class),' '),'modtype_resource')]/div/div/a"):
            request = scrapy.http.Request(sel.xpath('@href').extract()[0], callback=self.parseFile)
            request.meta['course']=response.meta['course']
            yield request

    def parseFile(self, response):
        #scrapy.shell.inspect_response(response)
        item = MoodleItem()
        item['course'] = response.meta['course']
        if response.headers['Content-Type'] == "text/html; charset=utf-8":            
            item['link'] = response.xpath('//object/@data').extract()[0]
            item['fileName'] = re.search('(?:/)([^/\?]+)($|(?:\?))', item['link'] ).group(1)
            request = scrapy.http.Request(item['link'], callback=self.parseFile)
            request.meta['course']=response.meta['course']
            yield(request)
        else:
            item['link'] = response.url
            item['fileName'] = re.search('(?:/)([^/\?]+)($|(?:\?))', item['link'] ).group(1)
            with open('downloads/' + item['course'] + '/' + item['fileName'], "wb") as f:
                f.write(response.body)
            yield item


