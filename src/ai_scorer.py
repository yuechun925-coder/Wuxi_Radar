"""
ai_scorer.py  —  DeepSeek AI 评分模块
评分维度：行业匹配 + 融资阶段 + 厂房需求真实性
"""

import os
import re
import json
import time
import requests

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 园区核心行业（完整列表，供 prompt 使用）
TARGET_INDUSTRIES = [
    "生物医药", "医疗技术", "医疗器械", "体外诊断", "CDMO", "CRO",
    "半导体", "芯片", "集成电路", "晶圆", "存储", "传感器",
    "新能源", "锂电池", "固态电池", "储能", "氢能", "光伏",
    "精密制造", "工业机器人", "工业自动化", "激光设备", "车规级",
    "健康消费", "大健康",
]

SYSTEM_PROMPT = """你是一位产业园区招商顾问，负责评估企业是否适合入驻无锡一个硬科技工业园区。
园区目标企业：生物医药、医疗技术、半导体/芯片、新能源、精密制造、工业机器人等硬科技制造型企业。
园区厂房面积1700-6500㎡，适合中小型硬科技企业设立生产/研发基地。

你必须返回且仅返回一个JSON对象，不含任何markdown标记或额外说明。
格式：{"score": 数字, "reason": "理由", "need_factory": 布尔值}"""

USER_PROMPT_TEMPLATE = """请评估以下企业是否适合入驻我们的硬科技工业园区：

公司名：{company_name}
行业：{industry}
融资轮次：{funding_round}
融资金额：{amount}

评分标准（满分10分）：
- 行业匹配（0-5分）：目标行业（生物医药/医疗技术/半导体/新能源/精密制造）得4-5分；相关制造业得2-3分；软件/互联网/消费等得0-1分
- 融资阶段（0-3分）：B轮及以上得3分；A轮/Pre-A得2分；天使/种子得1分；战略融资视规模得1-2分
- 厂房需求判断（0-2分）：有实际生产/制造需求得2分；纯研发得1分；纯软件得0分

need_factory：企业是否需要独立生产/研发厂房空间（非写字楼），true/false。

请返回JSON："""


def _extract_json(text: str) -> dict:
    """从 LLM 输出中安全提取 JSON，处理各种边缘情况"""
    # 去掉 markdown 代码块
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 找到最外层 {} 范围
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    # 用正则提取字段
    result = {}
    score_m = re.search(r'"score"\s*:\s*(\d+(?:\.\d+)?)', text)
    reason_m = re.search(r'"reason"\s*:\s*"([^"]+)"', text)
    factory_m = re.search(r'"need_factory"\s*:\s*(true|false)', text, re.IGNORECASE)
    if score_m:
        result["score"] = float(score_m.group(1))
    if reason_m:
        result["reason"] = reason_m.group(1)
    if factory_m:
        result["need_factory"] = factory_m.group(1).lower() == "true"
    return result


def _rule_based_score(company_name: str, industry: str, funding_round: str, amount: str) -> dict:
    """
    当 API 不可用时的规则兜底评分。
    保证系统在没有 API Key 时也能运行。
    """
    score = 0
    reasons = []
    need_factory = False

    # 行业匹配
    industry_keywords = {
        5: ["半导体", "芯片", "生物医药", "医疗器械", "医疗技术", "CDMO", "CRO", "IVD", "固态电池", "晶圆"],
        4: ["新能源", "精密制造", "工业机器人", "激光", "传感器", "车规", "健康消费", "大健康"],
        3: ["制造", "材料", "硬件", "工业", "自动化", "电子", "光电", "储能"],
        1: ["软件", "互联网", "电商", "直播", "游戏", "教育", "金融科技"],
    }
    combined = f"{industry} {company_name}"
    matched_score = 0
    for pts, kwds in sorted(industry_keywords.items(), reverse=True):
        if any(kw in combined for kw in kwds):
            matched_score = pts
            break
    score += matched_score
    if matched_score >= 4:
        need_factory = True
        reasons.append(f"行业高度匹配（{industry or '目标产业'}）")
    elif matched_score >= 3:
        need_factory = True
        reasons.append(f"行业较匹配（{industry or '制造业'}）")
    else:
        reasons.append(f"行业匹配度低（{industry or '未知'}）")

    # 融资阶段
    round_lower = funding_round.lower()
    if any(r in round_lower for r in ["c轮", "d轮", "e轮", "pre-ipo", "战略"]):
        score += 3
        reasons.append(f"融资阶段成熟（{funding_round}）")
    elif any(r in round_lower for r in ["b轮", "b+"]):
        score += 3
        reasons.append(f"融资阶段良好（{funding_round}）")
    elif any(r in round_lower for r in ["a轮", "a+", "pre-a"]):
        score += 2
        reasons.append(f"融资阶段较早（{funding_round}）")
    elif any(r in round_lower for r in ["天使", "种子"]):
        score += 1
        reasons.append(f"早期融资（{funding_round}）")

    # 融资金额
    if amount:
        amt_m = re.search(r"([\d.]+)\s*(亿|千万|百万|万)", amount)
        if amt_m:
            val = float(amt_m.group(1))
            unit = amt_m.group(2)
            val_wan = val * {"亿": 10000, "千万": 1000, "百万": 100, "万": 1}.get(unit, 1)
            if val_wan >= 10000:
                score += 2
                reasons.append(f"融资规模大（{amount}）")
            elif val_wan >= 3000:
                score += 2
                reasons.append(f"融资规模较大（{amount}）")
            else:
                score += 1
                reasons.append(f"有融资金额（{amount}）")

    return {
        "score": min(score, 10),
        "reason": "；".join(reasons),
        "need_factory": need_factory,
    }


def score_company(company_name: str, industry: str, funding_round: str, amount: str) -> dict:
    """
    主评分入口：优先调用 DeepSeek API，失败时退回规则评分。
    返回：{"score": int, "reason": str, "need_factory": bool}
    """
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    if not api_key or api_key.startswith("your-"):
        print("    [AI] 未配置 DEEPSEEK_API_KEY，使用规则评分")
        return _rule_based_score(company_name, industry, funding_round, amount)

    user_msg = USER_PROMPT_TEMPLATE.format(
        company_name=company_name,
        industry=industry or "未知",
        funding_round=funding_round or "未知",
        amount=amount or "未披露",
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.1,
        "max_tokens": 300,
        "response_format": {"type": "json_object"},  # 强制 JSON 输出
    }

    for attempt in range(3):
        try:
            resp = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            if resp.status_code == 200:
                raw = resp.json()["choices"][0]["message"]["content"]
                result = _extract_json(raw)
                if "score" in result:
                    result["score"] = int(float(result.get("score", 0)))
                    result.setdefault("reason", "")
                    result.setdefault("need_factory", result["score"] >= 5)
                    return result
            elif resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            else:
                print(f"    [AI] API 返回 {resp.status_code}，退回规则评分")
                break
        except Exception as e:
            print(f"    [AI] 调用失败（{e}），退回规则评分")
            break

    return _rule_based_score(company_name, industry, funding_round, amount)
