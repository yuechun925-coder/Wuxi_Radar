import os
import smtplib
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

TIANYANCHA_MCP_URL = "https://mcp.tianyancha.com/v1"
TIANYANCHA_AUTH_TOKEN = "eea76d7b-4e2f-4254-a9ef-6fd48cef3794"

def get_tianyancha_recommendations():
    import requests
    
    url = f"{TIANYANCHA_MCP_URL}/search"
    
    headers = {
        "Authorization": TIANYANCHA_AUTH_TOKEN,
        "Content-Type": "application/json"
    }
    
    industries = ['生物医药', '半导体', '新能源', '精密制造']
    cities = ['无锡', '苏州', '常州', '上海', '南京', '杭州', '嘉兴']
    
    all_companies = []
    
    for industry in industries:
        for city in cities:
            try:
                params = {
                    "keyword": f"{industry} {city}"
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") == 200 and data.get("data"):
                    for company in data["data"]:
                        reg_capital = company.get('regCapital', '')
                        try:
                            if '万' in reg_capital:
                                amount = float(reg_capital.replace('万', '').replace('人民币', '').strip())
                                if amount >= 1000:
                                    all_companies.append({
                                        'company_name': company.get('name', ''),
                                        'industry': industry,
                                        'city': city,
                                        'reg_capital': reg_capital,
                                        'legal_representative': company.get('legalPersonName', ''),
                                        'phone': company.get('phone', ''),
                                        'email': company.get('email', ''),
                                        'address': company.get('regAddress', '')
                                    })
                        except:
                            continue
            except Exception as e:
                print(f"获取推荐企业失败: {e}")
                continue
    
    return random.sample(all_companies, min(3, len(all_companies)))

def get_html_template():
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>招商情报日报</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 24px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .header p {
            margin: 8px 0 0;
            opacity: 0.9;
        }
        .content {
            padding: 24px;
        }
        .company-card {
            background-color: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            transition: box-shadow 0.2s;
        }
        .company-card:hover {
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        }
        .company-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }
        .company-name {
            font-size: 20px;
            font-weight: 600;
            color: #333;
        }
        .score {
            background-color: #4CAF50;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 16px;
            font-weight: bold;
        }
        .score.medium {
            background-color: #FF9800;
        }
        .score.high {
            background-color: #4CAF50;
        }
        .info-row {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 12px;
            font-size: 14px;
            color: #666;
        }
        .info-item {
            display: flex;
            align-items: center;
        }
        .info-label {
            font-weight: 500;
            color: #333;
            margin-right: 4px;
        }
        .reason-box {
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 12px 16px;
            border-radius: 0 4px 4px 0;
            margin-bottom: 16px;
        }
        .reason-box p {
            margin: 0;
            font-size: 14px;
            color: #444;
            line-height: 1.6;
        }
        .contacts-section {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #eee;
        }
        .contact-item {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 14px;
        }
        .contact-icon {
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 8px;
            color: #667eea;
        }
        .google-links {
            margin-top: 12px;
        }
        .google-links h4 {
            margin: 0 0 8px;
            font-size: 14px;
            color: #333;
        }
        .google-links ul {
            margin: 0;
            padding-left: 20px;
        }
        .google-links li {
            margin-bottom: 4px;
            font-size: 13px;
        }
        .google-links a {
            color: #667eea;
            text-decoration: none;
        }
        .google-links a:hover {
            text-decoration: underline;
        }
        .footer {
            background-color: #f5f5f5;
            padding: 16px 24px;
            text-align: center;
            color: #888;
            font-size: 13px;
        }
        .no-companies {
            text-align: center;
            padding: 40px;
            color: #888;
        }
        .no-companies p {
            margin: 0;
        }
        .recommendation-section {
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            border-left: 4px solid #ff9800;
            padding: 20px;
            border-radius: 0 8px 8px 0;
            margin-top: 20px;
        }
        .recommendation-title {
            font-size: 18px;
            font-weight: 600;
            color: #e65100;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
        }
        .recommendation-title span {
            margin-right: 8px;
        }
        .recommendation-card {
            background-color: white;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏭 __TITLE__</h1>
            <p>日期: __DATE_STR__</p>
        </div>
        <div class="content">
            __COMPANY_CARDS__
            __RECOMMENDATIONS__
        </div>
        <div class="footer">
            <p>自动生成 - 招商情报系统</p>
        </div>
    </div>
</body>
</html>
'''

def get_company_card_template():
    return '''
<div class="company-card">
    <div class="company-header">
        <div class="company-name">__COMPANY_NAME__</div>
        <div class="score __SCORE_CLASS__">__SCORE__分</div>
    </div>
    <div class="info-row">
        <div class="info-item"><span class="info-label">融资轮次:</span> __FUNDING_ROUND__</div>
        <div class="info-item"><span class="info-label">融资金额:</span> __AMOUNT__</div>
        <div class="info-item"><span class="info-label">行业:</span> __INDUSTRY__</div>
        <div class="info-item"><span class="info-label">日期:</span> __FUNDING_DATE__</div>
        <div class="info-item"><span class="info-label">来源:</span> __SOURCE__</div>
    </div>
    <div class="reason-box">
        <p><strong>AI评估理由:</strong> __REASON__</p>
    </div>
    <div class="contacts-section">
        <div class="contact-item">
            <span class="contact-icon">👤</span>
            <span><strong>法定代表人:</strong> __LEGAL_REPRESENTATIVE__</span>
        </div>
        <div class="contact-item">
            <span class="contact-icon">📞</span>
            <span><strong>联系电话:</strong> __PHONE__</span>
        </div>
        <div class="contact-item">
            <span class="contact-icon">📧</span>
            <span><strong>邮箱:</strong> __EMAIL__</span>
        </div>
        <div class="contact-item">
            <span class="contact-icon">📍</span>
            <span><strong>地址:</strong> __ADDRESS__</span>
        </div>
        __GOOGLE_LINKS__
    </div>
</div>
'''

def get_google_links_template():
    return '''
<div class="google-links">
    <h4>🔍 相关搜索结果:</h4>
    <ul>
        __LINKS__
    </ul>
</div>
'''

def get_recommendation_template():
    return '''
<div class="recommendation-section">
    <div class="recommendation-title">
        <span>🎯</span>主动挖掘目标企业
    </div>
    <p style="color: #666; margin-bottom: 16px; font-size: 14px;">
        根据无锡招商标准（生物医药/半导体/注册资本>1000万），为您推荐以下长三角地区的潜在目标企业：
    </p>
    __RECOMMENDATION_CARDS__
</div>
'''

def get_recommendation_card_template():
    return '''
<div class="recommendation-card">
    <div style="font-size: 16px; font-weight: 600; color: #333; margin-bottom: 8px;">
        __COMPANY_NAME__
    </div>
    <div style="display: flex; flex-wrap: wrap; gap: 12px; font-size: 14px; color: #666;">
        <span><strong>行业:</strong> __INDUSTRY__</span>
        <span><strong>地区:</strong> __CITY__</span>
        <span><strong>注册资本:</strong> __REG_CAPITAL__</span>
    </div>
    <div style="margin-top: 8px; font-size: 13px; color: #888;">
        <div><strong>法定代表人:</strong> __LEGAL_REP__</div>
        <div><strong>电话:</strong> __PHONE__</div>
        <div><strong>地址:</strong> __ADDRESS__</div>
    </div>
</div>
'''

def generate_html(companies, recommendations=None):
    date_str = datetime.now().strftime("%Y年%m月%d日")
    
    if companies:
        title = "招商情报日报"
    else:
        title = "【招商日报】今日市场动态与推荐"
    
    template = get_html_template().replace('__TITLE__', title).replace('__DATE_STR__', date_str)
    
    if not companies:
        company_cards = '<div class="no-companies"><p>今日暂无符合条件的招商目标企业</p></div>'
    else:
        company_cards = ""
        card_template = get_company_card_template()
        
        for company in companies:
            score = company['score']
            score_class = 'high' if score >= 8 else 'medium' if score >= 6 else ''
            
            if company.get('google_results'):
                links_html = "\n".join([f'<li><a href="{link}" target="_blank">{link}</a></li>' for link in company['google_results']])
                google_links_html = get_google_links_template().replace('__LINKS__', links_html)
            else:
                google_links_html = ""
            
            card = card_template.replace('__COMPANY_NAME__', company.get('company_name', '')) \
                               .replace('__SCORE__', str(score)) \
                               .replace('__SCORE_CLASS__', score_class) \
                               .replace('__FUNDING_ROUND__', company.get('funding_round', '')) \
                               .replace('__AMOUNT__', company.get('amount', '')) \
                               .replace('__INDUSTRY__', company.get('industry', '')) \
                               .replace('__FUNDING_DATE__', company.get('funding_date', '')) \
                               .replace('__SOURCE__', company.get('source', '未知')) \
                               .replace('__REASON__', company.get('reason', '')) \
                               .replace('__LEGAL_REPRESENTATIVE__', company.get('legal_representative', '未找到')) \
                               .replace('__PHONE__', company.get('phone', '未找到')) \
                               .replace('__EMAIL__', company.get('email', '未找到')) \
                               .replace('__ADDRESS__', company.get('address', '未找到')) \
                               .replace('__GOOGLE_LINKS__', google_links_html)
            
            company_cards += card
    
    if recommendations and len(recommendations) > 0:
        rec_cards = ""
        rec_card_template = get_recommendation_card_template()
        
        for rec in recommendations:
            rec_card = rec_card_template.replace('__COMPANY_NAME__', rec.get('company_name', '')) \
                                       .replace('__INDUSTRY__', rec.get('industry', '')) \
                                       .replace('__CITY__', rec.get('city', '')) \
                                       .replace('__REG_CAPITAL__', rec.get('reg_capital', '')) \
                                       .replace('__LEGAL_REP__', rec.get('legal_representative', '未找到')) \
                                       .replace('__PHONE__', rec.get('phone', '未找到')) \
                                       .replace('__ADDRESS__', rec.get('address', '未找到'))
            
            rec_cards += rec_card
        
        recommendations_html = get_recommendation_template().replace('__RECOMMENDATION_CARDS__', rec_cards)
    else:
        recommendations_html = ""
    
    return template.replace('__COMPANY_CARDS__', company_cards).replace('__RECOMMENDATIONS__', recommendations_html)

def send_email(html_content, subject=None):
    sender_email = os.getenv("GMAIL_USER")
    sender_password = os.getenv("GMAIL_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    
    if not sender_email or not sender_password or not recipient_email:
        raise ValueError("GMAIL_USER, GMAIL_PASSWORD, RECIPIENT_EMAIL environment variables not set")
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    if subject:
        msg['Subject'] = subject
    else:
        msg['Subject'] = f"🏭 招商情报日报 - {datetime.now().strftime('%Y-%m-%d')}"
    
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("邮件发送成功")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

if __name__ == "__main__":
    test_companies = []
    test_recommendations = [
        {
            'company_name': '示例生物科技公司',
            'industry': '生物医药',
            'city': '无锡',
            'reg_capital': '5000万人民币',
            'legal_representative': '张三',
            'phone': '13800138000',
            'address': '无锡市新吴区科技园区'
        }
    ]
    
    html = generate_html(test_companies, test_recommendations)
    print(html)