from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager

# 导入爬虫模块 (确保 crawler.py 在 backend/crawler 目录下)
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from crawler import crawler

# --- 数据库配置 ---
# 获取当前文件所在目录 (backend)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "news.db")

def init_db():
    """初始化数据库：确保目录存在，创建表结构"""
    print(f"Checking database at: {DB_PATH}")
    
    # 1. 确保目录存在
    if not os.path.exists(DB_DIR):
        print(f"Creating database directory: {DB_DIR}")
        os.makedirs(DB_DIR, exist_ok=True)
    
    # 2. 连接并创建表
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建 news 表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            publish_time TIMESTAMP NOT NULL,
            source TEXT NOT NULL,
            original_url TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_publish_time ON news(publish_time DESC)')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行数据库初始化
    init_db()
    yield

app = FastAPI(title="孙颖莎每日资讯 API", lifespan=lifespan)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewsItem(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    publish_time: str
    source: str
    original_url: Optional[str] = None
    created_at: str

def get_db_connection():
    # 运行时再次确保目录存在
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def read_root():
    return {"Hello": "World", "Project": "孙颖莎每日资讯", "Status": "Running"}

@app.get("/news", response_model=List[NewsItem])
def get_news(limit: int = 20, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, title, summary, publish_time, source, original_url, created_at
            FROM news
            ORDER BY publish_time DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Query error: {e}")
        return []
    finally:
        conn.close()

# --- 新增：手动触发爬虫的接口 ---
def run_crawler_task():
    print("Starting manual crawler task...")
    try:
        crawler.run()
        print("Manual crawler task finished.")
    except Exception as e:
        print(f"Manual crawler task failed: {e}")

@app.get("/crawl")
def trigger_crawler(background_tasks: BackgroundTasks):
    """
    手动触发爬虫 (后台运行) - GET 方便浏览器直接调用
    """
    background_tasks.add_task(run_crawler_task)
    return {"message": "Crawler started in background"}
