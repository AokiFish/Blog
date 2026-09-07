"""Markdown 渲染引擎：正文 HTML + 目录(TOC) + 代码高亮。

- python-markdown 负责解析，pymdown-extensions 提供增强语法（提示块/任务列表/折叠块）
- Pygments 负责代码高亮，配色由 static/css/code.css 提供（亮/暗双份）
- 中文标题需要自定义 slugify，否则默认实现会把中文吞掉导致锚点为空
"""
import re

import markdown

TAG_STRIP = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<\s*(script|iframe|object|embed)[^>]*>.*?<\s*/\s*1\s*>", re.I | re.S)
ON_ATTR_RE = re.compile(r"\son[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
JS_HREF_RE = re.compile(r"(href|src)\s*=\s*(\"|')\s*javascript:[^\"']*\2", re.I)


def _slugify(value: str, separator: str = "-", unicode: bool = False) -> str:
    """保留中文与数字的 slugify（markdown 默认实现会把中文全部过滤）。"""
    value = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s]+", separator, value.strip().lower())
    value = value.strip(separator)
    return value or "section"


EXTENSIONS = [
    "extra",            # 表格 / 脚注 / 定义列表 / attr_list / md_in_html
    "admonition",       # !!! note 提示块
    "sane_lists",
    "pymdownx.details",     # 折叠块（配合 admonition）
    "pymdownx.tasklist",    # - [x] 任务列表
    "pymdownx.superfences", # 代码围栏（支持 ```python 高亮）
    "pymdownx.highlight",
    "pymdownx.tilde",       # ~~~ 删除线
    "toc",
]

EXTENSION_CONFIGS = {
    "toc": {
        "slugify": _slugify,
        "permalink": True,
        "permalink_class": "anchor",
        "permalink_title": "链接到此标题",
        "toc_depth": "2-3",
    },
    "pymdownx.superfences": {
        "custom_fences": [
            {"name": "mermaid", "class": "mermaid", "format": lambda s, l, **k: f'<pre class="mermaid">{s}</pre>'},
        ]
    },
    "pymdownx.highlight": {
        "use_pygments": True,
        "guess_lang": False,
        "linenums": False,
        "css_class": "highlight",
        "pygments_style": "github-dark",
    },
    "pymdownx.tasklist": {"custom_checkbox": True},
}


def _sanitize(html: str) -> str:
    """去掉危险标签与事件属性（正文来自本地 md / 受 token 保护的管理接口）。"""
    html = SCRIPT_RE.sub("", html)
    html = ON_ATTR_RE.sub("", html)
    html = JS_HREF_RE.sub("", html)
    return html


def _flatten(tokens: list) -> list[dict]:
    """markdown 的 toc_tokens 是嵌套结构，摊平成 [{level, text, id}]。"""
    out = []
    for t in tokens or []:
        out.append({"level": int(t.get("level", 0)), "text": t.get("name", ""), "id": t.get("id", "")})
        out.extend(_flatten(t.get("children") or []))
    return out


def render_markdown(text: str) -> tuple[str, list[dict]]:
    """返回 (正文 HTML, 目录列表)。"""
    md = markdown.Markdown(extensions=EXTENSIONS, extension_configs=EXTENSION_CONFIGS)
    html = md.convert(text or "")
    return _sanitize(html), _flatten(getattr(md, "toc_tokens", []) or [])


def md_to_text(md_text: str, limit: int = 0) -> str:
    """Markdown -> 纯文本（用于自动摘要与搜索索引）。"""
    md = markdown.Markdown(extensions=["extra"])
    html = md.convert(md_text or "")
    text = TAG_STRIP.sub(" ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] if limit and len(text) > limit else text
