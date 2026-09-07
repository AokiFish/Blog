---
title: FastHTML 表单与文件上传
slug: fasthtml-form-upload
category: web
tags: [fasthtml, python, form, upload]
date: 2026-08-30
pinned: 0
summary: 用 python-fasthtml 处理表单提交、文件上传与 CSRF 保护，记录常见坑。
---

# FastHTML 表单与文件上传

## 普通表单

```python
@rt('/submit')
def post(name: str, email: str):
    return f"hello {name}, mail={email}"
```

`fast_app` 会自动把同名字段绑定到函数参数。

## 文件上传

```python
@rt('/upload', methods=['POST'])
async def upload(file: UploadFile):
    data = await file.read()
    return P(f"got {len(data)} bytes")
```

注意：上传是 `async`，`UploadFile` 来自 starlette。

## CSRF

FastHTML 在 `SecretKeyMiddleware` 启用时自动加 `_csrf` 字段到表单。
