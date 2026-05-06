import os
import sys
from dotenv import load_dotenv
from src.crawler import crawl_36kr_funding
from src.ai_scorer import score_company
from src.contacts import get_company_contacts
from src.database import init_database, is_processed, mark_processed
from src.email_sender import generate_html, send_email

def main(test_mode=False):
    load_dotenv()
    
    init_database()
    
    print("开始爬取36氪融资数据...")
    funding_data = crawl_36kr_funding()
    print(f"获取到 {len(funding_data)} 条融资信息")
    
    if not funding_data:
        print("未获取到融资数据")
        if not test_mode:
            html = generate_html([])
            send_email(html)
        return
    
    qualified_companies = []
    
    for item in funding_data:
        company_name = item.get('company_name', '')
        
        if not company_name:
            continue
        
        if is_processed(company_name):
            print(f"公司 {company_name} 已处理过，跳过")
            continue
        
        print(f"处理公司: {company_name}")
        
        industry = item.get('industry', '')
        funding_round = item.get('funding_round', '')
        amount = item.get('amount', '')
        funding_date = item.get('funding_date', '')
        
        print(f"  行业: {industry}, 轮次: {funding_round}, 金额: {amount}")
        
        ai_result = score_company(company_name, industry, funding_round, amount)
        score = ai_result.get('score', 0)
        reason = ai_result.get('reason', '')
        need_factory = ai_result.get('need_factory', False)
        
        print(f"  AI评分: {score}, 需要厂房: {need_factory}")
        
        if score >= 6 and need_factory:
            print(f"  ✓ 符合条件")
            
            if test_mode:
                qualified_company = {
                    'company_name': company_name,
                    'industry': industry,
                    'funding_round': funding_round,
                    'amount': amount,
                    'funding_date': funding_date,
                    'score': score,
                    'reason': reason,
                    'legal_representative': '测试数据',
                    'phone': '测试数据',
                    'email': '测试数据',
                    'address': '测试数据',
                    'google_results': []
                }
            else:
                print(f"  查询联系人信息...")
                contacts = get_company_contacts(company_name)
                
                qualified_company = {
                    'company_name': company_name,
                    'industry': industry,
                    'funding_round': funding_round,
                    'amount': amount,
                    'funding_date': funding_date,
                    'score': score,
                    'reason': reason,
                    'legal_representative': contacts.get('legal_representative', ''),
                    'phone': contacts.get('phone', ''),
                    'email': contacts.get('email', ''),
                    'address': contacts.get('address', ''),
                    'google_results': contacts.get('google_results', [])
                }
            
            qualified_companies.append(qualified_company)
        
        mark_processed(company_name)
    
    print(f"\n共找到 {len(qualified_companies)} 家符合条件的公司")
    
    html = generate_html(qualified_companies)
    
    if test_mode:
        print("\n测试模式 - 生成的HTML内容已保存到 test_output.html")
        with open("test_output.html", "w", encoding="utf-8") as f:
            f.write(html)
    else:
        print("\n发送邮件...")
        send_email(html)
    
    print("任务完成")

if __name__ == "__main__":
    test_mode = len(sys.argv) > 1 and sys.argv[1] == "--test"
    main(test_mode=test_mode)