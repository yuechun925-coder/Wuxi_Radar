import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta

def crawl_36kr_funding():
    url = "https://36kr.com/information/funding"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Referer": "https://36kr.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        data_items = []
        
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'window.initialState' in script.string:
                try:
                    start = script.string.find('window.initialState = ') + len('window.initialState = ')
                    end = script.string.find(';', start)
                    json_str = script.string[start:end]
                    json_data = json.loads(json_str)
                    
                    if 'information' in json_data and 'funding' in json_data['information']:
                        funding_data = json_data['information']['funding']
                        if 'items' in funding_data:
                            items = funding_data['items']
                            for item in items:
                                company_info = parse_funding_item(item)
                                if company_info:
                                    data_items.append(company_info)
                            break
                except (json.JSONDecodeError, ValueError):
                    continue
        
        if not data_items:
            articles = soup.find_all('article')
            for article in articles:
                company_info = parse_article(article)
                if company_info:
                    data_items.append(company_info)
        
        return data_items
    
    except Exception as e:
        print(f"爬取36氪数据失败: {e}")
        return []

def crawl_vcbeat():
    url = "https://www.vcbeat.net/news"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        data_items = []
        
        articles = soup.find_all('div', class_='article-item')
        for article in articles:
            title_tag = article.find('h3') or article.find('h2')
            if not title_tag:
                continue
            
            company_info = {
                'company_name': title_tag.get_text(strip=True),
                'funding_round': '',
                'amount': '',
                'industry': '生物医药',
                'funding_date': '',
                'source': '动脉网'
            }
            
            meta_tags = article.find_all('span', class_='tag')
            for meta in meta_tags:
                text = meta.get_text(strip=True)
                if '轮' in text or text in ['天使轮', 'Pre-A', 'A轮', 'B轮', 'C轮', '战略投资']:
                    company_info['funding_round'] = text
                elif any(keyword in text for keyword in ['亿元', '万元', '美元']):
                    company_info['amount'] = text
            
            date_tag = article.find('span', class_='time')
            if date_tag:
                company_info['funding_date'] = date_tag.get_text(strip=True)
            
            data_items.append(company_info)
        
        return data_items
    
    except Exception as e:
        print(f"爬取动脉网数据失败: {e}")
        return []

def crawl_pedaily():
    url = "https://www.pedaily.cn/investment"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        data_items = []
        
        articles = soup.find_all('div', class_='news-item')
        for article in articles:
            title_tag = article.find('h3') or article.find('h2')
            if not title_tag:
                continue
            
            company_info = {
                'company_name': title_tag.get_text(strip=True),
                'funding_round': '',
                'amount': '',
                'industry': '硬科技',
                'funding_date': '',
                'source': '投资界'
            }
            
            meta_tags = article.find_all('span')
            for meta in meta_tags:
                text = meta.get_text(strip=True)
                if '轮' in text or text in ['天使轮', 'Pre-A', 'A轮', 'B轮', 'C轮', '战略投资']:
                    company_info['funding_round'] = text
                elif any(keyword in text for keyword in ['亿元', '万元', '美元']):
                    company_info['amount'] = text
            
            date_tag = article.find('span', class_='date')
            if date_tag:
                company_info['funding_date'] = date_tag.get_text(strip=True)
            
            data_items.append(company_info)
        
        return data_items
    
    except Exception as e:
        print(f"爬取投资界数据失败: {e}")
        return []

def parse_funding_item(item):
    company_info = {}
    
    if 'companyName' in item:
        company_info['company_name'] = item['companyName']
    elif 'name' in item:
        company_info['company_name'] = item['name']
    else:
        return None
    
    company_info['funding_round'] = item.get('round', '')
    company_info['amount'] = item.get('amount', '')
    company_info['industry'] = item.get('industry', item.get('track', ''))
    company_info['funding_date'] = item.get('publishTime', item.get('date', ''))
    company_info['source'] = '36氪'
    
    return company_info

def parse_article(article):
    company_info = {}
    
    title_tag = article.find('h3') or article.find('h2') or article.find('h1')
    if not title_tag:
        return None
    
    company_info['company_name'] = title_tag.get_text(strip=True)
    company_info['funding_round'] = ''
    company_info['amount'] = ''
    company_info['industry'] = ''
    company_info['funding_date'] = ''
    company_info['source'] = '36氪'
    
    meta_div = article.find('div', class_='m-article-info')
    if meta_div:
        spans = meta_div.find_all('span')
        for span in spans:
            text = span.get_text(strip=True)
            if '轮' in text or text in ['天使轮', 'Pre-A', 'A轮', 'B轮', 'C轮', '战略投资']:
                company_info['funding_round'] = text
            elif any(keyword in text for keyword in ['亿元', '万元', '美元']):
                company_info['amount'] = text
    
    industry_tag = article.find('span', class_='category')
    if industry_tag:
        company_info['industry'] = industry_tag.get_text(strip=True)
    
    date_tag = article.find('span', class_='time')
    if date_tag:
        company_info['funding_date'] = date_tag.get_text(strip=True)
    
    return company_info

def crawl_all_sources():
    all_data = []
    
    print("开始爬取36氪...")
    kr_data = crawl_36kr_funding()
    all_data.extend(kr_data)
    print(f"36氪获取 {len(kr_data)} 条数据")
    
    print("开始爬取动脉网...")
    vcbeat_data = crawl_vcbeat()
    all_data.extend(vcbeat_data)
    print(f"动脉网获取 {len(vcbeat_data)} 条数据")
    
    print("开始爬取投资界...")
    pedaily_data = crawl_pedaily()
    all_data.extend(pedaily_data)
    print(f"投资界获取 {len(pedaily_data)} 条数据")
    
    print(f"总计获取 {len(all_data)} 条融资信息")
    return all_data

if __name__ == "__main__":
    result = crawl_all_sources()
    for item in result[:5]:
        print(item)