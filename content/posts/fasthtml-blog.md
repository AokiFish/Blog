---
title: 用 FastHTML 写博客：把 HTML 重新变回 Python 函数
slug: fasthtml-blog
date: 2026-09-02 09:30:00
category: Python
tags: [FastHTML, Python, Web]
summary: 试了一圈模板引擎之后，我发现最顺手的方案是不要模板——直接把标签写成 Python 函数，配合 Starlette 的路由，一个博客的骨架半天就能跑起来。
status: published
pinned: true
cover: /static/img/cover-fasthtml.svg
---

做个人博客这件事，我反复重写过四次。第一次用 Django，第二次是 Hugo，第三次 Next.js，这一次停在 FastHTML 上。不是因为它最流行，恰恰相反——它足够小，小到我能把整个框架的行为在脑子里跑一遍。

## 为什么放弃模板引擎

模板引擎的问题不在于它慢，而在于它引入了两套语言：一套写逻辑，一套写结构。你永远要在「这个值到底在哪一层被转义了」这件事上花时间。

FastHTML 的思路很直接：**HTML 标签就是函数**。

```python
from fasthtml.common import Div, H1, A, P

def card(post):
    return Div(
        H1(A(post["title"], href=f"/posts/{post['slug']}")),
        P(post["summary"], cls="muted"),
        cls="card",
    )
```

这段代码返回的就是一个可以序列化成 HTML 字符串的对象。没有模板目录，没有 `{% for %}`，循环用列表推导式解决：

```python
Div([card(p) for p in posts], cls="post-list")
```

## 路由：APIRouter 让子模块各自为政

路由装饰器看上去和 FastAPI 几乎一样：

```python
from fasthtml.common import APIRouter

router = APIRouter()

@router("/posts/{slug}")
def detail(slug: str):
    post = get_post(slug)
    if not post:
        return RedirectResponse("/")
    return post_detail(post)
```

关键区别在于返回值：FastAPI 返回 JSON，FastHTML 返回**节点树**，框架帮你渲染成完整的 HTML 文档。所以每篇博客文章、每个侧边栏组件，都可以按页面拆成一个独立的 package，`app.py` 只负责把它们挂上去。

## 一点点代价

当然不是全无代价：

| 场景 | 模板引擎 | FastHTML |
| --- | --- | --- |
| 前端同学改样式 | 直接改 HTML | 需要找对应 Python 函数 |
| 复杂条件渲染 | `{% if %}` 很直观 | 三元表达式会变长 |
| 缓存片段 | 生态成熟 | 得自己写 |
| 类型提示 | 基本没有 | 编辑器补全还不错 |

如果你的团队里有专职前端，模板引擎依然是更稳妥的选择。但如果是个人项目、内部工具，或者你本来就享受「用一种语言写完整个应用」的感觉，FastHTML 的体验是相当轻快的。

!!! note "关于性能"
    每次请求都重新构建节点树听起来很浪费，但实测下来渲染一棵几百个节点的树只占零点几毫秒，真正的瓶颈永远在数据库查询上。

## 我最后的项目结构

```
app.py           # 只做全局设置：hdrs、静态目录、挂载子路由
routes/          # 每个页面一个模块，各自持有 APIRouter
ui/              # 布局与可复用组件
repos/           # 数据访问
core/            # Markdown 渲染、分页、文本工具
```

这个结构最大的好处是：**我知道每一段 HTML 是从哪个函数里出来的**。对一个要长期维护的个人项目来说，这种确定性比任何花哨的特性都值钱。
