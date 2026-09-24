import httpx
import logging
from config import settings
from db.models import CapturedTweet, Project

logger = logging.getLogger("PusherRouter")

class NotificationRouter:
    @staticmethod
    async def push_all(tweet: CapturedTweet, project: Project = None):
        proj_name = project.name if project else "未知项目"
        raised = project.financing_amount if project else "未披露"
        priority_tag = "🔥 <b>[重点跟踪 Alpha]</b>\n" if project and project.is_priority else ""
        score_info = f"🎯 <b>Alpha 匹配度</b>: {project.alpha_score:.1f} 分\n" if project else ""

        # Telegram 卡片
        tg_text = (
            f"{priority_tag}"
            f"🚀 <b>Web3 Alpha 动态提醒</b>\n\n"
            f"📌 <b>项目</b>: {proj_name} (未发币)\n"
            f"{score_info}"
            f"💰 <b>融资</b>: {raised}\n"
            f"🏷️ <b>分类</b>: #{tweet.category} | <b>重要度</b>: {'⭐'*tweet.importance}\n"
            f"📝 <b>AI 摘要</b>: {tweet.summary_cn}\n\n"
            f"🔗 <b>推文原文</b>: https://x.com/{tweet.twitter_handle}/status/{tweet.tweet_id}"
        )
        await NotificationRouter._send_telegram(tg_text)

        # 飞书交互卡片
        feishu_card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"{'🔥 ' if project and project.is_priority else ''}[未发币] {proj_name} 最新动态"},
                    "template": "orange" if project and project.is_priority else "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": f"**融资**: {raised} | **Alpha 得分**: {project.alpha_score:.1f} 分\n**分类**: {tweet.category} (⭐{tweet.importance})"}
                    },
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": f"**AI 总结**: {tweet.summary_cn}"}
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "action",
                        "actions": [{
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "查看 X 原推文"},
                            "type": "primary",
                            "url": f"https://x.com/{tweet.twitter_handle}/status/{tweet.tweet_id}"
                        }]
                    }
                ]
            }
        }
        await NotificationRouter._send_feishu(feishu_card)

    @staticmethod
    async def _send_telegram(text: str):
        if not settings.TG_BOT_TOKEN or not settings.TG_CHAT_ID:
            return
        url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json={"chat_id": settings.TG_CHAT_ID, "text": text, "parse_mode": "HTML"})
            except Exception as e:
                logger.error(f"Telegram 推送失败: {e}")

    @staticmethod
    async def _send_feishu(card_payload: dict):
        if not settings.FEISHU_WEBHOOK_URL:
            return
        async with httpx.AsyncClient() as client:
            try:
                await client.post(settings.FEISHU_WEBHOOK_URL, json=card_payload)
            except Exception as e:
                logger.error(f"飞书推送失败: {e}")