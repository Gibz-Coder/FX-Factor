"""
ForexFactory Market-Specific News Spider

Scrapes news articles from ForexFactory market pages for specific currency pairs.
Example: https://www.forexfactory.com/market/goldusd

Command:
    scrapy crawl market_news -a pair=GOLDUSD
    scrapy crawl market_news -a pair=EURUSD
"""

import scrapy
from scrapy_playwright.page import PageMethod
import re
from datetime import datetime


class MarketNewsSpider(scrapy.Spider):
    """Scrape news specific to a currency pair from ForexFactory."""

    name = 'market_news'
    allowed_domains = ['forexfactory.com']
    custom_settings = {
        # Use Playwright for this spider; global download handler is set in settings.py
        'PLAYWRIGHT_LAUNCH_ARGS': ['--disable-blink-features=AutomationControlled'],
        'PLAYWRIGHT_ABORT_REQUEST': lambda req: req.resource_type == 'image',
    }

    pair_urls = {
        'EURUSD': 'https://www.forexfactory.com/market/eurusd',
        'GBPUSD': 'https://www.forexfactory.com/market/gbpusd',
        'USDJPY': 'https://www.forexfactory.com/market/usdjpy',
        'GOLDUSD': 'https://www.forexfactory.com/market/goldusd',
        'AUDUSD': 'https://www.forexfactory.com/market/audusd',
        'NZDUSD': 'https://www.forexfactory.com/market/nzdusd',
        'USDCAD': 'https://www.forexfactory.com/market/usdcad',
        'USDCHF': 'https://www.forexfactory.com/market/usdchf',
        'CRUDE': 'https://www.forexfactory.com/market/crude',
        'NATGAS': 'https://www.forexfactory.com/market/natgas',
    }

    def __init__(self, pair='GOLDUSD', *args, **kwargs):
        super(MarketNewsSpider, self).__init__(*args, **kwargs)
        self.pair = pair.upper()
        self.start_urls = [self.pair_urls.get(self.pair, self.pair_urls['GOLDUSD'])]
        self.logger.info(f"Scraping news for pair: {self.pair}")

    def start_requests(self):
        """Generate requests with Playwright."""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        # Wait for main page load, then give JS a moment to populate content
                        PageMethod('wait_for_load_state', 'load'),
                        PageMethod('wait_for_timeout', 5000),  # 5s extra
                    ],
                }
            )

    def parse(self, response):
        """Parse market page for news articles."""
        self.logger.info(f"Parsing news for {self.pair} from {response.url}")

        # DEBUG: save rendered HTML so we can inspect the exact structure (kept for future tuning)
        try:
            debug_path = f"data/market_page_{self.pair.lower()}.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            self.logger.info(f"Saved debug HTML to {debug_path}")
        except Exception as e:
            self.logger.debug(f"Could not save debug HTML: {e}")

        article_count = 0

        # -----------------------------
        # Primary strategy: dedicated parsing for
        # "Hottest Stories" and "Latest Stories" blocks
        # -----------------------------
        flex_blocks = [
            ("Hottest", response.css('div.flexBox.instrumenthottestnews')),
            ("Latest", response.css('div.flexBox.instrumentnews')),
        ]

        for section_type, blocks in flex_blocks:
            for block in blocks:
                section_title = block.css('div.head h2::text').get(default="").strip()
                for story in block.css('ul.body.flexposts > li.flexposts__item'):
                    article = self.extract_flex_story(story, response, section_title)
                    if article:
                        article_count += 1
                        yield article

        # If we found at least one article via the dedicated
        # flexposts parsing, we can stop here. This keeps the
        # output tightly aligned with the pair stories widgets.
        if article_count:
            self.logger.info(f"Extracted {article_count} articles for {self.pair} via flexposts blocks")
            return

        # -----------------------------
        # Fallback strategy: generic container-based extraction
        # (used only if the structure changes and flexposts
        # blocks are not found)
        # -----------------------------
        # Enhanced selectors for ForexFactory market pages
        # Try multiple selector strategies
        news_containers = []

        # Strategy 1: Look for news-specific containers
        news_containers = response.css('div.newsItem, div.news-item, div[class*="news"]')

        # Strategy 2: Look for content boxes
        if not news_containers:
            news_containers = response.css('div.contentBox, div.content-box, div[class*="content"]')

        # Strategy 3: Look for article/post containers
        if not news_containers:
            news_containers = response.css('article, div.post, div[class*="article"]')

        # Strategy 4: Look for table rows (some pages use tables)
        if not news_containers:
            news_containers = response.css('tr[class*="row"], div.row')

        # Strategy 5: Fallback to any div with text content
        if not news_containers:
            self.logger.warning(f"Using fallback selector for {response.url}")
            news_containers = response.css('div')

        self.logger.info(f"Found {len(news_containers)} potential news containers (fallback mode)")

        for container in news_containers[:100]:  # Increased limit to 100
            article = self.extract_article(container, response)
            if article and article.get('title') and len(article.get('title', '')) > 10:
                article_count += 1
                yield article

        self.logger.info(f"Extracted {article_count} articles for {self.pair} (including fallback mode)")


    def extract_flex_story(self, story_sel, response, section_title):
        """Extract a single story from a flexposts (instrument news) item."""
        try:
            link = story_sel.css('div.flexposts__story-title a')
            title = (link.css('::text').get() or "").strip()
            if not title:
                return None

            url = link.attrib.get('href', '')
            if url:
                url = response.urljoin(url)

            # Prefer hidden full preview text where available (Hottest Stories block)
            summary = story_sel.css('p.flexposts__preview span.fader__original::text').get()
            if not summary:
                # Fallback to the anchor's title attribute (often contains extended text)
                summary = link.attrib.get('title', '')
            summary = (summary or "").strip()

            # Source / provider
            source = story_sel.css('span.flexposts__caption a::attr(data-source)').get()
            if not source:
                # Text is typically like "From brecorder.com"; strip the leading word
                source_text = (story_sel.css('span.flexposts__caption a::text').get() or "").strip()
                if source_text.lower().startswith("from "):
                    source = source_text[5:].strip()
                else:
                    source = source_text or None

            # Relative time label (e.g., "5 hr ago") or full timestamp from title attribute
            time_label = (story_sel.css('span.flexposts__time::text').get() or "").strip()
            if not time_label:
                time_label = story_sel.css('span.flexposts__time::attr(title)').get()
                if time_label:
                    time_label = time_label.strip()

            # Impact from explicit storyimpact badge if present (mainly Latest Stories block)
            impact = None
            impact_class = story_sel.css('span.flexposts__storyimpact::attr(class)').get() or ""
            impact_class = impact_class.lower()
            if 'high' in impact_class:
                impact = 'HIGH'
            elif 'medium' in impact_class:
                impact = 'MEDIUM'
            elif 'low' in impact_class:
                impact = 'LOW'

            # Build base article
            base = {
                'pair': self.pair,
                'title': title,
                'url': url,
                'summary': summary,
                'source': source,
                'date': time_label,
                'section': section_title or None,
            }

            # Sentiment and impact using existing helpers
            sentiment = self.detect_sentiment(f"{title}. {summary}")
            base['sentiment'] = sentiment

            if not impact:
                impact = self.detect_impact(f"{title}. {summary}")
            base['impact'] = impact

            return base
        except Exception as e:
            self.logger.debug(f"Error extracting flex story: {e}")
            return None

    def extract_article(self, container, response):
        """Extract article data from a container."""
        try:
            # Enhanced title extraction with multiple strategies
            title = None

            # Strategy 1: Common heading tags
            title = container.css('h1::text, h2::text, h3::text, h4::text, h5::text').get()

            # Strategy 2: Title classes
            if not title:
                title = container.css('.title::text, .headline::text, .heading::text').get()

            # Strategy 3: Strong/bold text (often used for titles)
            if not title:
                title = container.css('strong::text, b::text').get()

            # Strategy 4: First link text (often the title)
            if not title:
                title = container.css('a::text').get()

            # Strategy 5: Aggregate all text and take first meaningful chunk
            if not title:
                all_text = container.css('::text').getall()
                all_text = [t.strip() for t in all_text if t.strip() and len(t.strip()) > 15]
                if all_text:
                    title = all_text[0][:200]

            # Skip if no valid title found
            if not title or len(title.strip()) < 10:
                return None

            # Enhanced date/time extraction
            date_str = None

            # Try datetime attribute
            date_str = container.css('time::attr(datetime)').get()

            # Try date/time classes
            if not date_str:
                date_str = container.css('[class*="date"]::text, [class*="time"]::text').get()

            # Try regex patterns for dates
            if not date_str:
                date_str = container.css('::text').re_first(
                    r'\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}|\d+ (hour|minute|day)s? ago'
                )

            # Default to current time if no date found
            if not date_str:
                date_str = datetime.now().strftime('%Y-%m-%d %H:%M')

            # Enhanced summary extraction
            summary_parts = []

            # Get paragraph text
            summary_parts.extend(container.css('p::text').getall())

            # Get div text content
            summary_parts.extend(container.css('div.summary::text, div.content::text, div.description::text').getall())

            # Get span text
            summary_parts.extend(container.css('span::text').getall())

            # Clean and join
            summary_parts = [s.strip() for s in summary_parts if s.strip() and len(s.strip()) > 20]
            summary = ' '.join(summary_parts[:3])[:600]  # Increased to 600 chars

            # If no summary, use title as summary
            if not summary:
                summary = title

            # Enhanced link extraction
            link = container.css('a::attr(href)').get('')
            if link:
                if not link.startswith('http'):
                    link = response.urljoin(link)
            else:
                link = response.url

            # Detect sentiment keywords
            sentiment = self.detect_sentiment(title + ' ' + summary)

            # Detect impact level
            impact = self.detect_impact(title + ' ' + summary)

            # Extract additional metadata
            article = {
                'pair': self.pair,
                'title': title.strip(),
                'summary': summary.strip(),
                'url': link,
                'date': date_str,
                'timestamp': datetime.now().isoformat(),
                'sentiment': sentiment,
                'impact': impact,
                'source': 'ForexFactory Market',
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }

            return article

        except Exception as e:
            self.logger.debug(f"Error extracting article: {e}")
            return None

    def detect_sentiment(self, text):
        """Detect sentiment from text keywords."""
        text_lower = text.lower()

        bullish_keywords = [
            'surge', 'rally', 'gain', 'rise', 'bull', 'strong', 'bullish',
            'positive', 'upbeat', 'optimism', 'good', 'improvement', 'boost',
            'support', 'recovery', 'strength', 'break higher', 'above',
        ]

        bearish_keywords = [
            'crash', 'fall', 'decline', 'bear', 'weak', 'bearish', 'negative',
            'pessimism', 'bad', 'concern', 'pressure', 'drop', 'dump', 'sell',
            'weakness', 'below', 'break lower', 'plunge',
        ]

        bullish_score = sum(1 for kw in bullish_keywords if kw in text_lower)
        bearish_score = sum(1 for kw in bearish_keywords if kw in text_lower)

        if bullish_score > bearish_score:
            return 'BULLISH'
        elif bearish_score > bullish_score:
            return 'BEARISH'
        else:
            return 'NEUTRAL'

    def detect_impact(self, text):
        """Detect market impact level."""
        text_lower = text.lower()

        high_impact_keywords = [
            'fed', 'ecb', 'boe', 'interest rate', 'fomc', 'gdp', 'inflation',
            'employment', 'crisis', 'emergency', 'urgent', 'significant', 'major',
            'breaking', 'shock', 'surprise', 'unexpected',
        ]

        medium_impact_keywords = [
            'data', 'report', 'release', 'announcement', 'statement', 'commentary',
            'update', 'change', 'adjustment',
        ]

        high_impact_count = sum(1 for kw in high_impact_keywords if kw in text_lower)
        medium_impact_count = sum(1 for kw in medium_impact_keywords if kw in text_lower)

        if high_impact_count >= 2:
            return 'HIGH'
        elif medium_impact_count >= 1:
            return 'MEDIUM'
        else:
            return 'LOW'
