import asyncio
import logging
from sqlalchemy import select, func
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from logger_config import setup_logger
from db.models import init_db, AsyncSessionLocal, Project, MonitoredAccount, CapturedTweet
from scrapers.rootdata_scraper import RootDataScraper
from monitors.twitter_monitor import TwitterMonitor
from classifiers.content_classifier import ContentClassifier
from pushers.pusher_router import NotificationRouter

setup_logger()
logger = logging.getLogger("Main")


async def job_rootdata_daily():
    logger.info("触发定时任务: RootData 增量抓取...")
    scraper = RootDataScraper()
    await scraper.run_incremental_scrape()


async def job_twitter_polling():
    logger.info("触发定时任务: X (Twitter) 增量轮询...")
    monitor = TwitterMonitor()
    await monitor.init_client()

    raw_tweets = await monitor.poll_incremental_tweets()
    if not raw_tweets:
        return

    async with AsyncSessionLocal() as session:
        for tw_data in raw_tweets:
            analysis = await ContentClassifier.classify(tw_data["content"])
            if not analysis or analysis.get("importance", 0) < 2:
                continue

            stmt = select(MonitoredAccount).where(MonitoredAccount.twitter_handle == tw_data["twitter_handle"])
            m_res = await session.execute(stmt)
            monitored_acc = m_res.scalar_one_or_none()

            project = None
            if monitored_acc and monitored_acc.project_id:
                p_stmt = select(Project).where(Project.id == monitored_acc.project_id)
                p_res = await session.execute(p_stmt)
                project = p_res.scalar_one_or_none()

            tweet_obj = CapturedTweet(
                tweet_id=tw_data["tweet_id"],
                twitter_handle=tw_data["twitter_handle"],
                content=tw_data["content"],
                category=analysis["category"],
                importance=analysis["importance"],
                summary_cn=analysis["summary_cn"],
                tweet_created_at=tw_data["tweet_created_at"],
                pushed=False
            )
            session.add(tweet_obj)

            await NotificationRouter.push_all(tweet_obj, project)
            tweet_obj.pushed = True

        await session.commit()


async def main():
    await init_db()

    async with AsyncSessionLocal() as session:
        count_res = await session.execute(select(func.count(Project.id)))
        if count_res.scalar() == 0:
            logger.info("数据库为空，启动首次 RootData 全量抓取...")
            scraper = RootDataScraper()
            await scraper.run_full_scrape()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(job_rootdata_daily, 'cron', hour=3, minute=0)
    scheduler.add_job(job_twitter_polling, 'interval', minutes=settings.TWITTER_POLL_INTERVAL_MINUTES)

    scheduler.start()
    logger.info("=== AlphaScout 守护进程已成功启动 ===")

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())