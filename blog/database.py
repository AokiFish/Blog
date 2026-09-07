"""数据库层：fastlite(SQLite) 连接与表结构定义。

表：posts / categories / tags / post_tags
时间统一存 ISO 字符串（UTC+8 本地时间，格式 YYYY-MM-DD HH:MM:SS），
归档按月取 published_at 前 7 位即可，避免时区换算问题。
"""
import os

from fastlite import database

from blog.config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

db = database(DB_PATH)
db.execute("PRAGMA journal_mode=WAL")
db.execute("PRAGMA foreign_keys=ON")

# ---------------------------------------------------------------- posts ----
posts = db.t.posts
if posts not in db.t:
    posts.create(
        id=int,
        slug=str,               # URL 片段，唯一
        title=str,
        summary=str,            # 摘要（列表页展示）
        content_md=str,         # Markdown 原文
        content_html=str,       # 渲染后的 HTML
        toc=str,                # 目录 JSON（[{level,text,id}]）
        category=str,           # 分类 slug（冗余字段，便于列表页直接取）
        status=str,             # published / draft
        pinned=bool,            # 置顶
        cover=str,              # 封面图 URL，可空
        views=int,
        words=int,              # 正文字数
        minutes=int,            # 预计阅读时长
        created_at=str,
        published_at=str,       # YYYY-MM-DD HH:MM:SS
        updated_at=str,
        source=str,             # 来源 Markdown 文件名
        pk="id",
    )
    posts.create_index(["slug"], index_name="idx_posts_slug", unique=True, if_not_exists=True)
    posts.create_index(["status", "published_at"], index_name="idx_posts_pub", if_not_exists=True)
    posts.create_index(["category"], index_name="idx_posts_cat", if_not_exists=True)

# ----------------------------------------------------------- categories ----
categories = db.t.categories
if categories not in db.t:
    categories.create(
        id=int,
        name=str,
        slug=str,
        description=str,
        sort=int,
        pk="id",
    )
    categories.create_index(["slug"], index_name="idx_cat_slug", unique=True, if_not_exists=True)

# ----------------------------------------------------------------- tags ----
tags = db.t.tags
if tags not in db.t:
    tags.create(id=int, name=str, slug=str, pk="id")
    tags.create_index(["slug"], index_name="idx_tag_slug", unique=True, if_not_exists=True)

# ------------------------------------------------------------ post_tags ----
post_tags = db.t.post_tags
if post_tags not in db.t:
    post_tags.create(id=int, post_id=int, tag_id=int, pk="id")
    post_tags.create_index(["post_id"], index_name="idx_pt_post", if_not_exists=True)
    post_tags.create_index(["tag_id"], index_name="idx_pt_tag", if_not_exists=True)
    post_tags.create_index(["post_id", "tag_id"], index_name="idx_pt_key", unique=True, if_not_exists=True)


def reset() -> None:
    """清空全部内容表（导入器全量重建时使用）。"""
    for t in (post_tags, tags, categories, posts):
        try:
            t.drop()
        except Exception:  # noqa: BLE001
            db.execute(f"DELETE FROM {t.name}" if hasattr(t, "name") else "")
