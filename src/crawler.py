"""
crawler.py  —  多源融资数据采集
来源优先级:
  1. 36氪内部 JSON API（无需 JS 渲染）
  2. 投资界 (pedaily.cn) RSS
  3. 创业邦融资快讯
"""

import re
import time
import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ──────────────────────────────────────────────
# 通用 headers（模拟真实浏览器）
# ──────────────────────────────────────────────
HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://36kr.com/",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://36kr.com/information/funding",
    },
]

def _headers():
    return random.choice(HEADERS_POOL)

def _sleep():
    time.sleep(random.uniform(1.5, 3.0))


# ──────────────────────────────────────────────
# 来源 1：36氪 — 内部 JSON API
# ──────────────────────────────────────────────
def crawl_36kr() -> list:
    """
    调用 36氪内部 newsflash/feed API，返回结构化融资数据。
    该接口返回 SSR JSON，无需 JS 渲染。
    """
    results = []
    urls = [
        "https://36kr.com/api/newsflash/home?per_page=30",
        "https://36kr.com/api/newsflash/home?per_page=30&page=2",
    ]
    keywords = ["融资", "完成", "亿元", "万元", "轮", "投资"]

    for url in urls:
        try:
            resp = requests.get(url, headers=_headers(), timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            items = (
                data.get("data", {}).get("items", [])
                or data.get("items", [])
                or data.get("data", [])
            )
            for item in items:
                title = item.get("title", "") or item.get("itemTitle", "")
                if not any(kw in title for kw in keywords):
                    continue
                content = item.get("description", "") or title
                parsed = _parse_funding_text(title + " " + content)
                if parsed:
                    parsed["source"] = "36氪"
                    parsed["title"] = title
                    results.append(parsed)
            _sleep()
        except Exception as e:
            print(f"[36kr API] 失败: {e}")
            continue

    # 如果 API 失效，fallback 到 RSS
    if not results:
        results = _crawl_36kr_rss()

    return results


def _crawl_36kr_rss() -> list:
    """36氪 RSS fallback"""
    results = []
    try:
        resp = requests.get(
            "https://36kr.com/feed",
            headers=_headers(),
            timeout=15
        )
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "xml")
        for item in soup.find_all("item")[:40]:
            title = item.find("title")
            title = title.text.strip() if title else ""
            description = item.find("description")
            desc = description.text.strip() if description else ""
            if not any(kw in title for kw in ["融资", "亿元", "万元", "轮次", "完成"]):
                continue
            parsed = _parse_funding_text(title + " " + desc)
            if parsed:
                parsed["source"] = "36氪RSS"
                parsed["title"] = title
                results.append(parsed)
    except Exception as e:
        print(f"[36kr RSS] 失败: {e}")
    return results


