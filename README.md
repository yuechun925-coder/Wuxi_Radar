# 自动招商情报系统

一个自动抓取融资信息、AI评估、联系人查询并发送日报邮件的招商情报系统。

## 功能特性

- **自动爬取**：每天抓取36氪最新融资动态
- **AI评分**：使用DeepSeek API对公司进行评分，判断是否适合入驻工业园区
- **联系人查询**：通过天眼查MCP和Google搜索获取公司联系信息
- **去重机制**：使用SQLite记录已处理公司，避免重复推送
- **邮件推送**：生成精美HTML日报，自动发送到指定邮箱
- **定时任务**：通过GitHub Actions每天自动运行

## 技术栈

- Python 3.11
- requests
- beautifulsoup4
- google (Google搜索)
- sqlite3
- smtplib (邮件发送)
- python-dotenv

## 项目结构

```
Wuxi_Radar/
├── .github/
│   └── workflows/
│       └── crawler.yml        # GitHub Actions配置
├── src/
│   ├── crawler.py             # 36氪爬虫模块
│   ├── ai_scorer.py           # DeepSeek AI评分模块
│   ├── contacts.py            # 天眼查MCP和Google搜索模块
│   ├── database.py            # SQLite数据库模块
│   └── email_sender.py        # 邮件发送模块
├── .env                       # 环境变量配置
├── requirements.txt           # 依赖列表
├── main.py                    # 主程序入口
└── README.md                  # 项目文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境变量配置

创建 `.env` 文件，填入以下内容：

```env
DEEPSEEK_API_KEY=your-deepseek-api-key
GMAIL_USER=your-gmail-account@gmail.com
GMAIL_PASSWORD=your-gmail-app-password
RECIPIENT_EMAIL=recipient@example.com
```

**注意**：Gmail需要使用[App Password](https://myaccount.google.com/apppasswords)（需开启2FA）

## 运行方式

### 本地运行

```bash
python main.py
```

### GitHub Actions自动运行

1. 将项目推送到GitHub仓库
2. 在仓库Settings -> Secrets and variables -> Actions中添加以下secrets：
   - `DEEPSEEK_API_KEY`
   - `GMAIL_USER`
   - `GMAIL_PASSWORD`
   - `RECIPIENT_EMAIL`

系统会每天北京时间08:00自动运行。

## 评分标准

AI评分系统采用10分制：

| 评分维度 | 分值 | 说明 |
|---------|------|------|
| 行业匹配度 | 4分 | 生物医药/医疗技术/半导体/新能源/精密制造相关得4分 |
| 发展阶段 | 3分 | A轮及以后得3分，天使轮/Pre-A得1分 |
| 资金实力 | 2分 | 有明确融资金额得2分 |
| 厂房需求 | 1分 | 制造业、生产型企业得1分 |

## 输出示例

系统会生成HTML邮件，包含符合条件的公司卡片，每张卡片包含：
- 公司名称和AI评分
- 融资信息（轮次、金额、行业、日期）
- AI评估理由
- 联系人信息（法定代表人、电话、邮箱、地址）
- Google搜索结果链接

## License

MIT