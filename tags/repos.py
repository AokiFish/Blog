"""标签仓库（tags 模块）。"""
from blog.database import db, post_tags, tags
from blog.core.textutil import slugify

PUBLISHED = "published"


def ensure_tags(names: list[str]) -> list[dict]:
    """批量创建标签，返回 [{id, name, slug}]。"""
    out = []
    for raw in names or []:
        name = (raw or "").strip()
        if not name:
            continue
        slug = slugify(name, "tag")
        row = db.execute("SELECT id FROM tags WHERE slug = ?", [slug]).fetchone()
        if not row:
            tags.insert(name=name, slug=slug)
            row = db.execute("SELECT id FROM tags WHERE slug = ?", [slug]).fetchone()
        out.append({"id": row[0], "name": name, "slug": slug})
    return out


def set_post_tags(post_id: int, tag_rows: list[dict]) -> None:
    db.execute("DELETE FROM post_tags WHERE post_id = ?", [post_id])
    for t in tag_rows:
        db.execute(
            "INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)",
            [post_id, t["id"]],
        )


def tags_of_post(post_id: int) -> list[dict]:
    rows = db.execute(
        "SELECT t.name, t.slug FROM tags t JOIN post_tags pt ON pt.tag_id = t.id "
        "WHERE pt.post_id = ? ORDER BY t.name",
        [post_id],
    ).fetchall()
    return [{"name": r[0], "slug": r[1]} for r in rows]


def tags_with_count() -> list[dict]:
    """标签云：按文章数倒序，用于侧边栏与标签页。"""
    rows = db.execute(
        "SELECT t.name, t.slug, COUNT(p.id) AS n "
        "FROM tags t "
        "JOIN post_tags pt ON pt.tag_id = t.id "
        "JOIN posts p ON p.id = pt.post_id AND p.status = ? "
        "GROUP BY t.id ORDER BY n DESC, t.name ASC",
        [PUBLISHED],
    ).fetchall()
    return [{"name": r[0], "slug": r[1], "count": int(r[2] or 0)} for r in rows]
