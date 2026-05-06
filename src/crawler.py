import requests
from bs4 import BeautifulSoup
import json

def crawl_36kr_funding():
    url = "https://36kr.com/information/funding"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Referer": "https://36kr.com/",
        "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"macOS\"",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
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
                                company_info = {}
                                if 'companyName' in item:
                                    company_info['company_name'] = item['companyName']
                                elif 'name' in item:
                                    company_info['company_name'] = item['name']
                                else:
                                    continue
                                
                                if 'round' in item:
                                    company_info['funding_round'] = item['round']
                                else:
                                    company_info['funding_round'] = ""
                                
                                if 'amount' in item:
                                    company_info['amount'] = item['amount']
                                else:
                                    company_info['amount'] = ""
                                
                                if 'industry' in item:
                                    company_info['industry'] = item['industry']
                                elif 'track' in item:
                                    company_info['industry'] = item['track']
                                else:
                                    company_info['industry'] = ""
                                
                                if 'publishTime' in item:
                                    company_info['funding_date'] = item['publishTime']
                                elif 'date' in item:
                                    company_info['funding_date'] = item['date']
                                else:
                                    company_info['funding_date'] = ""
                                
                                data_items.append(company_info)
                            break
                except (json.JSONDecodeError, ValueError):
                    continue
        
        if not data_items:
            articles = soup.find_all('article')
            for article in articles:
                company_info = {}
                title_tag = article.find('h3') or article.find('h2') or article.find('h1')
                if title_tag:
                    company_info['company_name'] = title_tag.get_text(strip=True)
                else:
                    continue
                
                meta_div = article.find('div', class_='m-article-info')
                if meta_div:
                    spans = meta_div.find_all('span')
                    for span in spans:
                        text = span.get_text(strip=True)
                        if '轮' in text or text in ['天使轮', 'Pre-A', 'A轮', 'A+轮', 'B轮', 'B+轮', 'C轮', 'D轮', 'E轮', 'F轮', 'IPO', '战略投资']:
                            company_info['funding_round'] = text
                        elif any(keyword in text for keyword in ['亿元', '万元', '美元', '万欧元']):
                            company_info['amount'] = text
                
                industry_tag = article.find('span', class_='category')
                if industry_tag:
                    company_info['industry'] = industry_tag.get_text(strip=True)
                
                date_tag = article.find('span', class_='time')
                if date_tag:
                    company_info['funding_date'] = date_tag.get_text(strip=True)
                
                company_info.setdefault('funding_round', "")
                company_info.setdefault('amount', "")
                company_info.setdefault('industry', "")
                company_info.setdefault('funding_date', "")
                
                data_items.append(company_info)
        
        if not data_items:
            cards = soup.find_all(class_='item-card')
            for card in cards:
                company_info = {}
                name_tag = card.find(class_='company-name') or card.find(class_='title')
                if name_tag:
                    company_info['company_name'] = name_tag.get_text(strip=True)
                else:
                    continue
                
                round_tag = card.find(class_='funding-round')
                if round_tag:
                    company_info['funding_round'] = round_tag.get_text(strip=True)
                
                amount_tag = card.find(class_='funding-amount')
                if amount_tag:
                    company_info['amount'] = amount_tag.get_text(strip=True)
                
                industry_tag = card.find(class_='industry')
                if industry_tag:
                    company_info['industry'] = industry_tag.get_text(strip=True)
                
                date_tag = card.find(class_='date')
                if date_tag:
                    company_info['funding_date'] = date_tag.get_text(strip=True)
                
                company_info.setdefault('funding_round', "")
                company_info.setdefault('amount', "")
                company_info.setdefault('industry', "")
                company_info.setdefault('funding_date', "")
                
                data_items.append(company_info)
        
        return data_items
    
    except Exception as e:
        print(f"爬取36氪数据失败: {e}")
        return []

if __name__ == "__main__":
    result = crawl_36kr_funding()
    print(f"获取到 {len(result)} 条融资信息")
    for item in result[:5]:
        print(item)