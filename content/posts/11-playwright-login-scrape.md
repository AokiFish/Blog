---
title: 用 Playwright 抓取需要登录的页面
slug: playwright-login-scrape
category: python
tags: [python, playwright, scraper, automation]
date: 2026-09-01
pinned: 0
summary: 遇到「需要登录才能看到的列表页」怎么办？用 Playwright 持久化 storage_state 后重复使用最稳。
---

# 用 Playwright 抓取需要登录的页面

## 一次性登录保存状态

```python
async with async_playwright() as p:
    browser = await p.chromium.launch()
    ctx = await browser.new_context()
    page = await ctx.new_page()
    await page.goto('https://example.com/login')
    await page.fill('input[name=u]', 'me')
    await page.fill('input[name=p]', 'secret')
    await page.click('button[type=submit]')
    await ctx.storage_state(path='state.json')
```

## 之后每次直接复用

```python
ctx = await browser.new_context(storage_state='state.json')
page = await ctx.new_page()
await page.goto('https://example.com/dashboard')
```

登录一次，状态文件反复用；过期再重新登录。
