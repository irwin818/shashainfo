import sqlite3
import datetime
import time
import random
import os
import uuid

# 配置
# 获取 backend/db 目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "news.db")
# 如果你有真实 API Key，请填入这里 (例如 OpenAI, DeepSeek, Gemini)
AI_API_KEY = os.getenv("AI_API_KEY", "") 
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.openai.com/v1") # 默认 OpenAI

def get_db_connection():
    # 确保目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def mock_crawl_wtt():
    """
    模拟抓取 WTT (世界乒联) 官网新闻
    每次生成 30 条数据，模拟“最新”的新闻
    """
    print("正在模拟抓取 WTT 官网 (Top 30)...")
    time.sleep(1) # 模拟网络请求
    
    mock_data = []
    base_time = datetime.datetime.now()
    
    # 模拟 30 条新闻
    for i in range(30):
        # 模拟发布时间：从现在开始，每条间隔 1-2 小时
        publish_time = base_time - datetime.timedelta(hours=i*2 + random.randint(0, 1))
        time_str = publish_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 模拟唯一 URL (基于时间戳，确保去重逻辑生效)
        # 实际爬虫中，这里应该是真实的网页链接
        url_id = publish_time.strftime("%Y%m%d%H") + f"_{i}"
        
        item = {
            "title": f"【模拟】孙颖莎 WTT 多哈站第 {i+1} 轮精彩表现 - {time_str}",
            "content": f"""
            北京时间 {time_str}，孙颖莎在 WTT 多哈球星挑战赛中表现出色。
            
            **比赛回顾**：
            在刚刚结束的比赛中，孙颖莎以 3-0 的比分战胜对手。
            三局比分分别为：11-5, 11-8, 11-3。
            
            **赛后声音**：
            孙颖莎赛后表示：“今天状态调整得不错，对接下来的比赛充满信心。”
            
            ![比赛现场图](https://picsum.photos/seed/{url_id}/400/300)
            
            (本条新闻由爬虫脚本自动生成，用于测试定时任务和去重逻辑)
            """,
            "source": random.choice(["WTT官网", "央视体育", "乒乓世界", "微博"]),
            "url": f"https://mock.wtt.com/news/{url_id}",
            "publish_time": time_str
        }
        mock_data.append(item)
        
    return mock_data

def ai_summarize(title, content):
    """
    调用 AI API 生成图文摘要
    如果未配置 API Key，则使用简单的截断逻辑作为 Mock
    """
    if not AI_API_KEY:
        # 简单的 Mock 摘要逻辑
        summary = f"**【AI 摘要】**\n\n{content[:150].strip()}...\n\n(此摘要由模拟 AI 生成，请配置 API Key 以启用真实智能摘要)"
        return summary
    
    return f"AI 处理接口待接入: {title}"

def save_to_db(news_item):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 生成摘要
        summary = ai_summarize(news_item['title'], news_item['content'])
        
        # 检查是否已存在 (用于日志显示)
        cursor.execute('SELECT 1 FROM news WHERE original_url = ?', (news_item['url'],))
        exists = cursor.fetchone()

        # 插入或更新数据 (Upsert)
        # SQLite 的 Upsert 语法: INSERT INTO ... ON CONFLICT(col) DO UPDATE SET ...
        cursor.execute('''
        INSERT INTO news (title, summary, publish_time, source, original_url)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(original_url) DO UPDATE SET
            title=excluded.title,
            summary=excluded.summary,
            publish_time=excluded.publish_time,
            source=excluded.source
        ''', (
            news_item['title'],
            summary,
            news_item['publish_time'],
            news_item['source'],
            news_item['url']
        ))
        conn.commit()
        
        if exists:
            print(f"🔄 更新: {news_item['title']}")
        else:
            print(f"✅ 新增: {news_item['title']}")
            
    except Exception as e:
        print(f"❌ 保存失败: {e}")
    finally:
        conn.close()

def run():
    # 1. 初始化数据库 (如果不存在)
    if not os.path.exists(DB_PATH):
        print("数据库不存在，正在初始化...")
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from db.init_sqlite import init_db
        init_db()

    # 2. 抓取数据
    news_list = mock_crawl_wtt()
    
    # 3. 处理并保存
    print(f"获取到 {len(news_list)} 条数据，开始入库...")
    for news in news_list:
        save_to_db(news)
        
    print("🎉 爬虫任务完成！")

if __name__ == "__main__":
    run()
