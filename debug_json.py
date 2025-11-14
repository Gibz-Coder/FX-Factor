#!/usr/bin/env python
"""Debug JSON extraction from ForexFactory HTML."""
import re
import json5

html = open('d:/PythonProject/web_scraper/debug_calendar.html').read()

# Extract just the 'days' array which is the core data
match = re.search(r'days:\s*\[(.*?)\],\s*time:', html, re.DOTALL)
if match:
    days_json = '[' + match.group(1) + ']'
    print(f"Extracted days array, length: {len(days_json)}")
    print(f"First 300 chars: {days_json[:300]}")
    
    try:
        days = json5.loads(days_json)
        print(f"✓ Successfully parsed {len(days)} days with {sum(len(d.get('events', [])) for d in days)} total events")
        for i, day in enumerate(days):
            evt_count = len(day.get('events', []))
            print(f"  Day {i}: {evt_count} events")
            if evt_count > 0:
                evt = day['events'][0]
                print(f"    Example: {evt.get('soloTitle')} ({evt.get('currency')}) - {evt.get('timeLabel')}")
    except Exception as e:
        print(f"✗ Parse error: {e}")
else:
    print("Could not find days array")

