"""
email_sender.py  —  HTML 日报生成 + 邮件发送
"""

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ──────────────────────────────────────────────
# HTML 生成
# ──────────────────────────────────────────────

_CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#f0f2f5;margin:0;padding:20px}
.wrap{max-width:860px;margin:0 auto}
.header{background:linear-gradient(135deg,#1D9E75,#0F6E56);color:#fff;padding:24px 28px;border-radius:12px 12px 0 0}
.header h1{margin:0;font-size:22px;font-weight:500}
.header p{margin:6px 0 0;opacity:.85;font-size:14px}
.body{background:#fff;padding:24px 28px;border-radius:0 0 12px 12px}
.section-title{font-size:13px;font-weight:500;color:#888;letter-spacing:.06em;text-transform:uppercase;margin:0 0 14px}
/* 企业卡片 */
.card{border:0.5px solid #e0e0e0;border-radius:10px;padding:18px 20px;margin-bottom:16px}
.card:hover{box-shadow:0 4px 14px rgba(0,0,0,.06)}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.company-name{font-size:17px;font-weight:500;color:#1a1a1a}
.score-badge{font-size:13px;font-weight:500;padding:3px 12px;border-radius:20px;background:#E1F5EE;color:#085041}
.score-high{background:#E1F5EE;color:#085041}
.score-mid{background:#FAEEDA;color:#633806}
.score-low{background:#F1EFE8;color:#5F5E5A}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.tag{font-size:12px;padding:2px 9px;border-radius:14px;background:#E6F1FB;color:#0C447C}
.tag.round{background:#EEEDFE;color:#3C3489}
.tag.amount{background:#E1F5EE;color:#085041}
.reason{background:#f8f9fb;border-left:3px solid #1D9E75;border-radius:0 6px 6px 0;padding:10px 14px;margin-bottom:14px;font-size:13px;color:#444;line-height:1.6}
.contacts{border-top:0.5px solid #eee;padding-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:6px}
.contact-item{font-size:13px;color:#555}
.contact-item strong{color:#222}
.link-list{list-style:none;padding:0;margin:8px 0 0}
.link-list li{margin-bottom:4px;font-size:12px}
.link-list a{color:#1D9E75;text-decoration:none}
/* FA 推荐表 */
.fa-table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
.fa-table th{text-align:left;padding:8px 10px;background:#f5f5f5;color:#555;font-weight:500;border-bottom:1px solid #e0e0e0}
.fa-table td{padding:8px 10px;border-bottom:0.5px solid #f0f0f0;color:#333}
.fa-table tr:last-child td{border-bottom:none}
/* 空状态 */
.empty{text-align:center;padding:40px 20px;color:#999}
.empty p{margin:4px 0;font-size:14px}
.footer{text-align:center;padding:16px;color:#aaa;font-size:12px}
"""


def _score_class(score: int) -> str:
    if score >= 7:
        return "score-high"
    elif score >= 5:
        return "score-mid"
    return "score-low"


def _company_card(c: dict) -> str:
    score = c.get("score", 0)
    sc = _score_class(score)

    tags_html = ""
    if c.get("industry"):
        tags_html += f'<span class="tag">{c["industry"]}</span>'
    if c.get("funding_round"):
        tags_html += f'<span class="tag round">{c["funding_round"]}</span>'
    if c.get("amount"):
        tags_html += f'<span class="tag amount">{c["amount"]}</span>'
    if c.get("source"):
        tags_html += f'<span class="tag" style="background:#F1EFE8;color:#5F5E5A">{c["source"]}</span>'

    contacts_html = ""
    fields = [
        ("法定代表人", c.get("legal_representative") or c.get("founder_name", "")),
        ("联系电话", c.get("phone", "")),
        ("邮箱", c.get("email", "")),
        ("地址", c.get("address", "")),
        ("LinkedIn", c.get("linkedin", "")),
    ]
    for label, val in fields:
        if val:
            if label == "LinkedIn":
                val_html = f'<a href="{val}" style="color:#1D9E75">{val[:50]}</a>'
            elif label == "邮箱":
                val_html = f'<a href="mailto:{val}" style="color:#1D9E75">{val}</a>'
            else:
                val_html = val
            contacts_html += f'<div class="contact-item"><strong>{label}：</strong>{val_html}</div>'

    google_html = ""
    gr = c.get("google_results", [])
    if gr:
        items = "".join(
            f'<li><a href="{r["url"]}" target="_blank">{r["title"][:50]}</a>'
            f'<span style="color:#999"> — {r["snippet"][:60]}</span></li>'
            for r in gr[:3] if r.get("title")
        )
        if items:
            google_html = f'<ul class="link-list">{items}</ul>'

    date_str = c.get("funding_date", "")

    return f"""
<div class="card">
  <div class="card-header">
    <div class="company-name">{c.get("company_name","")}</div>
    <div class="score-badge {sc}">{score}分</div>
  </div>
  <div class="tags">{tags_html}{'<span class="tag" style="background:#f5f5f5;color:#888">'+date_str+'</span>' if date_str else ''}</div>
  <div class="reason"><strong>AI 评估：</strong>{c.get("reason","")}</div>
  {'<div class="contacts">'+contacts_html+'</div>' if contacts_html else ''}
  {google_html}
</div>"""


def _fa_table(fa_list: list) -> str:
    def _link(f):
        hint = f.get("contact_hint", "")
        if hint:
            return f'<a href="https://{hint}" style="color:#1D9E75">官网</a>'
        return "—"

    rows = "".join(
        f'<tr><td><strong>{f["name"]}</strong></td><td>{f["focus"]}</td>'
        f'<td>{_link(f)}</td></tr>'
        for f in fa_list
    )
    return f"""
<table class="fa-table">
  <thead><tr><th>机构名称</th><th>重点赛道</th><th>联系</th></tr></thead>
  <tbody>{rows}</tbody>
</table>"""


def generate_html(companies: list, fa_recommendations: list = None) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    count = len(companies)

    if count > 0:
        summary = f"今日发现 <strong>{count}</strong> 家符合条件的目标企业"
        cards_html = "".join(_company_card(c) for c in companies)
        main_html = f"""
<p class="section-title">今日目标企业</p>
{cards_html}"""
    else:
        summary = "今日暂无新目标企业（展示 FA 中介资源，可冷外联获取项目线索）"
        main_html = """
<div class="empty">
  <p>📭 今日融资快讯中暂无新增符合条件的企业</p>
  <p style="color:#bbb;font-size:12px">明日将继续扫描，以下为可冷外联的 FA / 投资机构资源</p>
</div>"""

    fa_section = ""
    if fa_recommendations:
        fa_section = f"""
<div style="margin-top:24px">
  <p class="section-title">可冷外联的 FA / 投资机构（间接获取项目）</p>
  <p style="font-size:13px;color:#888;margin:0 0 10px">这些机构的 portfolio 企业是优质招商目标，通过 FA 推荐入园可大幅降低销售成本</p>
  {_fa_table(fa_recommendations)}
</div>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>招商情报日报 · {today}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>🏭 无锡园区 · 招商情报日报</h1>
    <p>{today} · {summary}</p>
  </div>
  <div class="body">
    {main_html}
    {fa_section}
  </div>
  <div class="footer">自动生成 · Wuxi Radar · 数据来源：36氪 / 投资界 / 创业邦 / IT桔子</div>
</div>
</body>
</html>"""


# ──────────────────────────────────────────────
# 邮件发送
# ──────────────────────────────────────────────

def send_email(html: str):
    gmail_user = os.getenv("GMAIL_USER", "")
    gmail_password = os.getenv("GMAIL_PASSWORD", "")
    recipient = os.getenv("RECIPIENT_EMAIL", gmail_user)

    if not gmail_user or not gmail_password:
        print("[邮件] 未配置 GMAIL_USER / GMAIL_PASSWORD，跳过发送")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"招商情报日报 · {today}"
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, [recipient], msg.as_string())
        print(f"[邮件] 已发送至 {recipient}")
    except Exception as e:
        print(f"[邮件] 发送失败: {e}")


# ──────────────────────────────────────────────
# 兼容旧接口（main.py 调用的）
# ──────────────────────────────────────────────

def get_tianyancha_recommendations() -> list:
    """
    保持与 main.py 接口兼容，返回 FA 机构列表。
    原名 get_tianyancha_recommendations 保留不变。
    """
    from src.contacts import get_fa_recommendations
    return get_fa_recommendations()
