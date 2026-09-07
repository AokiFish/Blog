---
slug: markdown-render
title: 给 Markdown 加上目录、代码高亮和提示块
date: 2026-06-11 10:20:00
category: Python
tags: [Python, Markdown, 前端]
summary: python-markdown 的默认配置在中文场景下有个隐蔽的坑——标题锚点会变成空字符串。这篇记下我最终使用的扩展组合。
---

用 python-markdown 渲染博客正文，最小实现只要三行：

```python
import markdown
html = markdown.markdown(text, extensions=["extra", "toc"])
```

但要把体验做到能看，还得处理三件事：目录、代码高亮、中文锚点。

## 坑：中文标题的锚点是空的

`toc` 扩展默认使用 `markdown.extensions.toc.slugify`，它内部做了 `NFKD` 归一化后强制转 ASCII：

```python
value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
```

也就是说 `## 开始之前` 会被处理成空字符串，页面上所有中文标题的锚点都变成 `#section` 或者直接失效，目录点击全部跳到顶部。

解决办法是传一个自己的 slugify：

```python
import re

def slugify(value, separator="-", unicode=False):
    value = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s]+", separator, value.strip().lower())
    return value.strip(separator) or "section"

markdown.Markdown(
    extensions=["extra", "toc"],
    extension_configs={"toc": {"slugify": slugify, "permalink": True}},
)
```

!!! warning "permalink 的样式"
    开启 `permalink: True` 后，每个标题后面会插入一个 `¶` 锚点链接。记得给 `.anchor` 设置 `opacity: 0`，hover 时再显示，否则正文会显得很吵。

## 目录数据从哪来

很多人不知道 `toc` 扩展除了生成 `md.toc`（一段 HTML）之外，还会在实例上挂一个 `toc_tokens`，是结构化的 Python 对象：

```python
md = markdown.Markdown(extensions=["toc"])
html = md.convert(text)
tokens = md.toc_tokens   # [{'level':2,'id':'xx','name':'xx','children':[...]}]
```

它是嵌套的，渲染成侧边栏目录之前需要摊平一层：

```python
def flatten(tokens):
    out = []
    for t in tokens:
        out.append({"level": t["level"], "text": t["name"], "id": t["id"]})
        out.extend(flatten(t.get("children") or []))
    return out
```

存成 JSON 跟着文章一起入库，详情页就不必每次重新解析一遍 Markdown。

## 代码高亮：Pygments 还是前端高亮

我一开始用的是 highlight.js，后来换成了服务端 Pygments，理由有三个：

1. **没有 FOUC**。页面加载完就是高亮好的，不会先闪一下白代码块。
2. **JS 体积归零**。博客的 JS 只有几百行交互逻辑，首屏更快。
3. **配色可控**。用 `HtmlFormatter().get_style_defs()` 直接导出 CSS。

配置方式：

```python
EXTENSION_CONFIGS = {
    "pymdownx.superfences": {},
    "pymdownx.highlight": {
        "use_pygments": True,
        "css_class": "highlight",
        "pygments_style": "github-dark",
    },
}
```

不过有个细节：Pygments 的样式是写死在 CSS 里的，一旦生成就是固定配色，没法跟着明暗主题切换。我的做法是生成两份，分别包在 `:root` 和 `[data-theme="dark"]` 里——这点 CSS 体积完全可以接受。

## 最终的扩展组合

```python
EXTENSIONS = [
    "extra",              # 表格 / 脚注 / 定义列表
    "admonition",         # !!! note 提示块
    "sane_lists",
    "pymdownx.details",   # 可折叠块
    "pymdownx.tasklist",  # - [x]
    "pymdownx.superfences",
    "pymdownx.highlight",
    "toc",
]
```

这套组合覆盖了写技术文章 99% 的需求，剩下的 1%（比如数学公式、流程图）我倾向于用图片代替——博客的复杂度应该控制住，否则最后维护的是博客本身，而不是内容。
