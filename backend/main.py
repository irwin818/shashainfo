from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from pydantic import BaseModel
from typing import List, Optional
import datetime

app = FastAPI(title="孙颖莎每日资讯 API")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "backend/db/news.db"

# 尝试修正 DB 路径（兼容不同运行目录）
if not os.path.exists(DB_PATH):
    if os.path.exists("db/news.db"):
        DB_PATH = "db/news.db"
    elif os.path.exists("../db/news.db"):
        DB_PATH = "../db/news.db"

class NewsItem(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    publish_time: str
    source: str
    original_url: Optional[str] = None
    created_at: str

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def read_root():
    return {"Hello": "World", "Project": "孙颖莎每日资讯"}

@app.get("/news", response_model=List[NewsItem])
def get_news(limit: int = 20, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, summary, publish_time, source, original_url, created_at
        FROM news
        ORDER BY publish_time DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# 用于 Vercel 部署的 handler
# import uvicorn
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
