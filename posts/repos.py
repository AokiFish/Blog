"""文章仓库（posts 模块）：列表 / 详情 / 归档 / 搜索 / 读写。

所有对外返回的文章 dict 都会附加：
    post["tags"]         -> [{"name", "slug"}]
    post["category_name"] -> 分类名
"""
import json

from blog.database import db, post_tags, posts, tags
from categories.repos import category_name
from tags.repos import tags_of_post

PUBLISHED = "published"

_ORDER = "p.published_at DESC, p.pinned DESC, p.id DESC"

# 与建表顺序一致，避免依赖 cursor.description（apsw 在语句结束后取列名会抛错）
POST_COLS = (
    "id", "slug", "title", "summary", "content_md", "content_html", "toc",
    "category", "status", "pinned", "cover", "views", "words", "minutes",
    "created_at", "published_at", "updated_at", "source",
)


def attach_taxonomy(row: dict) -> dict:
    row["tags"] = tags_of_post(row["id"])
    row["category_name"] = category_name(row.get("category"))
    return row


# ---------------------------------------------------------------- 查询 ----
def _rows(sql: str, params: list) -> list[dict]:
    out = []
    for r in db.execute(sql, params).fetchall():
        row = dict(zip(POST_COLS, r))
        row["tags"] = tags_of_post(row["id"])
        row["category_name"] = category_name(row.get("category"))
        out.append(row)
    return out


def _count(sql: str, params: list) -> int:
    row = db.execute(sql, params).fetchone()
    return int(row[0]) if row else 0


def count_posts(category: str = "", tag: str = "", ym: str = "", q: str = "") -> int:
    where, params = _filters(category, tag, ym, q)
    return _count(f"SELECT COUNT(*) FROM posts p {where}", params)


def _filters(category: str = "", tag: str = "", ym: str = "", q: str = "") -> tuple[str, list]:
    conds = [f"p.status = '{PUBLISHED}'"]
    params: list = []
    if category:
        conds.append("p.category = ?")
        params.append(category)
    if tag:
        conds.append(
            "EXISTS (SELECT 1 FROM post_tags pt JOIN tags t ON t.id = pt.tag_id "
            "WHERE pt.post_id = p.id AND t.slug = ?)"
        )
        params.append(tag)
    if ym:
        conds.append("substr(p.published_at, 1, 7) = ?")
        params.append(ym)
    if q:
        like = f"%{q}%"
        conds.append("(p.title LIKE ? OR p.summary LIKE ? OR p.content_md LIKE ?)")
        params.extend([like, like, like])
    return ("WHERE " + " AND ".join(conds)) if conds else "", params


def list_posts(
    page: int = 1,
    size: int = 10,
    category: str = "",
    tag: str = "",
    ym: str = "",
    q: str = "",
) -> list[dict]:
    where, params = _filters(category, tag, ym, q)
    sql = f"SELECT p.* FROM posts p {where} ORDER BY {_ORDER} LIMIT ? OFFSET ?"
    return _rows(sql, params + [size, max(0, (page - 1) * size)])


def all_posts(limit: int = 1000) -> list[dict]:
    """静态导出 / RSS 用：取全部已发布文章。"""
    return _rows(
        f"SELECT p.* FROM posts p WHERE p.status = ? ORDER BY {_ORDER} LIMIT ?",
        [PUBLISHED, limit],
    )


def get_post(slug: str) -> dict | None:
    rows = _rows("SELECT p.* FROM posts p WHERE p.slug = ? LIMIT 1", [slug])
    return rows[0] if rows else None


def all_rows(limit: int = 1000, offset: int = 0) -> list[dict]:
    """管理后台用：取全部文章（含草稿），按更新时间倒序；可传 offset 分页。"""
    return _rows(
        "SELECT p.* FROM posts p ORDER BY p.updated_at DESC, p.published_at DESC LIMIT ? OFFSET ?",
        [limit, offset],
    )


def count_all_rows() -> int:
    """管理后台用：全部文章（含草稿）总数。"""
    row = db.execute("SELECT COUNT(*) FROM posts").fetchone()
    return int(row[0]) if row else 0


def get_post_by_id(pid: int) -> dict | None:
    rows = _rows("SELECT p.* FROM posts p WHERE p.id = ? LIMIT 1", [pid])
    return rows[0] if rows else None


def recent_posts(limit: int = 6, exclude_slug: str = "") -> list[dict]:
    where = "WHERE p.status = ?"
    params: list = [PUBLISHED]
    if exclude_slug:
        where += " AND p.slug <> ?"
        params.append(exclude_slug)
    return _rows(
        f"SELECT p.* FROM posts p {where} ORDER BY p.published_at DESC LIMIT ?",
        params + [limit],
    )


