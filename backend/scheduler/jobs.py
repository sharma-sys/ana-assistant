# pyrefly: ignore [missing-import]
from apscheduler.schedulers.background import BackgroundScheduler
from database.session import SessionLocal
from collectors.hindi_news import HindiNewsCollector
from collectors.district_news import DistrictNewsCollector
from collectors.gov_news import GovernmentNewsCollector
from collectors.police_news import PoliceNewsCollector
from collectors.pib_news import PibNewsCollector
from collectors.national_news import NationalNewsCollector
from collectors.state_news import StateNewsCollector
from collectors.rss import GenericRssCollector
from collectors.google_news import GoogleNewsCollector
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_collector(collector_class, name):
    logger.info(f"Starting {name}...")
    db = SessionLocal()
    try:
        collector = collector_class(db)
        result = collector.run()
        logger.info(f"{name} completed: {result}")
    except Exception as e:
        logger.error(f"{name} failed: {e}")
    finally:
        db.close()


# Run fetch every 2 minutes for all collectors independently
scheduler.add_job(
    lambda: run_collector(HindiNewsCollector, "Hindi News Collector"),
    "interval",
    minutes=2,
    id="fetch_hindi_news_job",
    replace_existing=True,
)
scheduler.add_job(
    lambda: run_collector(NationalNewsCollector, "National News Collector"),
    "interval",
    minutes=2,
    id="fetch_national_news_job",
    replace_existing=True,
)
scheduler.add_job(
    lambda: run_collector(StateNewsCollector, "State News Collector"),
    "interval",
    minutes=2,
    id="fetch_state_news_job",
    replace_existing=True,
)
scheduler.add_job(
    lambda: run_collector(DistrictNewsCollector, "District News Collector"),
    "interval",
    minutes=2,
    id="fetch_district_news_job",
    replace_existing=True,
)
scheduler.add_job(
    lambda: run_collector(GovernmentNewsCollector, "Government News Collector"),
    "interval",
    minutes=2,
    id="fetch_gov_news_job",
    replace_existing=True,
)
scheduler.add_job(
    lambda: run_collector(PoliceNewsCollector, "Police News Collector"),
    "interval",
    minutes=2,
    id="fetch_police_news_job",
    replace_existing=True,
)
scheduler.add_job(
    lambda: run_collector(PibNewsCollector, "PIB News Collector"),
    "interval",
    minutes=2,
    id="fetch_pib_news_job",
    replace_existing=True,
)
scheduler.add_job(
    lambda: run_collector(GenericRssCollector, "Generic RSS Collector"),
    "interval",
    minutes=2,
    id="fetch_generic_rss_job",
    replace_existing=True,
)
scheduler.add_job(
    lambda: run_collector(GoogleNewsCollector, "Google News Collector"),
    "interval",
    minutes=2,
    id="fetch_google_news_job",
    replace_existing=True,
)
