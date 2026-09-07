"""本地冒烟测试：启动服务后逐条访问所有路由，检查状态码与关键内容。

用法：
    python scripts/smoke_test.py [base_url]
"""
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000").rstrip("/")

CHECKS = [
    ("/", 200, ["最新文章", "近期文章", "标签", "归档", "分类"]),
    ("/page/2/", 200, None),
    ("/about/", 200, ["关于"]),
    ("/archives/", 200, ["归档"]),
    ("/archives/2026-08/", 200, None),
    ("/tags/", 200, ["标签"]),
    ("/tags/python/", 200, None),
    ("/tags/深度学习/", 200, None),
    ("/categories/", 200, ["分类"]),
    ("/categories/python/", 200, None),
    ("/search?q=Python", 200, ["搜索"]),
    ("/search/", 200, ["search-results"]),
    ("/search-index.json", 200, ["url", "/posts/"]),
    ("/feed.xml", 200, ["<rss"]),
    ("/sitemap.xml", 200, ["<urlset"]),
    ("/robots.txt", 200, ["Sitemap:"]),
    ("/static/css/style.css", 200, None),
    ("/static/js/app.js", 200, None),
    ("/static/img/avatar.svg", 200, None),
    ("/this-page-does-not-exist/", 404, None),
]


def _get(path: str):
    url = BASE + urllib.parse.quote(path, safe="/:?=&%")
    req = urllib.request.Request(url, headers={"User-Agent": "smoke-test"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def main() -> int:
    ok = fail = 0

    # 详情页：先抓首页，取第一篇文章的真实 slug 再访问
    _, home = _get("/")
    slugs = re.findall(r'href="/posts/([^"/]+)/"', home)
    if slugs:
        path = f"/posts/{slugs[0]}/"
        status, body = _get(path)
        good = status == 200 and "相关文章" in body and "markdown-body" in body
        print(f"[ {'OK' if good else 'FAIL'} ] {path} -> {status}（正文渲染={'是' if 'markdown-body' in body else '否'}）")
        ok, fail = (ok + 1, fail) if good else (ok, fail + 1)
    else:
        print("[FAIL] 首页没有解析到任何文章链接")
        fail += 1

    for path, expect, must_contain in CHECKS:
        try:
            status, body = _get(path)
        except Exception as e:  # noqa: BLE001
            print(f"[ERR ] {path} -> {e!r}")
            fail += 1
            continue
        status_ok = status == expect
        content_ok = all(k in body for k in must_contain) if must_contain else True
        if status_ok and content_ok:
            print(f"[ OK ] {path} -> {status}")
            ok += 1
        else:
            print(f"[FAIL] {path} -> {status} (期望 {expect}) 内容命中={content_ok}")
            fail += 1

    # 首页 HTML 结构检查
    status, html = _get("/")
    has_title = "<title" in html and "</title>" in html
    has_theme = "theme-toggle" in html
    print(f"[INFO] <title> 存在: {has_title}; 主题切换存在: {has_theme}")

    # 搜索索引必须是合法 JSON（防止回落到默认页的假阳性）
    import json
    s, body = _get("/search-index.json")
    try:
        obj = json.loads(body)
        json_ok = isinstance(obj, list) and len(obj) > 0 and "title" in obj[0]
    except Exception:  # noqa: BLE001
        json_ok = False
    print(f"[ {'OK' if json_ok else 'FAIL'} ] /search-index.json 是合法 JSON 且含文章: {json_ok}")
    if not json_ok:
        fail += 1

    print(f"\n通过 {ok} 项，失败 {fail} 项")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
