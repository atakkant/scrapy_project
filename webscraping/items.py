# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WebscrapingItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()
    description = scrapy.Field()
    specs = scrapy.Field()
    highlights = scrapy.Field()
    questions = scrapy.Field()
    images_url = scrapy.Field()
