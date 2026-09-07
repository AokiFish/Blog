---
slug: cloudflare-pages
title: 把动态站点搬到 Cloudflare Pages：静态导出的六个坑
date: 2026-05-20 14:05:00
category: Web
tags: [Cloudflare, 部署, Web]
summary: Pages 只吃静态文件，而我的博客是 Python 渲染的。这篇记录我怎样用「本地渲染 + 全量导出」把两者接起来，以及踩过的坑。
cover: /static/img/cover-pages.svg
---

Cloudflare Pages 不能直接跑 Python。这是选择它之前必须接受的前提——它托管的是文件，不是进程。

好消息是：个人博客天生适合静态化。内容一天更新不了几次，读者看到的页面对所有人都是一样的。

## 方案：构建期渲染，而不是运行期

思路很朴素——在本地把所有页面渲染成 HTML 文件，然后整目录上传：

```python
# scripts/build_static.py 的核心
for post in all_posts():
    html = render(f"/posts/{post['slug']}")
    write(f"dist/posts/{post['slug']}/index.html", html)
```

这样 Pages 上跑的就是纯粹的静态文件，全球 CDN 分发，没有冷启动，也不存在数据库被公网访问的风险。

## 坑一：URL 末尾的斜杠

Pages 对 `/posts/hello` 和 `/posts/hello/` 的处理不一样。最省事的做法是**每个页面都写成目录 + index.html**：

- `/posts/hello/` → `dist/posts/hello/index.html`
- `/tags/Python/` → `dist/tags/Python/index.html`

链接一律带尾斜杠，就不会出现相对路径解析错位。

## 坑二：静态资源的缓存

HTML 必须不缓存（否则改了文章读者看不到），而带 hash 的 CSS/JS 可以缓存一年。Pages 支持 `_headers` 文件：

```
/*.html
  Cache-Control: no-cache

/static/*
  Cache-Control: public, max-age=31536000, immutable
```

## 坑三：中文路径

`/tags/Python/` 没问题，但 `/tags/深度学习/` 在导出时需要先百分号编码，否则落到文件系统上会出现编码错误：

```python
from urllib.parse import quote
path = quote(slug, safe="/")
```

## 坑四：分页页面容易漏

列表页有第 2 页、第 3 页，导出脚本如果只遍历文章，会漏掉 `/page/2/`。我的做法是让每个列表路由都暴露一个「总页数」函数，导出时按页数循环。

## 坑五：表单与动态功能会失效

阅读量统计、评论、搜索——这些都是动态的。处理方式有三种：

| 功能 | 静态化方案 |
| --- | --- |
| 搜索 | 生成 search-index.json，前端 JS 过滤 |
| 阅读量 | 接第三方计数（如不蒜子），或干脆不要 |
| 评论 | Giscus / Waline 等托管服务 |

!!! note "我的选择"
    搜索保留（离线索引，几十 KB 而已），阅读量去掉，评论用 Giscus 挂在 GitHub Discussions 上。

## 坑六：构建时间和数据库

导出的那一刻需要有数据库，但 Pages 的构建环境里没有。两个解法：

1. **把 SQLite 文件一起提交到仓库**（几百 KB，完全可以接受）
2. 构建时从 content/*.md 现场导入

我选了后者：仓库里只有 Markdown，构建脚本先导入再渲染，数据库不进版本控制，避免二进制冲突。

## 部署只需三步

```bash
python scripts/build_static.py     # 1. 渲染到 dist/
npx wrangler pages deploy dist     # 2. 上传
# 3. 在 Dashboard 里绑定自定义域 blog.example.com
```

第一次部署之后，Pages 会给你一个 `*.pages.dev` 的域名。绑定自定义域时它会提示添加 CNAME，照做即可，证书自动签发。

整个流程不到两分钟，而且没有任何运行时成本——这对一个可能半年才更新一次的个人站来说，比养一台服务器合理得多。
