"""blog 应用包：负责全局设置、创建 FastHTML 应用、挂载各子模块路由。

业务模块（posts / tags / categories / archive / web）各自持有 APIRouter，
本包把它们聚合并挂载到 app 上；首次启动且库为空时自动导入 content/ 下的文章。
"""
import os

from fasthtml.common import Link, Meta, Script, fast_app

from blog.config import AUTO_SEED, DEBUG, HOST, PORT, SITE_NAME
from web import feed, router
from web.layout import theme_script

# 确保数据库表先建好（导入即触发 database.py 的建表逻辑）
import blog.database  # noqa: F401

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app, rt = fast_app(
    default_hdrs=False,
    hdrs=(
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="generator", content="FastHTML"),
        Link(rel="icon", type="image/svg+xml", href="/static/img/favicon.svg"),
        Link(rel="stylesheet", href="/static/css/style.css", type="text/css"),
        Link(rel="stylesheet", href="/static/css/code.css", type="text/css"),
        Link(rel="alternate", type="application/rss+xml", title=SITE_NAME, href="/feed.xml"),
        theme_script(),
    ),
    ftrs=(Script(src="/static/js/app.js", defer=True),),
    htmlkw={"lang": "zh-CN"},
    # /static/* -> 项目根/static/*
    static_path=BASE_DIR,
)

# 挂载所有子路由（web/__init__.py 里已聚合各页面模块的 APIRouter）
router.to_app(app)

# FastHTML 的静态文件路由形如 /{fname}.{ext}，会先匹配到 /feed.xml、/sitemap.xml、
# /robots.txt、/search-index.json 这样的路径。把这几个输出类路由提到最前面。
_feed_paths = {"/feed.xml", "/sitemap.xml", "/robots.txt", "/search-index.json"}
_feed_routes = [r for r in app.router.routes if getattr(r, "path", None) in _feed_paths]
if _feed_routes:
    _ids = {id(r) for r in _feed_routes}
    app.router.routes = _feed_routes + [r for r in app.router.routes if id(r) not in _ids]


def ensure_content() -> None:
    """首次启动且库为空时，自动导入 content/posts 下的 Markdown。"""
    from posts.repos import count_posts
    from blog.services.importer import import_all

    if count_posts() > 0:
        return
    try:
        n = import_all()
        if n:
            print(f"[seed] 已导入 {n} 篇文章")
    except Exception as e:  # noqa: BLE001
        print(f"[seed] 自动导入失败：{e!r}")


if AUTO_SEED:
    ensure_content()


def serve() -> None:
    """本地开发入口：python main.py 或 python -m blog"""
    import uvicorn

    uvicorn.run("blog:app", host=HOST, port=PORT, reload=DEBUG)


if __name__ == "__main__":
    serve()
