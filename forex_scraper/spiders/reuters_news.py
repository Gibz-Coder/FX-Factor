import scrapy
from ..items import NewsItem


class ReutersNewsSpider(scrapy.Spider):
    name = 'reuters_news'
    allowed_domains = ['reuters.com']
    start_urls = ['https://www.reuters.com/markets/']

    def parse(self, response):
        # This selector is intentionally simple and may need adjustments for site changes
        for article in response.css('article'):
            title = article.css('h3::text, h2::text').get()
            url = article.css('a::attr(href)').get()
            if not url:
                continue
            if url.startswith('/'):
                url = response.urljoin(url)

            item = NewsItem()
            item['title'] = title.strip() if title else None
            item['url'] = url
            item['source'] = 'reuters'
            item['date'] = article.css('time::attr(datetime)').get()
            # brief summary if available
            item['summary'] = article.css('p::text').get()
            yield scrapy.Request(url, callback=self.parse_article, meta={'item': item})

    def parse_article(self, response):
        item = response.meta['item']
        paragraphs = response.css('div.ArticleBody__content__17Yit p::text').getall()
        if not paragraphs:
            # fallback selectors
            paragraphs = response.css('p::text').getall()
        text = '\n'.join([p.strip() for p in paragraphs if p.strip()])
        item['text'] = text
        yield item
