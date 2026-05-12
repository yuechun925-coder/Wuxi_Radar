"""
crawler.py - 多数据源融资新闻爬虫
使用搜索引擎作为数据源
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
import random

def _headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

def _sleep():
    time.sleep(random.uniform(2, 4))

def search_bing(query, num=10):
    url = f"https://www.bing.com/search?q={requests.utils.quote(query)}&count={num}&setlang=zh-CN"
    try:
        resp = requests.get(url, headers=_headers(), timeout=30)
        if resp.status_code != 200:
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        
        for result in soup.find_all("div", class_="b_algo")[:num]:
            title_tag = result.find("h2")
            if not title_tag:
                continue
            
            title = title_tag.get_text(strip=True)
            link = result.find("a")["href"] if result.find("a") else ""
            
            company_name = ""
            if "获" in title or "完成" in title:
                parts = title.split("获") if "获" in title else title.split("完成")
                if len(parts) > 0:
                    company_name = parts[0].strip()
            
            if company_name and len(company_name) >= 2:
                results.append({
                    "company_name": company_name,
                    "title": title,
                    "url": link,
                    "funding_round": "",
                    "amount": "",
                    "industry": "",
                    "funding_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "Bing搜索"
                })
        
        return results
    except Exception as e:
        print(f"Bing搜索失败: {e}")
        return []

def search_baidu(query, num=10):
    url = f"https://www.baidu.com/s?wd={requests.utils.quote(query)}&pn=0&rn={num}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=30)
        if resp.status_code != 200:
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        
        for result in soup.find_all("div", class_="result")[:num]:
            h3_tag = result.find("h3")
            if not h3_tag:
                continue
            
            title = h3_tag.get_text(strip=True)
            link = h3_tag.find("a")["href"] if h3_tag.find("a") else ""
            
            company_name = ""
            if "获" in title or "完成" in title:
                parts = title.split("获") if "获" in title else title.split("完成")
                if len(parts) > 0:
                    company_name = parts[0].strip()
            
            if company_name and len(company_name) >= 2:
                results.append({
                    "company_name": company_name,
                    "title": title,
                    "url": link,
                    "funding_round": "",
                    "amount": "",
                    "industry": "",
                    "funding_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "百度搜索"
                })
        
        return results
    except Exception as e:
        print(f"百度搜索失败: {e}")
        return []

def get_sample_data():
    """返回示例数据（当搜索失败时使用）"""
    return [
        {"company_name": "智芯科技", "title": "智芯科技完成B轮融资，专注半导体芯片研发", "url": "https://example.com/zhixin", "funding_round": "B轮", "amount": "2亿元", "industry": "半导体", "funding_date": datetime.now().strftime("%Y-%m-%d"), "source": "示例数据"},
        {"company_name": "康瑞生物", "title": "康瑞生物获A轮融资，深耕生物医药领域", "url": "https://example.com/kangrui", "funding_round": "A轮", "amount": "1亿元", "industry": "生物医药", "funding_date": datetime.now().strftime("%Y-%m-%d"), "source": "示例数据"},
        {"company_name": "绿能科技", "title": "绿能科技完成C轮融资，布局新能源产业链", "url": "https://example.com/lvnen", "funding_round": "C轮", "amount": "5亿元", "industry": "新能源", "funding_date": datetime.now().strftime("%Y-%m-%d"), "source": "示例数据"},
        {"company_name": "精密制造集团", "title": "精密制造集团获战略投资，加码高端制造", "url": "https://example.com/jingmi", "funding_round": "战略投资", "amount": "3亿元", "industry": "精密制造", "funding_date": datetime.now().strftime("%Y-%m-%d"), "source": "示例数据"},
        {"company_name": "医疗创新科技", "title": "医疗创新科技完成B轮融资，聚焦医疗器械研发", "url": "https://example.com/yiliao", "funding_round": "B轮", "amount": "1.5亿元", "industry": "医疗技术", "funding_date": datetime.now().strftime("%Y-%m-%d"), "source": "示例数据"},
    ]

def crawl_all_sources():
    print("开始爬取融资数据...")
    
    all_results = []
    
    queries = [
        "融资 生物医药 2024",
        "融资 半导体 2024",
        "融资 新能源 2024",
        "融资 硬科技 2024",
        "融资 精密制造 2024",
    ]
    
    for query in queries:
        print(f"  搜索: {query}")
        results = search_bing(query, 10)
        all_results.extend(results)
        _sleep()
    
    seen = set()
    unique_results = []
    for r in all_results:
        key = r["company_name"] + r["title"]
        if key not in seen:
            seen.add(key)
            unique_results.append(r)
    
    if len(unique_results) == 0:
        print("  搜索结果为空，使用示例数据")
        unique_results = get_sample_data()
    
    print(f"共获取 {len(unique_results)} 条融资新闻（去重后）")
    return unique_results

if __name__ == "__main__":
    results = crawl_all_sources()
    for r in results[:10]:
        print(f"{r['company_name']} - {r['source']}")
