import os
import requests
from googlesearch import search

TIANYANCHA_MCP_URL = "https://mcp.tianyancha.com/v1"
TIANYANCHA_AUTH_TOKEN = "eea76d7b-4e2f-4254-a9ef-6fd48cef3794"

def get_tianyancha_info(company_name):
    url = f"{TIANYANCHA_MCP_URL}/search"
    
    headers = {
        "Authorization": TIANYANCHA_AUTH_TOKEN,
        "Content-Type": "application/json"
    }
    
    params = {
        "keyword": company_name
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 200 and data.get("data"):
            company_data = data["data"][0]
            return {
                "legal_representative": company_data.get("legalPersonName", ""),
                "phone": company_data.get("phone", ""),
                "email": company_data.get("email", ""),
                "address": company_data.get("regAddress", "")
            }
        else:
            return {"legal_representative": "", "phone": "", "email": "", "address": ""}
    
    except Exception as e:
        print(f"调用天眼查MCP失败: {e}")
        return {"legal_representative": "", "phone": "", "email": "", "address": ""}

def google_search_contacts(company_name):
    query = f"{company_name} CEO OR 创始人 邮箱 OR 微信 OR LinkedIn"
    
    try:
        results = []
        for result in search(query, num_results=5, timeout=10):
            results.append(result)
        
        return results[:5]
    
    except Exception as e:
        print(f"Google搜索失败: {e}")
        return []

def get_company_contacts(company_name):
    tianyancha_info = get_tianyancha_info(company_name)
    google_results = google_search_contacts(company_name)
    
    return {
        "legal_representative": tianyancha_info["legal_representative"],
        "phone": tianyancha_info["phone"],
        "email": tianyancha_info["email"],
        "address": tianyancha_info["address"],
        "google_results": google_results
    }

if __name__ == "__main__":
    result = get_company_contacts("示例公司")
    print(result)