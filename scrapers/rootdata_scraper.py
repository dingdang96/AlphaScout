import logging
import asyncio
from typing import List, Dict, Any, Optional
from DrissionPage import ChromiumPage, ChromiumOptions
from sqlalchemy import select
from db.models import AsyncSessionLocal, Project, MonitoredAccount
from analytics.pattern_matcher import AlphaPatternMatcher

logger = logging.getLogger("RootDataScraper")


def safe_get_text(element, selector: str, timeout: float = 1.0) -> str:
    """安全提取 DOM 节点文本，防护空指针异常"""
    try:
        ele = element.ele(selector, timeout=timeout)
        return ele.text.strip() if ele and ele.text else ""
    except Exception:
        return ""


class RootDataScraper:
    def __init__(self):
        co = ChromiumOptions()
        co.headless()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        self.page_options = co

    def _parse_project_card(self, element) -> Optional[Dict[str, Any]]:
        try:
            name = safe_get_text(element, '.project-name')
            if not name:
                return None

            financing = safe_get_text(element, '.financing-amount') or "未披露"

            links = element.eles('a')
            twitter_handle, website_url, discord_url = None, None, None
            for link in links:
                href = link.attr('href') or ''
                if 'x.com/' in href or 'twitter.com/' in href:
                    twitter_handle = href.split('/')[-1].replace('@', '').strip().split('?')[0]
                elif 'discord.gg' in href or 'discord.com' in href:
                    discord_url = href
                elif href.startswith('http') and 'rootdata.com' not in href:
                    website_url = href

            token_text = safe_get_text(element, '.token-status-tag')
            has_token = any(kw in token_text for kw in ["Issued", "已发币", "Active"])

            return {
                "rootdata_id": f"rd_{name.lower().replace(' ', '_')}",
                "name": name,
                "financing_amount": financing,
                "website_url": website_url,
                "twitter_handle": twitter_handle,
                "discord_url": discord_url,
                "has_token": has_token
            }
        except Exception as e:
            logger.error(f"解析项目 DOM 元素失败: {e}")
            return None

    async def run_incremental_scrape(self):
        logger.info(">>> 开始 RootData 增量更新抓取...")
        page = ChromiumPage(self.page_options)
        try:
            page.get("https://www.rootdata.com/Fundraising")
            await asyncio.sleep(5)

            items = page.eles('.project-item')
            parsed_data = [self._parse_project_card(item) for item in items]
            valid_data = [d for d in parsed_data if d]

            await self._save_or_update_projects(valid_data)
        finally:
            page.quit()
        logger.info("<<< RootData 增量更新抓取完成！")

    async def run_full_scrape(self):
        logger.info(">>> 开始首次 RootData 全量抓取...")
        page = ChromiumPage(self.page_options)
        try:
            page.get("https://www.rootdata.com/Projects")
            await asyncio.sleep(5)

            page_num = 1
            while True:
                logger.info(f"正在抓取 RootData 第 {page_num} 页...")
                items = page.eles('.project-item')
                if not items:
                    break

                page_data = [self._parse_project_card(item) for item in items]
                valid_data = [d for d in page_data if d]

                await self._save_or_update_projects(valid_data)

                next_btn = page.ele('.btn-next', timeout=2)
                if next_btn and not next_btn.attr('disabled'):
                    next_btn.click()
                    await asyncio.sleep(3)
                    page_num += 1
                else:
                    break
        finally:
            page.quit()

    async def _save_or_update_projects(self, projects_data: List[Dict[str, Any]]):
        async with AsyncSessionLocal() as session:
            for p in projects_data:
                stmt = select(Project).where(Project.rootdata_id == p['rootdata_id'])
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()

                if not existing:
                    new_proj = Project(**p)

                    if not new_proj.has_token:
                        eval_res = await AlphaPatternMatcher.evaluate_project(new_proj)
                        new_proj.alpha_score = eval_res['score']
                        new_proj.is_priority = eval_res['is_priority']
                        new_proj.matched_traits = eval_res['matched_traits']

                    session.add(new_proj)
                    await session.flush()

                    if p['twitter_handle']:
                        monitored = MonitoredAccount(
                            twitter_handle=p['twitter_handle'].lower(),
                            project_id=new_proj.id,
                            source_type="ROOTDATA",
                            is_active=not p['has_token']
                        )
                        session.add(monitored)
                else:
                    existing.financing_amount = p['financing_amount']
                    existing.has_token = p['has_token']

                    stmt_m = select(MonitoredAccount).where(MonitoredAccount.project_id == existing.id)
                    m_res = await session.execute(stmt_m)
                    monitored = m_res.scalar_one_or_none()
                    if monitored:
                        monitored.is_active = not p['has_token']

            await session.commit()