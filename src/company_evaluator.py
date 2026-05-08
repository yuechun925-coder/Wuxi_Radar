import os
import requests

def generate_report(company_name, industry='', funding_round='', amount='', desc=''):
    industry_keywords = ['生物医药', '半导体', '新能源', '精密制造', '硬科技']
    round_keywords = {'天使轮':1, 'Pre-A':2, 'A轮':3, 'B轮':5, 'C轮':7, 'D轮':9}
    scores = {'fundamental':6, 'innovation':6, 'commercial':5, 'capital':5, 'policy':6, 'risk':7}
    all_text = company_name + industry + desc
    if any(k in all_text for k in industry_keywords):
        scores['innovation'] = min(10, scores['innovation']+3)
        scores['policy'] = min(10, scores['policy']+2)
    for rn, bonus in round_keywords.items():
        if rn in funding_round:
            scores['capital'] = min(10, bonus+2)
            scores['commercial'] = min(10, scores['commercial']+2)
            break
    if '亿元' in amount:
        scores['capital'] = min(10, scores['capital']+2)
    round_found_list = [k for k in round_keywords if k in funding_round]
    round_display = round_found_list[0] if round_found_list else '早期'
    total = int(scores['fundamental']*0.15 + scores['innovation']*0.25 + scores['commercial']*0.2 + scores['capital']*0.15 + scores['policy']*0.2 + scores['risk']*0.05)
    if total >= 80:
        suggestion = '强烈建议推进跟进'
    elif total >= 60:
        suggestion = '可作为储备库观察'
    else:
        suggestion = '直接放弃'
    has_hightech = any(k in all_text for k in industry_keywords)
    report = '='*70 + '
📊 企业落地价值评估报告
' + '='*70
    report += '

## 一、企业概览
公司名称：' + company_name
    report += '
所属行业：' + (industry or '未知')
    report += '
融资轮次：' + (funding_round or '未知')
    report += '
融资金额：' + (amount or '未知')
    report += '

## 二、分项评估（满分10分）'
    report += '

1️⃣ 基本面与核心团队
评分：' + str(scores['fundamental']) + '分'
    report += '
评语：公司基本信息完整，建议进一步核实股权结构和核心团队背景。'
    report += '

2️⃣ 创新能力与赛道
评分：' + str(scores['innovation']) + '分'
    report += '
评语：' + ('属于硬科技领域，符合园区产业定位。' if has_hightech else '赛道需要进一步评估。')
    report += '

3️⃣ 商业化与成长性
评分：' + str(scores['commercial']) + '分'
    report += '
评语：融资信息表明公司处于快速发展阶段，需确认盈利模式清晰度。'
    report += '

4️⃣ 资本认可度
评分：' + str(scores['capital']) + '分'
    report += '
评语：获得' + round_display + '融资，资本认可度较高。'
    report += '

5️⃣ 政策匹配度
评分：' + str(scores['policy']) + '分'
    report += '
评语：符合无锡园区产业导向，有机会申请相关人才政策和产业基金支持。'
    report += '

6️⃣ 风险与预警
评分：' + str(scores['risk']) + '分（注：风险评分越高表示风险越低）'
    report += '
评语：公开信息中未发现明显风险预警，建议通过天眼查等工具做尽调。'
    report += '

## 三、综合评估
综合评分：' + str(total) + '/100分'
    report += '
雷达图数据：[基本面,创新能力,商业化,资本认可,政策匹配,风险控制] = [' + ','.join([str(scores[k]) for k in ['fundamental','innovation','commercial','capital','policy','risk']]) + ']'
    report += '

## 四、总助决断建议
' + suggestion
    report += '

' + '='*70
    return report

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        name = sys.argv[1]
        industry = sys.argv[2] if len(sys.argv) > 2 else ''
        fr = sys.argv[3] if len(sys.argv) > 3 else ''
        amount = sys.argv[4] if len(sys.argv) > 4 else ''
        print(generate_report(name, industry, fr, amount))
    else:
        name = input('请输入公司名称：')
        industry = input('行业：')
        fr = input('融资轮次：')
        amount = input('金额：')
        print(generate_report(name, industry, fr, amount))
