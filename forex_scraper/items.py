import scrapy


class NewsItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    date = scrapy.Field()
    source = scrapy.Field()
    summary = scrapy.Field()
    text = scrapy.Field()
    sentiment = scrapy.Field()


class EventItem(scrapy.Item):
    time = scrapy.Field()
    currency = scrapy.Field()
    importance = scrapy.Field()
    event = scrapy.Field()
    forecast = scrapy.Field()
    previous = scrapy.Field()
