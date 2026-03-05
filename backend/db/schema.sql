-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- News Table
create table if not exists news (
  id uuid default uuid_generate_v4() primary key,
  title text not null, -- AI 生成的简短标题
  summary text,        -- AI 生成的图文摘要 (Markdown/HTML)
  publish_time timestamptz not null, -- 发布时间，用于排序
  source text not null, -- 来源 (e.g. "微博", "WTT官网")
  original_url text unique, -- 原文链接，用于去重
  created_at timestamptz default now() -- 入库时间
);

-- Index for faster sorting
create index if not exists idx_news_publish_time on news(publish_time desc);

-- RLS (Row Level Security) Policies
-- 允许所有用户读取 (用于小程序端)
alter table news enable row level security;

create policy "Allow public read access"
  on news for select
  using (true);

-- 仅允许 Service Role (后端爬虫) 写入
create policy "Allow service role insert"
  on news for insert
  with check (true);
