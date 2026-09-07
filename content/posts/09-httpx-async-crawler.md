---
title: 用 httpx 异步重写一个网络爬虫
slug: httpx-async-crawler
category: python
tags: [python, asyncio, httpx, crawler]
date: 2026-08-22
pinned: 0
summary: 分享把同步 requests + BeautifulSoup 爬虫改写为 httpx + asyncio 后，速度提升 8 倍的过程与坑。
---

# 用 httpx 异步重写一个网络爬虫

## 背景

早期爬虫用 `requests` + `ThreadPoolExecutor`，并发开到 32 时仍受限于 GIL 与 socket 复用。

## 改写

`httpx.AsyncClient` + `asyncio.gather`：

```python
async with httpx.AsyncClient(timeout=10) as c:
    tasks = [c.get(url) for url in urls]
    pages = await asyncio.gather(*tasks)
```

## 坑

- `Client` 不要每次新建，复用同一个以保持 keep-alive；
- 单页异常用 `return_exceptions=True`，避免整批失败；
- QPS 太大时记得用 `aiometer` 加并发上限。
