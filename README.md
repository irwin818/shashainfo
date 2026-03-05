# 孙颖莎每日资讯小程序 - 开发指南

## 🚀 快速启动

### 1. 后端 (Backend)

后端使用 Python FastAPI，数据库使用 SQLite (本地) / Supabase (线上)。

**环境准备**:
```bash
pip install requests beautifulsoup4 fastapi uvicorn pydantic
```

**运行爬虫 (生成数据)**:
```bash
python3 backend/crawler/crawler.py
```
> 注意：目前爬虫使用 Mock 数据和模拟 AI 摘要。如需真实 AI 摘要，请在 `crawler.py` 中配置 `AI_API_KEY`。

**启动 API 服务器**:
```bash
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
API 地址: `http://localhost:8000/news`

### 2. 前端 (Mini Program)

前端为原生微信小程序。

**导入项目**:
1. 打开 **微信开发者工具**。
2. 选择 **导入项目**，目录指向 `miniprogram/` 文件夹。
3. AppID 可以使用测试号。

**关键设置**:
*   在开发者工具右上角 -> **详情** -> **本地设置** -> 勾选 ✅ **不校验合法域名、web-view（业务域名）、TLS版本以及HTTPS证书**。
*   (因为本地 API 是 `http://localhost:8000`，非 HTTPS)

## 📂 目录结构

*   `backend/`
    *   `crawler/`: 爬虫脚本
    *   `db/`: 数据库文件 (SQLite) & Schema
    *   `main.py`: 后端 API 入口
*   `miniprogram/`: 微信小程序源码

## ✨ 功能说明
*   **列表页**: 展示新闻标题、来源、时间。
*   **交互**: 点击标题 -> 展开显示 AI 生成的图文摘要 (手风琴效果)。
