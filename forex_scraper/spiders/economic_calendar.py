import scrapy
from ..items import EventItem


class EconCalendarSpider(scrapy.Spider):
    """Scrape ForexFactory economic calendar.

    This spider uses Playwright (via scrapy-playwright) to render the page because the
    calendar is dynamically loaded. It yields `EventItem` objects for rows found.
    """
    name = 'economic_calendar'
    allowed_domains = ['forexfactory.com']
    start_urls = ['https://www.forexfactory.com/calendar.php']

    def start_requests(self):
        for url in self.start_urls:
            # use Playwright to render the JS-heavy calendar
            # Build a list of Playwright page methods to run before scraping.
            pm = []
            # wait for calendar container
            pm.append({"method": "wait_for_selector", "args": ["table#calendar, div.calendar__table, table.calendar", {"timeout": 10000}]})

            # If the spider was given a timezone or country via -a, attempt to set them on the page.
            tz = getattr(self, 'timezone', None)
            country = getattr(self, 'country', None)
            day = getattr(self, 'day', None)

            if tz:
                # Try several variants of the timezone label (full, short, replace '_' with ' ', last segment).
                # The script will attempt to set a <select> if present, else click a matching link/button.
                js = "(tz) => { const variants = []; variants.push(tz); try{ const parts = tz.split('/'); if(parts.length>1) variants.push(parts[parts.length-1]); }catch(e){} variants.push(tz.replace('_',' ')); variants.push(tz.replace('/',' ')); for (const v of variants){ const sel = document.querySelector('select#timezone, select[name=timezone]'); if (sel){ const opt = Array.from(sel.options).find(o=> (o.textContent||'').toLowerCase().includes(v.toLowerCase()) || (o.value||'').toLowerCase().includes(v.toLowerCase())); if(opt){ sel.value = opt.value; sel.dispatchEvent(new Event('change')); return v; } } const btn = Array.from(document.querySelectorAll('a,button,li,span')).find(e=>e.textContent&&e.textContent.toLowerCase().includes(v.toLowerCase())); if (btn){ btn.click(); return v; } } return false; }"
                pm.append({"method": "evaluate", "args": [js, tz]})
                pm.append({"method": "wait_for_timeout", "args": [900]})

            if country:
                js_c = "(c) => { const sel = document.querySelector('select#country, select[name=country]'); if (sel) { sel.value = c; sel.dispatchEvent(new Event('change')); return true; } const els = Array.from(document.querySelectorAll('a,button,li')).filter(e=>e.textContent&&e.textContent.trim().toLowerCase().includes(c.toLowerCase())); if(els.length){ els[0].click(); return true;} return false; }"
                pm.append({"method": "evaluate", "args": [js_c, country]})
                pm.append({"method": "wait_for_timeout", "args": [800]})

            if day:
                # day can be 'today','tomorrow','this-week' etc. Try to click a matching link/button or set query param.
                js_d = "(d) => { const link = Array.from(document.querySelectorAll('a,button')).find(x=>x.textContent&&x.textContent.toLowerCase().includes(d)); if(link){ link.click(); return true;} return false; }"
                pm.append({"method": "evaluate", "args": [js_d, day]})
                pm.append({"method": "wait_for_timeout", "args": [600]})

            # finally ensure rows are present
            pm.append({"method": "wait_for_selector", "args": ["tr[class*='calendar__row'], tr.calendar_row", {"timeout": 10000}]})

            yield scrapy.Request(url, meta={"playwright": True, "playwright_page_methods": pm})

    def parse(self, response):
        """Parse calendar events from embedded JavaScript in the page."""
        import json5
        import re

        # ForexFactory embeds calendar data as a JavaScript object in window.calendarComponentStates[1].
        # The key data is in the 'days' array which contains event objects for each day.
        # Extract just the days array to simplify parsing.
        
        match = re.search(r'days:\s*\[(.*?)\],\s*time:', response.text, re.DOTALL)
        if not match:
            self.logger.warning("Could not find days array in calendar data.")
            return

        # Extract the days array and wrap it in brackets for valid JSON5
        days_content = match.group(1)
        days_json = '[' + days_content + ']'
        
        try:
            days = json5.loads(days_json)
        except Exception as e:
            self.logger.error(f"Failed to parse calendar days array: {e}")
            return

        self.logger.info(f"Found {len(days)} day(s) of events")
        
        total_events = 0
        for day_obj in days:
            events = day_obj.get('events', [])
            total_events += len(events)
            for evt in events:
                item = EventItem()
                # Map event fields from the JavaScript object to item fields
                item['time'] = evt.get('timeLabel') or None
                item['currency'] = evt.get('currency') or None
                item['importance'] = evt.get('impactTitle') or None
                item['event'] = evt.get('soloTitle') or evt.get('name') or None
                item['forecast'] = evt.get('forecast') or None
                item['previous'] = evt.get('previous') or None
                yield item
        
        self.logger.info(f"Extracted {total_events} total events")