# ──────────────────────────────────────────────
# 来源 2：投资界 (pedaily.cn)
# ──────────────────────────────────────────────
def crawl_pedaily() -> list:
    """
    投资界融资快讯列表页，纯 HTML，requests 可直接抓取。
    """
    results = []
    urls = [
        "https://www.pedaily.cn/news/list?JiLu=1&Type=3",
        "https://www.pedaily.cn/news/",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=_headers(), timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            # 文章列表
            articles = soup.select("li.news-item, div.news-list li, .list-box li")
            if not articles:
                articles = soup.select("a[href*='/news/']")
            for art in articles[:40]:
                title_tag = art.select_one("a, h3, .title")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                if not any(kw in title for kw in ["融资", "亿元", "万元", "完成", "轮"]):
                    continue
                parsed = _parse_funding_text(title)
                if parsed:
                    parsed["source"] = "投资界"
                    parsed["title"] = title
                    results.append(parsed)
            if results:
                break
            _sleep()
        except Exception as e:
            print(f"[投资界] 失败: {e}")
            continue
    return results


# ──────────────────────────────────────────────
# 来源 3：创业邦融资快讯
# ──────────────────────────────────────────────
def crawl_cyzone() -> list:
    """创业邦融资新闻"""
    results = []
    try:
        resp = requests.get(
            "https://www.cyzone.cn/event/",
            headers=_headers(),
            timeout=15
        )
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select(".event-list li, .news-list li, article")[:40]:
            text = item.get_text(separator=" ", strip=True)
            if not any(kw in text for kw in ["融资", "亿元", "万元", "轮", "完成"]):
                continue
            parsed = _parse_funding_text(text[:200])
            if parsed:
                parsed["source"] = "创业邦"
                parsed["title"] = text[:60]
                results.append(parsed)
    except Exception as e:
        print(f"[创业邦] 失败: {e}")
    return results


# ──────────────────────────────────────────────
# 来源 4：IT桔子公开融资列表
# ──────────────────────────────────────────────
def crawl_itjuzi() -> list:
    """IT桔子融资事件列表（公开部分）"""
    results = []
    try:
        headers = _headers().copy()
        headers["Referer"] = "https://www.itjuzi.com/"
        resp = requests.get(
            "https://www.itjuzi.com/investevent",
            headers=headers,
            timeout=15
        )
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.select("tr, .event-row, .invest-item")[:40]:
            text = row.get_text(separator=" ", strip=True)
            if len(text) < 10:
                continue
            parsed = _parse_funding_text(text[:300])
            if parsed:
                parsed["source"] = "IT桔子"
                parsed["title"] = text[:60]
                results.append(parsed)
    except Exception as e:
        print(f"[IT桔子] 失败: {e}")
    return results


# ──────────────────────────────────────────────
# 文本解析：从标题/摘要提取结构化字段
# ──────────────────────────────────────────────

# 融资轮次关键词（顺序很重要，长的放前面）
ROUND_PATTERNS = [
    r"Pre-?IPO", r"战略融资", r"战略投资", r"股权融资",
    r"天使\+轮", r"Pre-?[A-Z](?:\+)?轮?",
    r"[A-Z]\+?轮", r"[A-Z][1-9]轮",
    r"天使轮", r"种子轮", r"新三板",
    r"上市", r"IPO",
]

# 行业关键词 → 标准化行业名
INDUSTRY_MAP = {
    "半导体": "半导体", "芯片": "半导体", "集成电路": "半导体", "EDA": "半导体",
    "晶圆": "半导体", "存储": "半导体", "光刻": "半导体", "功率器件": "半导体",
    "生物医药": "生物医药", "制药": "生物医药", "新药": "生物医药", "基因": "生物医药",
    "抗体": "生物医药", "疫苗": "生物医药", "CDMO": "生物医药", "CRO": "生物医药",
    "医疗器械": "医疗技术", "医疗技术": "医疗技术", "IVD": "医疗技术",
    "手术机器人": "医疗技术", "影像": "医疗技术", "诊断": "医疗技术",
    "新能源": "新能源", "锂电": "新能源", "固态电池": "新能源", "氢能": "新能源",
    "储能": "新能源", "光伏": "新能源", "充电": "新能源",
    "精密制造": "精密制造", "机器人": "精密制造", "工业自动化": "精密制造",
    "数控": "精密制造", "激光": "精密制造", "传感器": "精密制造",
    "车规": "精密制造", "汽车零部件": "精密制造",
    "健康消费": "健康消费", "医美": "健康消费", "大健康": "健康消费",
}

def _parse_funding_text(text: str) -> dict | None:
    """
    从一段文本中提取：公司名、融资轮次、融资金额、行业、日期。
    返回 None 表示无法提取有效信息。
    """
    if not text:
        return None

    # 1. 融资金额
    amount = ""
    amt_match = re.search(r"([\d.]+\s*(?:亿|千万|百万|万)\s*(?:元|美元|美金|RMB|USD)?)", text)
    if amt_match:
        amount = amt_match.group(1).strip()

    # 2. 融资轮次
    funding_round = ""
    for pattern in ROUND_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            funding_round = m.group(0)
            break

    # 3. 行业（多关键词匹配，取第一个命中）
    industry = ""
    for kw, std in INDUSTRY_MAP.items():
        if kw in text:
            industry = std
            break

    # 4. 公司名（简单启发式：「XX公司」「XX科技」「XX生物」等）
    company_name = ""
    company_patterns = [
        r"([\u4e00-\u9fa5a-zA-Z0-9]{2,12}(?:科技|生物|医疗|制造|能源|芯片|半导体|医药|机器人|智能|材料|电子|信息|数字|健康|创新|医学|工业|新材料|装备|系统|软件|网络|云|传感|光电|动力|集团)(?:有限公司|股份有限公司|公司)?)",
        r"完成.*?融资的([\u4e00-\u9fa5a-zA-Z0-9]{2,15})",
        r"([\u4e00-\u9fa5a-zA-Z0-9]{2,15})(?:完成|获得|宣布).*?融资",
        r"([\u4e00-\u9fa5a-zA-Z0-9]{2,15})(?:获|完成)",
    ]
    for pat in company_patterns:
        m = re.search(pat, text)
        if m:
            candidate = m.group(1).strip()
            # 过滤掉明显的非公司名
            if len(candidate) >= 3 and not any(
                bad in candidate for bad in ["今日", "最新", "重磅", "独家", "紧急"]
            ):
                company_name = candidate
                break

    # 5. 日期（优先文本中的，否则用今天）
    funding_date = datetime.now().strftime("%Y-%m-%d")
    date_m = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})", text)
    if date_m:
        raw = date_m.group(1).replace("年", "-").replace("月", "-").replace("/", "-")
        try:
            funding_date = datetime.strptime(raw, "%Y-%m-%d").strftime("%Y-%m-%d")
        except:
            pass

    # 至少要有公司名才返回
    if not company_name:
        return None

    return {
        "company_name": company_name,
        "industry": industry,
        "funding_round": funding_round,
        "amount": amount,
        "funding_date": funding_date,
    }


# ──────────────────────────────────────────────
# 主入口：聚合所有来源 + 去重
# ──────────────────────────────────────────────
def crawl_all_sources() -> list:
    all_data = []

    print("  [爬虫] 抓取 36氪...")
    kr_data = crawl_36kr()
    print(f"    → 获取 {len(kr_data)} 条")
    all_data.extend(kr_data)
    _sleep()

    print("  [爬虫] 抓取 投资界...")
    pd_data = crawl_pedaily()
    print(f"    → 获取 {len(pd_data)} 条")
    all_data.extend(pd_data)
    _sleep()

    print("  [爬虫] 抓取 创业邦...")
    cy_data = crawl_cyzone()
    print(f"    → 获取 {len(cy_data)} 条")
    all_data.extend(cy_data)
    _sleep()

    print("  [爬虫] 抓取 IT桔子...")
    ij_data = crawl_itjuzi()
    print(f"    → 获取 {len(ij_data)} 条")
    all_data.extend(ij_data)

    # 按公司名去重（保留最早出现的）
    seen = set()
    deduped = []
    for item in all_data:
        key = item.get("company_name", "").strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)

    print(f"  [爬虫] 合计去重后: {len(deduped)} 条")
    return deduped
