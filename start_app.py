"""
Start Forex Trading Dashboard with Background Scheduler

This script launches:
1. Streamlit dashboard on http://localhost:8501
2. Background scheduler for data refresh (calendar, news, prices)

Usage:
    python start_app.py
"""

import subprocess
import time
import sys
import logging
from pathlib import Path
import signal
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)

class ForexAppManager:
    """Manages both dashboard and scheduler processes."""
    
    def __init__(self, python_path='C:/Python312/python.exe'):
        self.python_path = python_path
        self.dashboard_process = None
        self.scheduler_process = None
    
    def start_dashboard(self):
        """Start Streamlit dashboard."""
        logger.info("Starting Streamlit Dashboard...")
        try:
            self.dashboard_process = subprocess.Popen(
                [self.python_path, '-m', 'streamlit', 'run', 'dashboard.py', '--logger.level=error'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("✓ Dashboard started on http://localhost:8501")
            return True
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")
            return False
    
    def start_scheduler(self):
        """Start background scheduler."""
        logger.info("Starting Background Scheduler...")
        try:
            self.scheduler_process = subprocess.Popen(
                [self.python_path, 'scheduler.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(2)  # Give scheduler time to start
            logger.info("✓ Scheduler started (calendar every 30min, news every 15min, prices every 5min)")
            return True
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            return False
    
    def start_all(self):
        """Start both dashboard and scheduler."""
        logger.info("="*70)
        logger.info("FOREX TRADING DASHBOARD - Production Mode")
        logger.info("="*70)
        
        success = True
        success = self.start_scheduler() and success
        time.sleep(3)
        success = self.start_dashboard() and success
        
        if success:
            logger.info("="*70)
            logger.info("✓ All services started successfully!")
            logger.info("="*70)
            logger.info("")
            logger.info("Dashboard:  http://localhost:8501")
            logger.info("Logs:       logs/scheduler.log")
            logger.info("")
            logger.info("Background tasks:")
            logger.info("  • Economic calendar refresh: every 30 minutes")
            logger.info("  • News articles refresh:     every 15 minutes")
            logger.info("  • Price data refresh:        every 5 minutes")
            logger.info("")
            logger.info("Press Ctrl+C to stop all services")
            logger.info("="*70)
        
        return success
    
    def stop_all(self):
        """Stop both processes."""
        logger.info("Stopping all services...")
        
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=5)
                logger.info("✓ Dashboard stopped")
            except:
                self.dashboard_process.kill()
                logger.info("✓ Dashboard killed")
        
        if self.scheduler_process:
            try:
                self.scheduler_process.terminate()
                self.scheduler_process.wait(timeout=5)
                logger.info("✓ Scheduler stopped")
            except:
                self.scheduler_process.kill()
                logger.info("✓ Scheduler killed")
        
        logger.info("All services stopped")
    
    def monitor(self):
        """Monitor both processes."""
        try:
            while True:
                # Check if processes are still running
                if self.dashboard_process and self.dashboard_process.poll() is not None:
                    logger.warning("Dashboard process died, restarting...")
                    self.start_dashboard()
                
                if self.scheduler_process and self.scheduler_process.poll() is not None:
                    logger.warning("Scheduler process died, restarting...")
                    self.start_scheduler()
                
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("\nShutdown requested")
            self.stop_all()
            sys.exit(0)


if __name__ == '__main__':
    manager = ForexAppManager()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start everything
    if manager.start_all():
        manager.monitor()
    else:
        logger.error("Failed to start services")
        sys.exit(1)
