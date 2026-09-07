"""一次性脚本：把旧 import 改写成新包结构。运行后删除即可。"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 全局前缀替换（对所有文件生效）
GLOBAL = [
    ("from config import", "from blog.config import"),
    ("from database import", "from blog.database import"),
    ("from core.", "from blog.core."),
    ("from core import", "from blog.core import"),
    ("from services.", "from blog.services."),
    ("from services import", "from blog.services import"),
    ("from ui.layout import", "from web.layout import"),
    ("from ui.widgets import", "from web.widgets import"),
    ("from ui import", "from web import"),
    ("from routes.post import", "from web.post import"),
    ("from routes import", "from web import"),
    ("from repos.posts import", "from posts.repos import"),
    ("from repos.taxonomy import ensure_category", "from categories.repos import ensure_category"),
    ("from app import app", "from blog import app"),
]

# 每个文件特有的 `from repos import ...` 拆分
SPECIFIC = {
    "web/home.py": [
        ("from repos import count_posts, list_posts",
         "from posts.repos import count_posts, list_posts"),
    ],
    "web/post.py": [
        ("from repos import add_views, get_post, neighbors, related_posts",
         "from posts.repos import add_views, get_post, neighbors, related_posts"),
    ],
    "web/archive.py": [
        ("from repos import archive_months, count_posts, list_posts",
         "from archive.repos import archive_months\nfrom posts.repos import count_posts, list_posts"),
    ],
    "web/tags.py": [
        ("from repos import count_posts, list_posts, tags_with_count",
         "from posts.repos import count_posts, list_posts\nfrom tags.repos import tags_with_count"),
    ],
    "web/categories.py": [
        ("from repos import categories_with_count, count_posts, list_posts",
         "from categories.repos import categories_with_count\nfrom posts.repos import count_posts, list_posts"),
    ],
    "web/search.py": [
        ("from repos import count_posts, list_posts",
         "from posts.repos import count_posts, list_posts"),
    ],
    "web/feed.py": [
        ("from repos import all_posts, archive_months, categories_with_count, tags_with_count",
         "from posts.repos import all_posts\nfrom archive.repos import archive_months\n"
         "from categories.repos import categories_with_count\nfrom tags.repos import tags_with_count"),
    ],
    "web/widgets.py": [
        ("from repos import archive_months, categories_with_count, recent_posts, tags_with_count",
         "from archive.repos import archive_months\nfrom categories.repos import categories_with_count\n"
         "from posts.repos import recent_posts\nfrom tags.repos import tags_with_count"),
    ],
    "web/admin.py": [
        ("from repos import count_posts",
         "from posts.repos import count_posts"),
    ],
    "blog/services/importer.py": [
        ("from repos.posts import save_post",
         "from posts.repos import save_post"),
        ("from repos.taxonomy import ensure_category",
         "from categories.repos import ensure_category"),
    ],
}

TARGETS = [
    "web/home.py", "web/post.py", "web/about.py", "web/archive.py", "web/tags.py",
    "web/categories.py", "web/search.py", "web/feed.py", "web/widgets.py",
    "web/layout.py", "web/admin.py",
    "blog/services/importer.py",
    "scripts/build_static.py",
]


def fix(text: str, rel: str) -> str:
    for old, new in GLOBAL:
        text = text.replace(old, new)
    for old, new in SPECIFIC.get(rel, []):
        text = text.replace(old, new)
    return text


for rel in TARGETS:
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        print("跳过(不存在):", rel)
        continue
    with io.open(path, encoding="utf-8") as f:
        src = f.read()
    out = fix(src, rel)
    if out != src:
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(out)
        print("已修正:", rel)
    else:
        print("无变化:", rel)

print("done")
