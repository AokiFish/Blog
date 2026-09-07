"""站点输出：RSS / sitemap / robots。"""
from datetime import datetime
from email.utils import format_datetime
from urllib.parse import quote
from xml.sax.saxutils import escape

from fasthtml.common import APIRouter
from starlette.responses import JSONResponse, Response

from blog.config import SITE_NAME, SITE_TAGLINE, SITE_URL
from blog.core import format_date
from posts.repos import all_posts
from archive.repos import archive_months
from categories.repos import categories_with_count
from tags.repos import tags_with_count

router = APIRouter()


def _url(path: str) -> str:
    return SITE_URL + quote(path, safe="/")


@router("/feed.xml")
def rss():
    posts = all_posts(50)
    now = format_datetime(datetime.now())
    items = "\n".join(
        f"""    <item>
      <title>{escape(p['title'])}</title>
      <link>{_url('/posts/' + p['slug'] + '/')}</link>
      <guid isPermaLink="true">{_url('/posts/' + p['slug'] + '/')}</guid>
      <pubDate>{format_datetime(datetime.strptime(p['published_at'][:19], '%Y-%m-%d %H:%M:%S'))}</pubDate>
      <description>{escape(p.get('summary', ''))}</description>
    </item>"""
        for p in posts
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(SITE_NAME)}</title>
    <link>{SITE_URL}/</link>
    <description>{escape(SITE_TAGLINE)}</description>
    <language>zh-CN</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{_url('/feed.xml')}" rel="self" type="application/rss+xml"/>
{items}
  </channel>
</rss>
"""
    return Response(xml, media_type="application/rss+xml; charset=utf-8")


@router("/sitemap.xml")
def sitemap():
    urls = ["/", "/about/", "/archives/", "/tags/", "/categories/"]
    urls += [f"/posts/{p['slug']}/" for p in all_posts()]
    urls += [f"/tags/{quote(t['slug'], safe='')}/" for t in tags_with_count()]
    urls += [f"/categories/{quote(c['slug'], safe='')}/" for c in categories_with_count()]
    urls += [f"/archives/{m['ym']}/" for m in archive_months()]

    body = "\n".join(
        f"  <url><loc>{escape(_url(u))}</loc><changefreq>weekly</changefreq><priority>0.{'8' if u == '/' else '6'}</priority></url>"
        for u in dict.fromkeys(urls)
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""
    return Response(xml, media_type="application/xml; charset=utf-8")


@router("/search-index.json")
def search_index():
    """客户端搜索索引：静态部署后 /search/ 用它做离线搜索。

    必须显式返回 JSONResponse —— FastHTML 对“裸列表”返回值在直接 ASGI
    调用（静态构建脚本）下不会自动序列化为 JSON，会回落到默认页。
    """
    data = [
        {
            "title": p["title"],
            "url": f"/posts/{p['slug']}/",
            "summary": p.get("summary", ""),
            "date": format_date(p["published_at"]),
            "category": p.get("category_name", "未分类"),
            "tags": [t["name"] for t in p.get("tags", [])],
        }
        for p in all_posts()
    ]
    return JSONResponse(data)


@router("/robots.txt")
def robots():
    txt = f"""User-agent: *
Allow: /
Disallow: /admin/

Sitemap: {SITE_URL}/sitemap.xml
"""
    return Response(txt, media_type="text/plain; charset=utf-8")
