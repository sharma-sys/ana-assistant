"""
One-time script to run DistrictNewsCollector and populate district news in the DB.
Run with: python run_district_collector.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.session import SessionLocal
from collectors.district_news import DistrictNewsCollector

def main():
    db = SessionLocal()
    try:
        print("Starting DistrictNewsCollector...")
        collector = DistrictNewsCollector(db)
        result = collector.run()
        print(f"Done! Result: {result}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
