"""
Background scheduler for real-time data refresh.

Runs scheduled tasks to:
- Refresh economic calendar every 30 minutes
- Fetch latest news every 15 minutes
- Update price data every 5 minutes
"""

import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)

class ForexDataScheduler:
    """Manages background data refresh tasks."""
    
    def __init__(self, python_path='C:/Python312/python.exe', project_path=None):
        self.python_path = python_path
        self.project_path = project_path or Path(__file__).parent
        self.scheduler = BackgroundScheduler()
        self.last_updates = {}
    
    def refresh_calendar(self):
        """Refresh economic calendar data."""
        try:
            logger.info("Starting calendar refresh...")
            cmd = [
                self.python_path, 
                '-m', 'scrapy', 'crawl', 'economic_calendar',
                '-a', 'timezone=Asia/Manila',
                '-o', 'data/calendar_latest.jsonl'
            ]
            result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info("✓ Calendar refresh completed")
                self.last_updates['calendar'] = datetime.now().isoformat()
                self._save_update_log()
            else:
                logger.error(f"Calendar refresh failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error refreshing calendar: {e}")
    
    def refresh_news(self):
        """Refresh news data."""
        try:
            logger.info("Starting news refresh...")
            cmd = [
                self.python_path,
                '-m', 'scrapy', 'crawl', 'news',
                '-o', 'data/news_latest.jsonl'
            ]
            result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info("✓ News refresh completed")
                self.last_updates['news'] = datetime.now().isoformat()
                self._save_update_log()
            else:
                logger.error(f"News refresh failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error refreshing news: {e}")
    
    def refresh_market_news(self, pair='GOLDUSD'):
        """Refresh pair-specific market news."""
        try:
            logger.info(f"Starting market news refresh for {pair}...")
            cmd = [
                self.python_path,
                '-m', 'scrapy', 'crawl', 'market_news',
                '-a', f'pair={pair}',
                '-O', f'data/market_news_{pair.lower()}.jsonl'  # overwrite instead of append
            ]
            result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info(f"✓ Market news refresh for {pair} completed")
                self.last_updates[f'market_news_{pair}'] = datetime.now().isoformat()
                self._save_update_log()
            else:
                logger.error(f"Market news refresh for {pair} failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error refreshing market news for {pair}: {e}")
    
    def refresh_prices(self):
        """Refresh market price data."""
        try:
            logger.info("Starting price refresh...")
            cmd = [self.python_path, 'run.py', '--pairs', 'EURUSD,GBPUSD,USDJPY,GOLDUSD']
            result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info("✓ Price refresh completed")
                self.last_updates['prices'] = datetime.now().isoformat()
                self._save_update_log()
            else:
                logger.warning(f"Price refresh had issues: {result.stderr[:200]}")
        except Exception as e:
            logger.error(f"Error refreshing prices: {e}")
    
    def _save_update_log(self):
        """Save last update times to file."""
        log_file = self.project_path / 'data' / 'refresh_log.json'
        log_file.parent.mkdir(exist_ok=True)
        try:
            with open(log_file, 'w') as f:
                json.dump(self.last_updates, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving update log: {e}")
    
    def start(self):
        """Start the background scheduler."""
        logger.info("="*60)
        logger.info("Starting Forex Data Scheduler")
        logger.info("="*60)
        
        # Schedule tasks
        self.scheduler.add_job(
            self.refresh_calendar,
            trigger=IntervalTrigger(minutes=30),
            id='refresh_calendar',
            name='Refresh Economic Calendar',
            replace_existing=True
        )
        logger.info("✓ Scheduled: Calendar refresh every 30 minutes")
        
        self.scheduler.add_job(
            self.refresh_news,
            trigger=IntervalTrigger(minutes=15),
            id='refresh_news',
            name='Refresh News',
            replace_existing=True
        )
        logger.info("✓ Scheduled: News refresh every 15 minutes")
        
        # Schedule market-specific news refresh for multiple pairs
        pairs_to_monitor = ['GOLDUSD', 'EURUSD', 'GBPUSD', 'USDJPY']
        for pair in pairs_to_monitor:
            self.scheduler.add_job(
                self.refresh_market_news,
                trigger=IntervalTrigger(minutes=10),
                id=f'refresh_market_news_{pair}',
                name=f'Refresh Market News - {pair}',
                kwargs={'pair': pair},
                replace_existing=True
            )
        logger.info(f"✓ Scheduled: Market news refresh every 10 minutes for {len(pairs_to_monitor)} pairs")
        
        self.scheduler.add_job(
            self.refresh_prices,
            trigger=IntervalTrigger(minutes=5),
            id='refresh_prices',
            name='Refresh Prices',
            replace_existing=True
        )
        logger.info("✓ Scheduled: Price refresh every 5 minutes")
        
        # Start scheduler
        self.scheduler.start()
        logger.info("="*60)
        logger.info("Scheduler running in background")
        logger.info("="*60)
    
    def stop(self):
        """Stop the background scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def get_status(self):
        """Get scheduler status."""
        return {
            'running': self.scheduler.running,
            'jobs': len(self.scheduler.get_jobs()),
            'last_updates': self.last_updates
        }
    
    def run_forever(self):
        """Run scheduler indefinitely."""
        try:
            self.start()
            logger.info("Press Ctrl+C to stop")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
            self.stop()


if __name__ == '__main__':
    scheduler = ForexDataScheduler()
    scheduler.run_forever()
