#!/usr/bin/env python
"""Inspect ForexFactory HTML structure via Playwright for selector debugging."""
import asyncio
from playwright.async_api import async_playwright


async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate and wait for calendar to load
        await page.goto('https://www.forexfactory.com/calendar.php', wait_until='networkidle')
        await page.wait_for_selector('table, tr', timeout=10000)

        # Get first 3 rows to inspect
        html = await page.content()
        
        # Save full HTML for inspection
        with open('d:/PythonProject/web_scraper/debug_calendar.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print("✓ Full HTML saved to debug_calendar.html")

        # Get first few table rows and print their HTML
        rows = await page.locator('tr').all()
        print(f"Total rows found: {len(rows)}")
        print("\n--- First 3 rows HTML ---")
        for i, row in enumerate(rows[:3]):
            html_content = await row.inner_html()
            print(f"\nRow {i}:\n{html_content[:500]}...\n")

        # Try to get cell counts
        first_row_cells = await rows[0].locator('td').all() if rows else []
        print(f"Cells in first row: {len(first_row_cells)}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(inspect())
