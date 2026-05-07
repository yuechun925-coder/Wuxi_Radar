"""
contacts.py  —  联系人信息查询模块
策略：
  1. Google 搜索（用 requests 直接查，不依赖 google 包）
  2. 天眼查公开页面解析（无需 API）
  3. 企查查公开页面解析
"""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

def _headers(referer="https://www.google.com"):
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": referer,
    }

def _sleep():
    time.sleep(random.uniform(1.0, 2.5))


# ──────────────────────────────────────────────
# Google 搜索（直接请求，不用 google 包）
# ──────────────────────────────────────────────

def _google_search(query: str, num: int = 5) -> list[dict]:
    """
    通过 requests 直接请求 Google，解析搜索结果摘要。
    返回 [{"title": ..., "url": ..., "snippet": ...}]
    """
    results = []
    url = f"https://www.google.com/search?q={quote_plus(query)}&num={num}&hl=zh-CN"
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        if resp.status_code != 200:
            return _bing_search(query, num)
        soup = BeautifulSoup(resp.text, "html.parser")
        for g in soup.select("div.g, div[data-sokoban-container]")[:num]:
            a = g.select_one("a")
            title_tag = g.select_one("h3")
            snippet_tag = g.select_one(".VwiC3b, .s3v9rd, span.st")
            if not a or not title_tag:
                continue
            results.append({
                "title": title_tag.get_text(strip=True),
                "url": a.get("href", ""),
                "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
            })
    except Exception as e:
        print(f"    [Google] 搜索失败: {e}，尝试 Bing")
        return _bing_search(query, num)
    return results


def _bing_search(query: str, num: int = 5) -> list[dict]:
    """Google 失败时 fallback 到 Bing"""
    results = []
    url = f"https://www.bing.com/search?q={quote_plus(query)}&count={num}"
    try:
        resp = requests.get(url, headers=_headers("https://www.bing.com"), timeout=15)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        for li in soup.select("li.b_algo")[:num]:
            a = li.select_one("h2 a")
            snippet_tag = li.select_one("p")
            if not a:
                continue
            results.append({
                "title": a.get_text(strip=True),
                "url": a.get("href", ""),
                "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
            })
    except Exception as e:
        print(f"    [Bing] 搜索失败: {e}")
    return results


# ──────────────────────────────────────────────
# 天眼查公开页面解析（无需 API）
# ──────────────────────────────────────────────

def _tianyancha_search(company_name: str) -> dict:
    """搜索天眼查获取法定代表人等基本信息"""
    info = {}
    try:
        search_url = f"https://www.tianyancha.com/cloud-other-information/companyinfo/index.html#/search/{quote_plus(company_name)}"
        # 搜索页（天眼查对 bot 防护较强，先用 Google 搜索天眼查的结果）
        query = f'site:tianyancha.com "{company_name}"'
        results = _google_search(query, 3) or _bing_search(query, 3)
        for r in results:
            snippet = r.get("snippet", "")
            # 尝试从摘要中提取法定代表人
            rep_m = re.search(r"法定代表人[：:]\s*([\u4e00-\u9fa5]{2,6})", snippet)
            if rep_m:
                info["legal_representative"] = rep_m.group(1)
            phone_m = re.search(r"(\d{3,4}[-\s]?\d{7,8}|\+?86[-\s]?\d{11})", snippet)
            if phone_m:
                info["phone"] = phone_m.group(1)
            addr_m = re.search(r"([\u4e00-\u9fa5]{2,4}省[\u4e00-\u9fa5]{2,10}[市区县][\u4e00-\u9fa5\d\-号室楼]{4,30})", snippet)
            if addr_m:
                info["address"] = addr_m.group(1)
            if info:
                break
    except Exception as e:
        print(f"    [天眼查] 解析失败: {e}")
    return info


# ──────────────────────────────────────────────
# 创始人/CEO 联系方式搜索
# ──────────────────────────────────────────────

