"""
contacts.py  —  联系人信息查询模块
"""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

def _headers(referer="https://www.google.com"):
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": referer,
    }

def _sleep():
    time.sleep(random.uniform(1.0, 2.5))

def _google_search(query: str, num: int = 5) -> list:
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
    except:
        return _bing_search(query, num)
    return results

def _bing_search(query: str, num: int = 5) -> list:
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
    except:
        pass
    return results

def _tianyancha_search(company_name: str) -> dict:
    info = {}
    try:
        query = f'site:tianyancha.com "{company_name}"'
        results = _google_search(query, 3) or _bing_search(query, 3)
        for r in results:
            url = r.get("url", "")
            snippet = r.get("snippet", "")
            if "tianyancha.com" in url:
                info["tianyancha_url"] = url
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
    except:
        pass
    return info

def _find_founder_contact(company_name: str) -> dict:
    info = {}
    queries = [
        f'"{company_name}" CEO OR 创始人 OR 董事长 邮箱 OR email',
        f'"{company_name}" 创始人 OR CEO LinkedIn',
        f'"{company_name}" 官网 OR official website',
    ]
    all_results = []
    for q in queries[:3]:
        results = _google_search(q, 5)
        all_results.extend(results)
        _sleep()

    combined_text = " ".join(r.get("snippet", "") + " " + r.get("title", "") for r in all_results)

    email_m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", combined_text)
    if email_m:
        email = email_m.group(0)
        if not any(bad in email for bad in ["example", "test@", "xxx@", "abc@"]):
            info["email"] = email

    linkedin_results = [r for r in all_results if "linkedin.com" in r.get("url", "")]
    if linkedin_results:
        info["linkedin"] = linkedin_results[0]["url"]

    website_results = [
        r for r in all_results 
        if "www." in r.get("url", "") and not any(domain in r["url"] for domain in ["tianyancha", "qcc", "baidu", "google", "bing", "zhihu", "weibo"])
    ]
    if website_results:
        info["website"] = website_results[0]["url"]

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

    info["google_results"] = [
        {"title": r["title"], "url": r["url"], "snippet": r["snippet"][:100]}
        for r in all_results[:4]
        if r.get("title") and r.get("url")
    ]

    return info

def get_company_contacts(company_name: str) -> dict:
    contacts = {
        "legal_representative": "",
        "phone": "",
        "email": "",
        "address": "",
        "founder_name": "",
        "linkedin": "",
        "website": "",
        "tianyancha_url": "",
        "google_results": [],
    }

    tyc_info = _tianyancha_search(company_name)
    contacts.update({k: v for k, v in tyc_info.items() if v})
    _sleep()

    founder_info = _find_founder_contact(company_name)
    for key, val in founder_info.items():
        if val and not contacts.get(key):
            contacts[key] = val

    return contacts

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
    return KNOWN_FA_FIRMS