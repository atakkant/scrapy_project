# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html


from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.utils.python import to_bytes
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
import time
import pyautogui
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
import logging

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


def infinite_scroll_down(driver,height,count=0):
    total_height = int(driver.execute_script("return document.body.scrollHeight"))
    scroll_height = int(total_height/5)
    for i in range(1, total_height, scroll_height):
        driver.execute_script("window.scrollTo(0, {});".format(i))
        time.sleep(2)

    new_height = int(driver.execute_script("return document.body.scrollHeight"))
    print("actual height: %d"%new_height)
    count += 1
    if total_height != new_height:
        infinite_scroll_down(driver,new_height,count)
    else:
        print("end of scroll. Number of pages: %d"%count)
        return


class SeleniumMiddleware(object):

    def __init__(self):
        self.drivers = {}

    @classmethod
    def from_crawler(cls,crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed,signals.spider_closed)
        return middleware


    def process_request(self,request,spider):
        print("inside process request")

        try:
            options = Options()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument("--test-type")
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument("disable-infobars")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--remote-debugging-port=9230")
            options.add_argument("--disable-setuid-sandbox")
            #options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

            #options.binary_location = "/home/atakantuncer/Desktop/scrapy_project/webscraping/webscraping/chromedriver"
            self.drivers[request.url] = webdriver.Chrome(chrome_options=options) #ChromeDriverManager(version="95.0.4638.69").install(),
            self.drivers[request.url].maximize_window()
            self.drivers[request.url].get(request.url)
            wait_at_open = spider.wait_at_open
            time.sleep(wait_at_open)

            last_height = self.drivers[request.url].execute_script('return document.body.scrollHeight')
            print("last_height: %d"%last_height)
            scroll = spider.scroll
            if scroll == 'inf':
                infinite_scroll_down(self.drivers[request.url],last_height)


            body = to_bytes(self.drivers[request.url].page_source)
            current_url = self.drivers[request.url].current_url

        except Exception as e:
            print("driver couldn't be initiated for %s"%request.url)
            print(e)
            current_url = self.drivers[request.url].current_url

        self.drivers[request.url].stop_client()
        self.drivers[request.url].close()
        self.drivers[request.url].quit()

        return HtmlResponse(current_url,body=body,encoding='utf-8',request=request)

    def spider_opened(self,spider):
        print('Selenium spider is opened %s'%spider.name)

    def spider_closed(self,spider):
        print('Selenium spider is closed %s'%spider.name)

        #WebDriverWait(self.driver, 5)



class WebscrapingSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class WebscrapingDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
