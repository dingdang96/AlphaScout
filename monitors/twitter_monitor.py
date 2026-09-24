import random
import asyncio
import logging
from typing import List, Dict, Any
from sqlalchemy import select, desc
from twikit import Client
from config import settings
from db.models import AsyncSessionLocal, MonitoredAccount, Project

logger = logging.getLogger("TwitterMonitor")

class TwitterMonitor:
    def __init__(self):
        self.client = Client('en-US')
        if settings.PROXY_URL:
            self.client.set_proxy(settings.PROXY_URL)

    async def init_client(self):
        if settings.TWITTER_AUTH_TOKEN:
            self.client.set_cookies({'auth_token': settings.TWITTER_AUTH_TOKEN})

    async def poll_incremental_tweets(self) -> List[Dict[str, Any]]:
        logger.info(">>> 开始轮询 [未发币] 账号增量推文 (重点项目优先)...")
        raw_captured = []

        async with AsyncSessionLocal() as session:
            # 按 priority 和 alpha_score 倒序排队
            stmt = (
                select(MonitoredAccount)
                .join(Project, MonitoredAccount.project_id == Project.id)
                .where(MonitoredAccount.is_active == True)
                .order_by(desc(Project.is_priority), desc(Project.alpha_score))
            )
            result = await session.execute(stmt)
            accounts: List[MonitoredAccount] = result.scalars().all()

            logger.info(f"队列就绪，待监控未发币账号数: {len(accounts)}")

            for acc in accounts:
                try:
                    user = await self.client.get_user_by_screen_name(acc.twitter_handle)
                    tweets = await user.get_tweets('Tweets', count=5)

                    new_max_id = acc.last_tweet_id

                    for tweet in tweets:
                        tweet_id = int(tweet.id)
                        if tweet_id > acc.last_tweet_id:
                            raw_captured.append({
                                "tweet_id": tweet_id,
                                "twitter_handle": acc.twitter_handle,
                                "content": tweet.text,
                                "tweet_created_at": tweet.created_at_datetime
                            })
                            if tweet_id > new_max_id:
                                new_max_id = tweet_id

                    acc.last_tweet_id = new_max_id
                    await session.commit()

                except Exception as e:
                    logger.warning(f"抓取账号 @{acc.twitter_handle} 失败: {e}")

                # 随机延迟防封锁
                delay = random.uniform(settings.TWITTER_DELAY_MIN, settings.TWITTER_DELAY_MAX)
                await asyncio.sleep(delay)

        return raw_captured