import json
import logging
import httpx
from typing import Dict, Any
from config import settings
from db.models import Project

logger = logging.getLogger("PatternMatcher")

class AlphaPatternMatcher:
    # 顶级 Tier-1 机构白名单
    TIER1_VCS = {"paradigm", "a16z", "dragonfly", "polychain", "binance labs", "coinbase ventures", "sequoia", "multicoin"}

    @classmethod
    async def evaluate_project(cls, project: Project) -> Dict[str, Any]:
        """评估未发币项目，进行黄金特征匹配与软打分"""
        score = 50.0
        matched_traits = []

        # 1. 机构与融资额判定
        financing_str = (project.financing_amount or "").lower()
        for vc in cls.TIER1_VCS:
            if vc in financing_str:
                score += 12.0
                matched_traits.append(f"顶级 VC: {vc.capitalize()}")

        if any(amt in financing_str for amt in ["$10m", "$20m", "$50m", "$100m"]):
            score += 10.0
            matched_traits.append("大额融资 ($10M+)")

        # 2. LLM 软评估：反 PUA 与社区友好度
        if settings.DEEPSEEK_API_KEY:
            prompt = f"""
            你是 Web3 研报专家，请评估以下未发币项目的社区友好度与反 PUA 特性：
            项目名称: {project.name}
            融资背景: {project.financing_amount}
            官网: {project.website_url}

            评估要点：
            - 是否拒绝无限银河/Galxe刷分或每日打卡陷阱？
            - 是否有清晰透明的技术/测试网路线图？

            按 JSON 输出：
            {{
                "soft_score_delta": -15 到 +15 的整数,
                "non_pua_traits": ["标签1", "标签2"]
            }}
            """
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
                        llm_data = json.loads(resp.json()['choices'][0]['message']['content'])
                        score += llm_data.get("soft_score_delta", 0)
                        matched_traits.extend(llm_data.get("non_pua_traits", []))
            except Exception as e:
                logger.warning(f"LLM 评估项目失败 ({project.name}): {e}")

        final_score = max(0.0, min(100.0, score))
        is_priority = final_score >= 75.0

        return {
            "score": final_score,
            "is_priority": is_priority,
            "matched_traits": matched_traits
        }