"""blog 应用包：负责全局设置、创建 FastHTML 应用、挂载各子模块路由。

业务模块（posts / tags / categories / archive / web）各自持有 APIRouter，
本包把它们聚合并挂载到 app 上；首次启动且库为空时自动导入 content/ 下的文章。
"""
import os

from fasthtml.common import Link, Meta, Script, fast_app

import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from blog.config import AUTO_SEED, DEBUG, HOST, PORT, SITE_NAME
from web import feed, router
from web.layout import theme_script

# 确保数据库表先建好（导入即触发 database.py 的建表逻辑）
import blog.database  # noqa: F401

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _asset_ver(rel: str) -> str:
    """按静态文件修改时间生成版本号,文件一改 URL 即变,强制浏览器/CDN 破缓存。"""
    p = os.path.join(BASE_DIR, rel.lstrip("/"))
    try:
        return str(int(os.path.getmtime(p)))
    except OSError:
        return "1"


class _AssetVersionMiddleware(BaseHTTPMiddleware):
    """请求时按磁盘 mtime 给静态资源加版本号：文件一改 URL 即变，缓存必破。
    解决 dev 下 uvicorn --reload 不接管 __init__ 顶层、写死版本号不刷新的问题。"""

    _rx = re.compile(rb"(/static/(?:css|js|img)/[^\"'>\s]+)")

    async def dispatch(self, request, call_next):
        resp = await call_next(request)
        if "text/html" not in resp.headers.get("content-type", ""):
            return resp
        chunks = []
        async for chunk in resp.body_iterator:
            chunks.append(chunk if isinstance(chunk, bytes) else chunk.encode())
        body = b"".join(chunks)

        def repl(m):
            full = m.group(1).decode()
            path = full.split("?", 1)[0]
            return (path + "?v=" + _asset_ver(path.lstrip("/"))).encode()

        new_body = self._rx.sub(repl, body)
        headers = dict(resp.headers)
        headers.pop("content-length", None)
        return Response(content=new_body, status_code=resp.status_code, headers=headers)


app, rt = fast_app(
    default_hdrs=False,
    hdrs=(
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="generator", content="FastHTML"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=True),
        Link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,900&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap",
        ),
        Link(rel="icon", type="image/svg+xml", href="/static/img/favicon.svg"),
        Link(rel="stylesheet", href=f"/static/css/style.css?v={_asset_ver('static/css/style.css')}", type="text/css"),
        Link(rel="stylesheet", href=f"/static/css/code.css?v={_asset_ver('static/css/code.css')}", type="text/css"),
        Link(rel="alternate", type="application/rss+xml", title=SITE_NAME, href="/feed.xml"),
        theme_script(),
    ),
    ftrs=(Script(src=f"/static/js/app.js?v={_asset_ver('static/js/app.js')}", defer=True),),
    htmlkw={"lang": "zh-CN"},
    # /static/* -> 项目根/static/*
    static_path=BASE_DIR,
)

# 开发服务器动态注入静态资源版本号（请求时按文件 mtime），确保改 CSS/JS 后
# 浏览器/CDN 必然重新拉取，不再因缓存看到旧样式。
app.add_middleware(_AssetVersionMiddleware)

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
