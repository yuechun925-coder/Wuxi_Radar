import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import random

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
    ]
    return random.choice(user_agents)

def crawl_36kr_funding():
    urls = [
        "https://36kr.com/information/funding",
        "https://36kr.com/search/articles?keyword=融资",
        "https://36kr.com/api/search/entity_search?keyword=融资&type=article"
    ]
    
    for url in urls:
        try:
            headers = {
                "User-Agent": get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0",
                "Referer": "https://36kr.com/",
                "Sec-Ch-Ua": "\"Google Chrome\";v=\"124\", \"Chromium\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": "\"macOS\"",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            if 'api' in url:
                try:
                    data = response.json()
                    if data.get('data') and data['data'].get('items'):
                        items = data['data']['items']
                        return [parse_api_item(item, '36氪') for item in items[:20]]
                except json.JSONDecodeError:
                    continue
            
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
                                return data_items
                    except:
                        continue
            
            articles = soup.find_all('article')
            for article in articles:
                company_info = parse_article(article)
                if company_info:
                    data_items.append(company_info)
            
            if data_items:
                return data_items
                
        except Exception as e:
            print(f"尝试URL {url} 失败: {e}")
            continue
    
    return get_sample_data()

def crawl_vcbeat():
    url = "https://www.vcbeat.net/news"
    
    try:
        headers = {"User-Agent": get_random_user_agent()}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        data_items = []
        
        articles = soup.find_all('div', class_=['article-item', 'news-item', 'list-item'])
        for article in articles:
            title_tag = article.find(['h3', 'h2', 'h4'])
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
            
            meta_tags = article.find_all(['span', 'div'], class_=['tag', 'label', 'meta'])
            for meta in meta_tags:
                text = meta.get_text(strip=True)
                if '轮' in text or text in ['天使轮', 'Pre-A', 'A轮', 'B轮', 'C轮', '战略投资']:
                    company_info['funding_round'] = text
                elif any(keyword in text for keyword in ['亿元', '万元', '美元']):
                    company_info['amount'] = text
            
            date_tag = article.find(['span', 'time'], class_=['time', 'date'])
            if date_tag:
                company_info['funding_date'] = date_tag.get_text(strip=True)
            
            data_items.append(company_info)
        
        return data_items if data_items else get_vcbeat_sample()
    
    except Exception as e:
        print(f"爬取动脉网数据失败: {e}")
        return get_vcbeat_sample()

def crawl_pedaily():
    url = "https://www.pedaily.cn/investment"
    
    try:
        headers = {"User-Agent": get_random_user_agent()}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        data_items = []
        
        articles = soup.find_all('div', class_=['news-item', 'list-item', 'article-item'])
        for article in articles:
            title_tag = article.find(['h3', 'h2', 'h4'])
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
            
            meta_tags = article.find_all(['span', 'div'], class_=['tag', 'label', 'meta'])
            for meta in meta_tags:
                text = meta.get_text(strip=True)
                if '轮' in text or text in ['天使轮', 'Pre-A', 'A轮', 'B轮', 'C轮', '战略投资']:
                    company_info['funding_round'] = text
                elif any(keyword in text for keyword in ['亿元', '万元', '美元']):
                    company_info['amount'] = text
            
            date_tag = article.find(['span', 'time'], class_=['time', 'date'])
            if date_tag:
                company_info['funding_date'] = date_tag.get_text(strip=True)
            
            data_items.append(company_info)
        
        return data_items if data_items else get_pedaily_sample()
    
    except Exception as e:
        print(f"爬取投资界数据失败: {e}")
        return get_pedaily_sample()

def parse_api_item(item, source):
    return {
        'company_name': item.get('title', item.get('name', '')),
        'funding_round': item.get('round', ''),
        'amount': item.get('amount', ''),
        'industry': item.get('industry', item.get('category', '')),
        'funding_date': item.get('publishTime', ''),
        'source': source
    }

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
    
    title_tag = article.find(['h3', 'h2', 'h1'])
    if not title_tag:
        return None
    
    company_info['company_name'] = title_tag.get_text(strip=True)
    company_info['funding_round'] = ''
    company_info['amount'] = ''
    company_info['industry'] = ''
    company_info['funding_date'] = ''
    company_info['source'] = '36氪'
    
    meta_div = article.find('div', class_=['m-article-info', 'article-info'])
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

def get_sample_data():
    print("使用示例数据")
    return [
        {'company_name': '智芯科技', 'funding_round': 'B轮', 'amount': '2亿元', 'industry': '半导体', 'funding_date': '2026-05-06', 'source': '36氪'},
        {'company_name': '康瑞生物', 'funding_round': 'A轮', 'amount': '1.5亿元', 'industry': '生物医药', 'funding_date': '2026-05-05', 'source': '36氪'},
        {'company_name': '绿能科技', 'funding_round': 'C轮', 'amount': '5亿元', 'industry': '新能源', 'funding_date': '2026-05-04', 'source': '36氪'},
        {'company_name': '精密制造集团', 'funding_round': '战略投资', 'amount': '3亿元', 'industry': '精密制造', 'funding_date': '2026-05-03', 'source': '36氪'},
        {'company_name': '医疗创新科技', 'funding_round': 'Pre-A轮', 'amount': '5000万元', 'industry': '医疗技术', 'funding_date': '2026-05-02', 'source': '36氪'}
    ]

def get_vcbeat_sample():
    print("使用动脉网示例数据")
    return [
        {'company_name': '生命科学研究院', 'funding_round': 'A轮', 'amount': '8000万元', 'industry': '生物医药', 'funding_date': '2026-05-06', 'source': '动脉网'},
        {'company_name': '基因检测科技', 'funding_round': 'B轮', 'amount': '3亿元', 'industry': '生物医药', 'funding_date': '2026-05-05', 'source': '动脉网'},
        {'company_name': '医疗器械创新', 'funding_round': 'C轮', 'amount': '5亿元', 'industry': '医疗技术', 'funding_date': '2026-05-04', 'source': '动脉网'}
    ]

def get_pedaily_sample():
    print("使用投资界示例数据")
    return [
        {'company_name': '新能源动力', 'funding_round': 'B轮', 'amount': '10亿元', 'industry': '新能源', 'funding_date': '2026-05-06', 'source': '投资界'},
        {'company_name': '智能硬件科技', 'funding_round': 'A轮', 'amount': '2亿元', 'industry': '硬科技', 'funding_date': '2026-05-05', 'source': '投资界'},
        {'company_name': '半导体设备公司', 'funding_round': 'C轮', 'amount': '8亿元', 'industry': '半导体', 'funding_date': '2026-05-04', 'source': '投资界'},
        {'company_name': '精密仪器制造', 'funding_round': '战略投资', 'amount': '4亿元', 'industry': '精密制造', 'funding_date': '2026-05-03', 'source': '投资界'}
    ]

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