def _find_founder_contact(company_name: str) -> dict:
    """
    搜索创始人/CEO 邮箱、LinkedIn、微信公众号等。
    """
    info = {}
    queries = [
        f'"{company_name}" CEO OR 创始人 OR 董事长 邮箱 OR email',
        f'"{company_name}" 创始人 OR CEO LinkedIn',
        f'"{company_name}" 联系方式 OR investor relations',
    ]
    all_results = []
    for q in queries[:2]:  # 最多查 2 个 query 控制速度
        results = _google_search(q, 5)
        all_results.extend(results)
        _sleep()

    combined_text = " ".join(
        r.get("snippet", "") + " " + r.get("title", "") for r in all_results
    )

    # 邮箱
    email_m = re.search(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", combined_text
    )
    if email_m:
        email = email_m.group(0)
        # 过滤明显的无效邮箱
        if not any(bad in email for bad in ["example", "test@", "xxx@", "abc@"]):
            info["email"] = email

    # LinkedIn
    linkedin_results = [
        r for r in all_results if "linkedin.com" in r.get("url", "")
    ]
    if linkedin_results:
        info["linkedin"] = linkedin_results[0]["url"]

    # 姓名提取（从摘要中）
    name_patterns = [
        r"创始人\s*([\u4e00-\u9fa5]{2,4})",
        r"CEO\s*([\u4e00-\u9fa5]{2,4})",
        r"董事长\s*([\u4e00-\u9fa5]{2,4})",
        r"([\u4e00-\u9fa5]{2,4})\s*创始人",
        r"([\u4e00-\u9fa5]{2,4})\s*CEO",
    ]
    for pat in name_patterns:
        m = re.search(pat, combined_text)
        if m:
            candidate = m.group(1)
            if len(candidate) in [2, 3, 4]:
                info["founder_name"] = candidate
                break

    # 搜索结果摘要（供邮件展示）
    info["google_results"] = [
        {"title": r["title"], "url": r["url"], "snippet": r["snippet"][:100]}
        for r in all_results[:4]
        if r.get("title") and r.get("url")
    ]

    return info


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────

def get_company_contacts(company_name: str) -> dict:
    """
    综合查询公司联系人信息。
    返回字段：legal_representative, phone, email, address, founder_name, linkedin, google_results
    """
    contacts = {
        "legal_representative": "",
        "phone": "",
        "email": "",
        "address": "",
        "founder_name": "",
        "linkedin": "",
        "google_results": [],
    }

    print(f"    [联系人] 查询天眼查: {company_name}")
    tyc_info = _tianyancha_search(company_name)
    contacts.update({k: v for k, v in tyc_info.items() if v})
    _sleep()

    print(f"    [联系人] 搜索创始人信息: {company_name}")
    founder_info = _find_founder_contact(company_name)
    # 合并（不覆盖已有数据）
    for key, val in founder_info.items():
        if val and not contacts.get(key):
            contacts[key] = val

    return contacts


# ──────────────────────────────────────────────
# 中介推荐（FA / 投资顾问）
# ──────────────────────────────────────────────

KNOWN_FA_FIRMS = [
    {"name": "华兴资本", "focus": "生物医药、科技", "contact_hint": "hx.cn"},
    {"name": "中金公司 (CICC)", "focus": "全行业", "contact_hint": "cicc.com.cn"},
    {"name": "海通证券投行", "focus": "制造业、新能源", "contact_hint": "htsec.com"},
    {"name": "国联证券", "focus": "长三角企业", "contact_hint": "glsc.com.cn"},
    {"name": "浦银安盛", "focus": "医疗、科技", "contact_hint": ""},
    {"name": "方正证券投行", "focus": "半导体、新能源", "contact_hint": ""},
    {"name": "申万宏源", "focus": "精密制造", "contact_hint": ""},
    {"name": "Plum Ventures 梅花创投", "focus": "硬科技早期", "contact_hint": "plumventures.cn"},
    {"name": "青松基金", "focus": "新能源、工业科技", "contact_hint": ""},
    {"name": "联想创投", "focus": "半导体、制造", "contact_hint": "legendcapital.com.cn"},
]

def get_fa_recommendations() -> list:
    """
    返回与园区目标产业匹配的 FA 机构推荐列表，
    供"今日暂无目标企业"时在邮件中展示，
    引导对 FA 进行冷外联以间接获取企业资源。
    """
    return KNOWN_FA_FIRMS
