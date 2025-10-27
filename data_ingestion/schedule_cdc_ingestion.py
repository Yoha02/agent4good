"""
Schedule CDC NREVSS data ingestion to run automatically.

RECOMMENDED CADENCE: Weekly (CDC updates data weekly)
Alternative: Daily if you want to ensure fresh data

To run hourly (NOT RECOMMENDED - wasteful):
  - Windows: Use Task Scheduler
  - Linux/Mac: Use cron
  - Cloud: Use Google Cloud Scheduler

This script sets up the schedule using Python's schedule library.
"""

import schedule
import time
import subprocess
import os
from datetime import datetime

# Path to the ingestion script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INGESTION_SCRIPT = os.path.join(SCRIPT_DIR, 'fetch_cdc_nrevss.py')
PYTHON_EXE = os.path.join(SCRIPT_DIR, '..', '.venv', 'Scripts', 'python.exe')

def run_ingestion():
    """Run the CDC NREVSS data ingestion script"""
    print(f"\n{'='*80}")
    print(f"[{datetime.now().isoformat()}] Starting scheduled CDC NREVSS ingestion...")
    print(f"{'='*80}\n")
    
    try:
        # Run the ingestion script
        result = subprocess.run(
            [PYTHON_EXE, INGESTION_SCRIPT],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"\n[{datetime.now().isoformat()}] ✓ Ingestion completed successfully")
        else:
            print(f"\n[{datetime.now().isoformat()}] ✗ Ingestion failed with code {result.returncode}")
    
    except subprocess.TimeoutExpired:
        print(f"\n[{datetime.now().isoformat()}] ✗ Ingestion timed out after 5 minutes")
    except Exception as e:
        print(f"\n[{datetime.now().isoformat()}] ✗ Ingestion error: {e}")

def main():
    """Main scheduler function"""
    print("="*80)
    print("CDC NREVSS Data Ingestion Scheduler")
    print("="*80)
    print(f"Script location: {INGESTION_SCRIPT}")
    print(f"Python executable: {PYTHON_EXE}")
    
    # RECOMMENDED: Run weekly on Sunday at 2 AM
    schedule.every().sunday.at("02:00").do(run_ingestion)
    print("\n✓ Scheduled: Every Sunday at 2:00 AM (RECOMMENDED)")
    
    # ALTERNATIVE: Run daily at 3 AM
    # Uncomment the line below if you want daily updates instead
    # schedule.every().day.at("03:00").do(run_ingestion)
    # print("\n✓ Scheduled: Every day at 3:00 AM")
    
    # HOURLY (NOT RECOMMENDED - CDC only updates weekly)
    # Uncomment the line below if you really want hourly updates
    # schedule.every().hour.do(run_ingestion)
    # print("\n✓ Scheduled: Every hour (NOT RECOMMENDED)")
    
    # Run once immediately on startup
    print("\n[INFO] Running initial ingestion now...")
    run_ingestion()
    
    # Keep the scheduler running
    print(f"\n{'='*80}")
    print("Scheduler is running... Press Ctrl+C to stop")
    print(f"{'='*80}\n")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user.")
