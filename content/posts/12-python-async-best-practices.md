---
slug: python-async-best-practices
title: Python 异步编程的五个常见陷阱，以及怎么避开它们
date: 2026-09-05 14:20:00
category: Python
tags: [Python, asyncio, 异步, 性能]
summary: 异步不是银弹。我用 asyncio 写过爬虫、写过服务，踩过不少坑。这篇记录五个最典型的错误，以及对应的修复思路。
cover: /static/img/cover-attention.svg
---

写异步代码最容易犯的错误，不是语法错了，而是**你以为你在写异步，其实还是在同步阻塞**。

## 陷阱一：在异步函数里调用同步阻塞代码

```python
import requests
import asyncio

async def fetch(url):
    # 这是同步的！会阻塞整个事件循环
    resp = requests.get(url)
    return resp.text

async def main():
    tasks = [fetch(f"https://example.com/{i}") for i in range(10)]
    results = await asyncio.gather(*tasks)
```

`requests` 是同步库，调用它会阻塞事件循环，其他协程全部卡住。正确做法是用 `httpx`：

```python
import httpx

async def fetch(url):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.text
```

## 陷阱二：忘记 await 协程

```python
async def get_data():
    return {"key": "value"}

async def main():
    # 这行不会报错，但 data 是一个协程对象，不是结果
    data = get_data()
    print(data)  # <coroutine object get_data at 0x...>
```

协程对象必须被 `await` 才会真正执行。忘记 `await` 是最隐蔽的 bug 之一——代码不报错，但逻辑完全不对。

## 陷阱三：在事件循环里跑 CPU 密集型任务

```python
async def heavy_computation():
    # 这会阻塞事件循环，其他协程全部等待
    result = sum(i * i for i in range(10_000_000))
    return result
```

异步适合 I/O 密集型，不适合计算密集型。CPU 密集型任务应该用 `loop.run_in_executor` 放到线程池或进程池：

```python
import concurrent.futures

async def heavy_computation():
    loop = asyncio.get_event_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, compute)
    return result

def compute():
    return sum(i * i for i in range(10_000_000))
```

## 陷阱四：嵌套循环里创建太多任务

```python
async def fetch_all(urls):
    # 1000 个 URL 同时发起，可能撑爆连接池或触发限流
    tasks = [fetch(url) for url in urls]
    return await asyncio.gather(*tasks)
```

正确做法是用信号量控制并发数：

```python
async def fetch_all(urls, limit=50):
    semaphore = asyncio.Semaphore(limit)
    
    async def bounded_fetch(url):
        async with semaphore:
            return await fetch(url)
    
    tasks = [bounded_fetch(url) for url in urls]
    return await asyncio.gather(*tasks)
```

## 陷阱五：异常处理不当

```python
async def main():
    tasks = [fetch(url) for url in urls]
    results = await asyncio.gather(*tasks)
    # 如果任何一个任务抛异常，整个 gather 会立即失败
```

用 `return_exceptions=True` 可以让所有任务都跑完，异常作为结果返回：

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
for r in results:
    if isinstance(r, Exception):
        print(f"任务失败: {r}")
    else:
        print(f"任务成功: {r}")
```

## 总结

| 陷阱 | 症状 | 修复 |
| --- | --- | --- |
| 同步阻塞调用 | 事件循环卡顿 | 用异步库替代 |
| 忘记 await | 拿到协程对象而非结果 | 加 `await` |
| CPU 密集型任务 | 阻塞其他协程 | 用 `run_in_executor` |
| 任务数量失控 | 资源耗尽或限流 | 用 `Semaphore` 限流 |
| 异常处理不当 | 一个失败全部失败 | `return_exceptions=True` |

异步编程的核心思维是：**不要阻塞事件循环**。任何可能等待的操作（网络、文件、数据库）都应该用异步版本；任何计算密集的操作都应该移出事件循环。
