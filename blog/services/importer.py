"""Markdown 文章导入器：content/posts/*.md -> posts 表（按 slug 幂等）。

front-matter 字段：
    title / date / category / tags / summary / pinned / cover / status / slug
日期缺省时取文件 mtime；摘要缺省时取正文前 120 字。
"""
import os
from datetime import datetime

from blog.config import CONTENT_DIR, POSTS_DIR
from blog.core import (
    format_date,
    md_to_text,
    reading_minutes,
    slugify,
    truncate,
)
from blog.core.frontmatter import parse
from blog.core.markdown_engine import render_markdown
from blog.database import categories
from posts.repos import save_post
from categories.repos import ensure_category

DEFAULT_CATEGORY = "未分类"


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _published_at(meta: dict, path: str) -> str:
    raw = meta.get("date") or meta.get("published_at") or ""
    if raw:
        raw = raw.replace("T", " ").strip()
        if len(raw) == 10:
            raw += " 09:00:00"
        return format_date(raw, "%Y-%m-%d %H:%M:%S") or raw
    return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")


def import_file(path: str) -> dict | None:
    """导入单篇，返回落库后的文章 dict；草稿跳过。"""
    meta, body = parse(_read(path))
    if not meta.get("title"):
        # 无标题时退化为取正文首个 # 标题
        for line in body.splitlines():
            if line.startswith("# "):
                meta["title"] = line[2:].strip()
                break
    title = meta.get("title") or os.path.splitext(os.path.basename(path))[0]
    html, toc = render_markdown(body)
    words, minutes = reading_minutes(body)

    cat_name = (meta.get("category") or DEFAULT_CATEGORY).strip()
    cat_slug = slugify(cat_name, "misc")
    ensure_category(cat_name, cat_slug)

    published_at = _published_at(meta, path)
    return save_post(
        {
            "slug": meta.get("slug") or slugify(title),
            "title": title,
            "summary": meta.get("summary") or truncate(md_to_text(body), 120),
            "content_md": body,
            "content_html": html,
            "toc": toc,
            "category": cat_slug,
            "category_name": cat_name,
            "status": (meta.get("status") or "published").lower(),
            "pinned": bool(meta.get("pinned", False)),
            "cover": meta.get("cover", ""),
            "words": words,
            "minutes": minutes,
            "published_at": published_at,
            "updated_at": published_at,
            "created_at": published_at,
            "source": os.path.basename(path),
            "tag_names": meta.get("tags") or [],
        }
    )


def import_all(clean: bool = False) -> int:
    """全量导入 content/posts/ 下的 .md 文件，返回篇数。"""
    if clean:
        from posts.repos import delete_all

        delete_all()
    if not os.path.isdir(POSTS_DIR):
        return 0
    n = 0
    for name in sorted(os.listdir(POSTS_DIR)):
        if not name.lower().endswith(".md"):
            continue
        try:
            import_file(os.path.join(POSTS_DIR, name))
            n += 1
        except Exception as e:  # noqa: BLE001
            print(f"[import] {name} 失败: {e!r}")
    return n


def load_about() -> tuple[str, str]:
    """读取 content/about.md -> (正文 HTML, 目录)。"""
    path = os.path.join(CONTENT_DIR, "about.md")
    if not os.path.isfile(path):
        return "<p>还没有填写关于页面，在 content/about.md 里写点什么吧。</p>", "[]"
    _, body = parse(_read(path))
    html, toc = render_markdown(body)
    return html, toc
