# Blog

基于 **FastHTML** 的个人技术博客，支持本地开发、静态构建与 Cloudflare Pages 部署。

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | [FastHTML](https://github.com/AnswerDotAI/fasthtml) |
| 数据库 | SQLite（FastLite） |
| 内容格式 | Markdown + YAML Frontmatter |
| 部署 | Cloudflare Pages（静态导出） |

## 功能特性

- 文章管理：Markdown 文件驱动，自动解析 Frontmatter
- 分类 / 标签：自动生成，支持分页
- 归档：按年月组织
- 搜索：客户端全文搜索（`search-index.json`）
- RSS：`/feed.xml`
- Sitemap：`/sitemap.xml`
- 代码高亮：Pygments + CSS 自动生成
- 响应式主题：深色/浅色模式切换
- 静态导出：一键生成完整静态站点

## 快速开始

### 环境要求

- Python 3.11+
- pip / uv

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 按需修改 .env 中的站点信息、数据库路径等
```

### 本地运行

```bash
python main.py
# 或
uvicorn app:app --reload
```

访问 http://127.0.0.1:5000

### Windows 一键重启（开发用）

双击 `restart-dev.bat`，自动清理端口占用并重启服务。

## 内容管理

文章存放在 `content/posts/` 目录下，每个 `.md` 文件包含 YAML Frontmatter：

```markdown
---
title: 文章标题
date: 2026-01-01
categories:
  - Python
tags:
  - 教程
slug: article-slug
---

正文内容...
```

新增文章后重启服务即可自动导入。

## 静态构建 & 部署

### 本地构建

```bash
python scripts/build_static.py
```

输出到 `build/` 目录，包含所有页面、静态资源和 `_headers` 文件。

### Cloudflare Pages 部署

**方式一：Git 自动部署（推荐）**

1. 将本项目连接到 Cloudflare Pages
2. 构建配置：
   - 构建命令：`pip install -r requirements.txt && python scripts/gen_code_css.py && python scripts/build_static.py`
   - 输出目录：`build`
3. 推送代码后自动触发构建和部署

**方式二：手动部署**

```bash
python scripts/build_static.py
npx wrangler pages deploy build
```

## 项目结构

```
Blog/
├── blog/              # 应用核心包
│   ├── config.py      # 站点配置（读取 .env）
│   ├── database.py    # 数据库初始化
│   └── services/      # 业务服务（导入器等）
├── content/           # Markdown 文章源
│   └── posts/
├── web/               # 页面路由模块
│   ├── home.py        # 首页
│   ├── post.py        # 文章详情
│   ├── tags.py        # 标签页
│   ├── categories.py  # 分类页
│   ├── archive.py     # 归档页
│   └── search.py      # 搜索页
├── scripts/
│   ├── build_static.py  # 静态构建脚本
│   └── gen_code_css.py  # 代码高亮 CSS 生成
├── static/            # 静态资源（CSS、JS、图片）
├── build/             # 构建产物（gitignore 排除）
├── data/              # SQLite 数据库（gitignore 排除）
├── app.py             # uvicorn 兼容入口
├── main.py            # 本地开发入口
├── requirements.txt
├── wrangler.toml      # Cloudflare Pages 配置
└── .env.example       # 环境变量示例
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SITE_NAME` | 技术笔记 | 站点名称 |
| `SITE_URL` | https://blog.272314369.xyz | 站点 URL |
| `AUTHOR` | 博主 | 作者名 |
| `DB_PATH` | data/blog.db | 数据库路径 |
| `SECRET_KEY` | dev-secret | 会话密钥 |
| `ADMIN_TOKEN` | dev-token | 管理员 Token |
| `HOST` | 127.0.0.1 | 监听地址 |
| `PORT` | 5000 | 监听端口 |
| `PAGE_SIZE` | 10 | 每页文章数 |

## License

MIT
