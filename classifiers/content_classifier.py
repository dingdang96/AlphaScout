import re
import json
import httpx
from typing import Dict, Any, Optional
from config import settings

class ContentClassifier:
    KEYWORDS_REGEX = re.compile(
        r'(airdrop|testnet|mainnet|quest|galxe|zealy|task|mint|incentivized|snapshot|reward|roadmap|phase)',
        re.IGNORECASE
    )

    @classmethod
    async def classify(cls, text: str) -> Optional[Dict[str, Any]]:
        # 1. 正则快速初筛
        if not cls.KEYWORDS_REGEX.search(text):
            return None

        # 2. LLM 智能分类与总结
        prompt = f"""
        请分析以下 Web3 项目推文：
        推文内容: "{text}"

        按 JSON 输出：
        {{
            "category": "AIRDROP | QUEST | ROADMAP | ANNOUNCEMENT | GENERAL",
            "importance": 1到5的整数,
            "summary_cn": "用一句精炼中文概括重点"
        }}
        """

        if settings.DEEPSEEK_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{settings.DEEPSEEK_API_BASE}/chat/completions",
                        headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
                        json={
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": prompt}],
                            "response_format": {"type": "json_object"}
                        }
                    )
                    if resp.status_code == 200:
                        return json.loads(resp.json()['choices'][0]['message']['content'])
            except Exception:
                pass

        return {
            "category": "GENERAL",
            "importance": 3,
            "summary_cn": "包含任务/空投关键字，请核对原文"
        }