def hot_posts(limit: int = 20) -> list[dict]:
    """热点文章：按阅读量倒序。"""
    return _rows(
        f"SELECT p.* FROM posts p WHERE p.status = ? ORDER BY p.views DESC LIMIT ?",
        [PUBLISHED, limit],
    )


def neighbors(post: dict) -> tuple[dict | None, dict | None]:
    prev = _rows(
        "SELECT p.* FROM posts p WHERE p.status = ? AND p.published_at < ? "
        "ORDER BY p.published_at DESC LIMIT 1",
        [PUBLISHED, post["published_at"]],
    )
    nxt = _rows(
        "SELECT p.* FROM posts p WHERE p.status = ? AND p.published_at > ? "
        "ORDER BY p.published_at ASC LIMIT 1",
        [PUBLISHED, post["published_at"]],
    )
    return (prev[0] if prev else None, nxt[0] if nxt else None)


def related_posts(post: dict, limit: int = 4) -> list[dict]:
    ids = [t["slug"] for t in post.get("tags", [])]
    sql = (
        "SELECT p.* FROM posts p WHERE p.status = ? AND p.id <> ? "
        "ORDER BY (p.category = ?) DESC, p.published_at DESC LIMIT ?"
    )
    rows = _rows(sql, [PUBLISHED, post["id"], post.get("category"), limit * 3])
    if ids:
        same_tag = [r for r in rows if set(t["slug"] for t in r["tags"]) & set(ids)]
        rest = [r for r in rows if r not in same_tag]
        rows = (same_tag + rest)[:limit]
    return rows[:limit]


def search_posts(q: str, page: int = 1, size: int = 10) -> list[dict]:
    return list_posts(page=page, size=size, q=q)


def add_views(slug: str) -> None:
    db.execute("UPDATE posts SET views = views + 1 WHERE slug = ?", [slug])


# ---------------------------------------------------------------- 写入 ----
def save_post(data: dict) -> dict:
    """按 slug 幂等写入（存在则更新）。返回落库后的文章 dict。"""
    row = db.execute("SELECT id FROM posts WHERE slug = ?", [data["slug"]]).fetchone()

    payload = {
        "slug": data["slug"],
        "title": data["title"],
        "summary": data.get("summary", ""),
        "content_md": data.get("content_md", ""),
        "content_html": data.get("content_html", ""),
        "toc": json.dumps(data.get("toc", []), ensure_ascii=False),
        "category": data.get("category", ""),
        "status": data.get("status", PUBLISHED),
        "pinned": bool(data.get("pinned", False)),
        "cover": data.get("cover", ""),
        "words": int(data.get("words", 0)),
        "minutes": int(data.get("minutes", 1)),
        "published_at": data.get("published_at", ""),
        "updated_at": data.get("updated_at", ""),
        "source": data.get("source", ""),
    }
    if row:
        sets = ", ".join(f"[{k}] = ?" for k in payload)
        db.execute(f"UPDATE posts SET {sets} WHERE id = ?", [*payload.values(), row[0]])
        pid = row[0]
    else:
        payload["views"] = int(data.get("views", 0))
        payload["created_at"] = data.get("created_at") or payload["published_at"]
        cols = ", ".join(f"[{c}]" for c in payload)
        marks = ", ".join("?" for _ in payload)
        db.execute(f"INSERT INTO posts ({cols}) VALUES ({marks})", list(payload.values()))
        pid = db.execute("SELECT id FROM posts WHERE slug = ?", [data["slug"]]).fetchone()[0]

    if data.get("tag_names"):
        from tags.repos import ensure_tags, set_post_tags

        set_post_tags(pid, ensure_tags(data["tag_names"]))
    if data.get("category_name"):
        from categories.repos import ensure_category

        ensure_category(data["category_name"], data.get("category", ""), data.get("category_desc", ""))

    return get_post(data["slug"])


def set_status(slug: str, status: str) -> bool:
    cur = db.execute("UPDATE posts SET status = ? WHERE slug = ?", [status, slug])
    return bool(cur)


def delete_post(slug: str) -> bool:
    post = get_post(slug)
    if not post:
        return False
    pid = post["id"]
    db.execute("DELETE FROM post_tags WHERE post_id = ?", [pid])
    db.execute("DELETE FROM posts WHERE id = ?", [pid])
    return True


def delete_all() -> None:
    db.execute("DELETE FROM post_tags")
    db.execute("DELETE FROM tags")
    db.execute("DELETE FROM categories")
    db.execute("DELETE FROM posts")
