"""归档仓库（archive 模块）：按月聚合文章数。"""
from blog.database import db

PUBLISHED = "published"


def archive_months() -> list[dict]:
    """按月聚合：[{ym, label, count}]，倒序。"""
    cur = db.execute(
        "SELECT substr(published_at, 1, 7) AS ym, COUNT(*) AS n FROM posts "
        f"WHERE status = ? GROUP BY ym ORDER BY ym DESC",
        [PUBLISHED],
    )
    return [{"ym": r[0], "count": int(r[1])} for r in cur.fetchall() if r[0]]
