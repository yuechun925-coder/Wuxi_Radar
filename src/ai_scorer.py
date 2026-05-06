import os
import json
import requests

TARGET_INDUSTRIES = ['生物医药', '医疗技术', '半导体', '新能源', '精密制造']
RELATED_INDUSTRIES = ['医疗器械', '生物制药', '基因检测', '芯片', '集成电路', '光伏', '锂电', '智能制造', '高端制造', '新材料']

def local_score_company(company_name, industry, funding_round, amount):
    score = 0
    reasons = []
    
    industry_lower = industry.lower()
    
    industry_match = False
    related_match = False
    
    for target in TARGET_INDUSTRIES:
        if target.lower() in industry_lower or industry_lower in target.lower():
            score += 4
            industry_match = True
            reasons.append(f"行业匹配度高（{industry}属于目标产业）")
            break
    
    if not industry_match:
        for related in RELATED_INDUSTRIES:
            if related.lower() in industry_lower or industry_lower in related.lower():
                score += 2
                related_match = True
                reasons.append(f"行业较相关（{industry}属于相关领域）")
                break
    
    if not industry_match and not related_match:
        reasons.append(f"行业匹配度低（{industry}与目标产业不相关）")
    
    round_order = ['天使轮', 'Pre-A', 'A轮', 'A+轮', 'B轮', 'B+轮', 'C轮', 'C+轮', 'D轮', 'E轮', 'F轮', 'IPO', '战略投资']
    if funding_round:
        found_round = False
        for i, r in enumerate(round_order):
            if r in funding_round:
                if i >= 2:
                    score += 3
                    reasons.append(f"发展阶段成熟（{funding_round}）")
                else:
                    score += 1
                    reasons.append(f"发展阶段较早（{funding_round}）")
                found_round = True
                break
        if not found_round:
            score += 1
            reasons.append(f"发展阶段评估（{funding_round}）")
    else:
        reasons.append("融资轮次未知")
    
    if amount:
        score += 2
        reasons.append(f"有明确融资金额（{amount}）")
    else:
        reasons.append("融资金额未知")
    
    need_factory = industry_match or related_match
    
    if need_factory:
        score += 1
        reasons.append("属于制造业，需要厂房")
    else:
        reasons.append("可能为轻资产公司")
    
    return {
        "score": min(10, score),
        "reason": "; ".join(reasons),
        "need_factory": need_factory
    }

def score_company(company_name, industry, funding_round, amount):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("未配置DeepSeek API密钥，使用本地评分逻辑")
        return local_score_company(company_name, industry, funding_round, amount)
    
    url = "https://api.deepseek.com/v1/chat/completions"
    
    prompt = f"""
你是一个专业的工业园区招商分析师。请根据以下公司信息，评估该公司是否适合入驻我们专注于生物医药、医疗技术、半导体、新能源、精密制造的工业园区。

工业园区信息：
- 面积需求：1700-6500㎡厂房
- 重点产业：生物医药、医疗技术、半导体、新能源、精密制造

公司信息：
- 公司名称：{company_name}
- 行业：{industry}
- 融资轮次：{funding_round}
- 融资金额：{amount}

请按照以下JSON格式输出评估结果：
{{
    "score": 0-10的整数，表示适合度评分，10分为最适合，0分为完全不适合",
    "reason": "详细说明评分理由，包括行业匹配度、发展阶段、资金实力等",
    "need_factory": true或false，表示该公司是否需要厂房"
}}

评分标准：
1. 行业匹配度（4分）：生物医药/医疗技术/半导体/新能源/精密制造相关得4分，相关领域得2分，不相关得0分
2. 发展阶段（3分）：A轮及以后得3分，天使轮/Pre-A得1分
3. 资金实力（2分）：有明确融资金额得2分，金额较大得额外加分
4. 厂房需求（1分）：制造业、生产型企业得1分，纯软件/服务型得0分

请严格按照JSON格式输出，不要添加额外文字。
"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        content = data["choices"][0]["message"]["content"].strip()
        
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            content = content.replace("```json", "").replace("```", "").strip()
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                print("AI返回格式解析失败，使用本地评分逻辑")
                return local_score_company(company_name, industry, funding_round, amount)
    
    except requests.exceptions.HTTPError as e:
        print(f"DeepSeek API调用失败: {e}")
        print("使用本地评分逻辑")
        return local_score_company(company_name, industry, funding_round, amount)
    except Exception as e:
        print(f"调用DeepSeek API失败: {e}")
        print("使用本地评分逻辑")
        return local_score_company(company_name, industry, funding_round, amount)

if __name__ == "__main__":
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    result = score_company("示例生物科技公司", "生物医药", "B轮", "5000万元")
    print(result)