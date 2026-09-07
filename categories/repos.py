"""分类仓库（categories 模块）。"""
from blog.database import db, categories
from blog.core.textutil import slugify

PUBLISHED = "published"


def ensure_category(name: str, slug: str = "", desc: str = "") -> str:
    """分类不存在则创建，返回 slug。"""
    slug = slug or slugify(name, "misc")
    if not db.execute("SELECT id FROM categories WHERE slug = ?", [slug]).fetchone():
        categories.insert(name=name, slug=slug, description=desc, sort=0)
    return slug


def category_name(slug: str) -> str:
    if not slug:
        return "未分类"
    row = db.execute("SELECT name FROM categories WHERE slug = ?", [slug]).fetchone()
    return row[0] if row else slug


def categories_with_count() -> list[dict]:
    rows = db.execute(
        "SELECT c.name, c.slug, c.description, COUNT(p.id) AS n "
        "FROM categories c LEFT JOIN posts p ON p.category = c.slug AND p.status = ? "
        "GROUP BY c.id ORDER BY n DESC, c.sort ASC, c.name ASC",
        [PUBLISHED],
    ).fetchall()
    return [{"name": r[0], "slug": r[1], "description": r[2], "count": int(r[3])} for r in rows]
