---
slug: asyncio-crawler
title: 用 asyncio 重构爬虫：6 倍提速背后的三个细节
date: 2026-03-08 09:15:00
category: Python
tags: [Python, 异步, 爬虫]
summary: 同样的 2000 个 URL，同步版跑了 11 分钟，异步版 1 分 50 秒。但提速的关键不是换成 aiohttp，而是限流和超时策略。
---

重构之前，我的爬虫长这样：

```python
for url in urls:
    resp = requests.get(url, timeout=10)
    save(parse(resp.text))
```

2000 个 URL，耗时 11 分 23 秒。换成 asyncio 之后是 1 分 50 秒。但如果你以为把 `requests` 换成 `aiohttp` 就能自动获得这个提升，那多半会失望——我第一版异步代码跑了 9 分钟，几乎没变快。

## 细节一：并发数不是越大越好

第一版我写了个无限并发：

```python
async def fetch_all(urls):
    async with aiohttp.ClientSession() as s:
        return await asyncio.gather(*[fetch(s, u) for u in urls])
```

2000 个协程同时开，结果是被目标站点限流，大量请求重试，还有一堆连接超时。加上信号量之后立刻正常：

```python
sem = asyncio.Semaphore(20)   # 同时最多 20 个

async def fetch(session, url):
    async with sem:
        async with session.get(url) as r:
            return await r.text()
```

!!! note "并发数怎么定"
    经验公式：`并发数 ≈ 目标站点的响应时间(秒) × 你想要的 QPS`。响应时间 0.2 秒、想跑 100 QPS，并发就是 20。比这再高，收益递减而封禁风险上升。

## 细节二：超时要分层设置

`aiohttp` 的默认超时是 5 分钟——对爬虫来说等于没有。而且单一 timeout 值没法区分「连不上」和「连上了但一直不发数据」：

```python
timeout = aiohttp.ClientTimeout(
    total=30,        # 整个请求最长 30 秒
    connect=5,       # 建连 5 秒
    sock_read=10,    # 连接建立后，10 秒没数据就放弃
)
session = aiohttp.ClientSession(timeout=timeout)
```

`sock_read` 是最容易被忽略的一项。没有它，遇到一个慢速响应的死连接，你的协程能挂好几分钟。

## 细节三：失败要退避重试，但不能无脑重试

```python
async def fetch_with_retry(session, url, retries=3):
    for i in range(retries):
        try:
            return await fetch(session, url)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            if i == retries - 1:
                return None
            await asyncio.sleep(2 ** i + random.random())   # 指数退避 + 抖动
```

两个要点：

- **指数退避**：1s、2s、4s，给对方喘息时间
- **抖动**：`+ random.random()` 防止多个协程同时重试，形成新的洪峰

## 完整的骨架

```python
import asyncio, aiohttp, random

async def worker(session, queue, results):
    while True:
        url = await queue.get()
        try:
            html = await fetch_with_retry(session, url)
            if html:
                results.append(parse(html))
        finally:
            queue.task_done()

async def main(urls):
    queue = asyncio.Queue()
    for u in urls:
        queue.put_nowait(u)
    results = []
    async with aiohttp.ClientSession(timeout=timeout) as s:
        workers = [asyncio.create_task(worker(s, queue, results)) for _ in range(20)]
        await queue.join()
        for w in workers:
            w.cancel()
    return results
```

用队列而不是 `gather` 的好处是：**任务进度可见，中途可以持久化，崩了不用从头再来**。

## 什么时候别上 asyncio

最后泼一盆冷水。下面这些场景，同步代码反而更合适：

| 场景 | 原因 |
| --- | --- |
| 只有几十个请求 | 复杂度不划算 |
| 重度 CPU 计算 | asyncio 解决不了 GIL，用多进程 |
| 依赖的库不支持异步 | 一个阻塞调用拖垮整个事件循环 |
| 需要精细控制请求顺序 | 调试成本会让你怀疑人生 |

异步的本质是**在等待 IO 的时候去干别的事**。如果你的瓶颈根本不在 IO 等待上，换 async 只会让代码更难读。
