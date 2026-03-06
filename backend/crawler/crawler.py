import sqlite3
import datetime
import time
import random
import os
import uuid
from openai import OpenAI

# 配置
# 获取 backend/db 目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "news.db")

# 环境变量配置 (Zeabur / GitHub Secrets)
AI_API_KEY = os.getenv("AI_API_KEY", "") 
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com") # 默认 DeepSeek
AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat") # 默认模型

def get_db_connection():
    # 确保目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def mock_crawl_wtt():
    """
    模拟抓取 WTT (世界乒联) 官网新闻
    (实际项目中这里应该替换为真实的 requests + BeautifulSoup 抓取逻辑)
    """
    print("正在模拟抓取 WTT 官网 (Top 30)...")
    time.sleep(1) 
    
    mock_data = []
    base_time = datetime.datetime.now()
    
    for i in range(30):
        publish_time = base_time - datetime.timedelta(hours=i*2 + random.randint(0, 1))
        time_str = publish_time.strftime("%Y-%m-%d %H:%M:%S")
        url_id = publish_time.strftime("%Y%m%d%H") + f"_{i}"
        
        # 模拟一些稍微真实一点的文本，方便 AI 总结
        item = {
            "title": f"【模拟】孙颖莎 WTT 多哈站第 {i+1} 轮精彩表现 - {time_str}",
            "content": f"""
            北京时间 {time_str}，WTT 多哈球星挑战赛激战正酣。
            中国乒乓球队主力、世界排名第一的孙颖莎在女单第 {i+1} 轮比赛中登场。
            
            **比赛过程**：
            孙颖莎今天的对手是来自欧洲的实力派选手。首局比赛，孙颖莎进入状态非常快，以 11-5 轻松拿下。
            第二局对手展开反扑，比分一度胶着至 8-8 平，关键时刻孙颖莎利用发球抢攻连得 3 分，以 11-8 再下一城。
            第三局彻底进入孙颖莎的节奏，她以 11-3 锁定胜局，大比分 3-0 晋级。
            
            **赛后采访**：
            在赛后接受采访时，孙颖莎表示：“今天自己调动得还不错，多哈的场馆氛围很好，感谢现场为我加油的球迷。”
            对于下一轮的对手，莎莎说：“会认真观看录像，做好困难准备。”
            
            (本条新闻由爬虫脚本自动生成，用于测试 AI 摘要功能)
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
    """
    if not AI_API_KEY:
        print(f"⚠️ 未配置 AI_API_KEY，跳过 AI 摘要 (使用 Mock 数据)")
        return f"**【AI 摘要 (Mock)】**\n\n(请配置 AI_API_KEY 以启用真实摘要)\n\n{content[:150].strip()}..."
    
    print(f"🤖 正在请求 AI 摘要: {title[:10]}...")
    
    try:
        client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
        
        prompt = f"""
        请你扮演一位专业的乒乓球新闻编辑。请将以下新闻内容提炼为一个【图文摘要】，要求：
        1. **字数**：200字以内，言简意赅。
        2. **格式**：使用 Markdown 格式。
        3. **重点**：突出比赛比分、孙颖莎的关键表现、赛后金句。
        4. **图片**：如果原文没有图片，请在合适的位置插入一张孙颖莎的通用配图占位符 (Markdown 图片语法: ![孙颖莎](https://picsum.photos/400/300?random={random.randint(1,1000)}) )。
        5. **语气**：积极向上，专业客观。

        新闻标题：{title}
        新闻内容：
        {content}
        """

        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的体育资讯摘要助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        summary = response.choices[0].message.content.strip()
        print("✅ AI 摘要生成成功！")
        return summary

    except Exception as e:
        print(f"❌ AI 调用失败: {e}")
        return f"**【AI 处理出错】**\n\n暂时无法生成摘要，请稍后再试。\nError: {str(e)}"

def save_to_db(news_item):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 检查是否已存在
        cursor.execute('SELECT title, summary FROM news WHERE original_url = ?', (news_item['url'],))
        existing = cursor.fetchone()
        
        # 智能跳过逻辑：
        # 如果已存在，且摘要不包含 "Mock" 或 "模拟" 字样，说明已经是真实摘要，跳过（省钱）。
        # 如果包含 "Mock"，说明是旧数据，需要覆盖。
        if existing and existing['summary']:
            summary_text = existing['summary']
            is_mock = "**【AI 摘要 (Mock)】**" in summary_text or "【模拟】" in summary_text or "Mock" in summary_text
            
            if not is_mock:
                print(f"⏭️ 已存在真实摘要 (跳过): {news_item['title']}")
                return
            else:
                print(f"🔄 发现旧 Mock 数据，准备覆盖: {news_item['title']}")

        # 2. 生成摘要 (调用 AI)
        summary = ai_summarize(news_item['title'], news_item['content'])
        
        # 3. 插入或更新
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
        
        if existing:
            print(f"🔄 更新数据 (AI 摘要): {news_item['title']}")
        else:
            print(f"✅ 新增数据 (AI 摘要): {news_item['title']}")
            
    except Exception as e:
        print(f"❌ 保存失败: {e}")
    finally:
        conn.close()

def run():
    # 1. 初始化数据库
    if not os.path.exists(DB_PATH):
        # 尝试调用 main.py 里的 init_db 或者直接在这里创建目录
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # 2. 抓取数据
    news_list = mock_crawl_wtt()
    
    # 3. 处理并保存
    print(f"获取到 {len(news_list)} 条数据，开始处理...")
    for news in news_list:
        save_to_db(news)
        
    print("🎉 爬虫任务完成！")

if __name__ == "__main__":
    run()
