"""标签页：/tags/ 标签总览，/tags/{slug}/ 单标签文章列表。"""
from urllib.parse import unquote, quote

from fasthtml.common import APIRouter, A, Div, H1, P, Span
from fasthtml.core import FtResponse

from blog.config import PAGE_SIZE, SITE_NAME
from blog.core import Pager
from posts.repos import count_posts, list_posts
from tags.repos import tags_with_count
from web.post import not_found_page
from web import (
    empty_state,
    footer,
    meta_tags,
    navbar,
    page_shell,
    pager_bar,
    post_card,
    sidebar_column,
)

router = APIRouter()


@router("/tags/")
def index():
    items = tags_with_count()
    body = [
        Div(
            H1("标签", cls="page-title"),
            P(f"共 {len(items)} 个标签。", cls="page-subtitle"),
            cls="page-head",
        )
    ]
    if items:
        body.append(
            Div(
                *[
                    A(
                        t["name"],
                        Span(str(t["count"]), cls="tag-count"),
                        href=f"/tags/{quote(t['slug'], safe='')}/",
                        cls="tag-chip is-large",
                    )
                    for t in items
                ],
                cls="tag-cloud is-page",
            )
        )
    else:
        body.append(empty_state("还没有任何标签。"))

    return (
        meta_tags(f"标签 · {SITE_NAME}"),
        navbar("/tags"),
        page_shell(*body, aside=sidebar_column()),
        footer(),
    )


@router("/tags/{slug}/")
def tag(slug: str, page: int = 1):
    slug = unquote(slug)
    name = next((t["name"] for t in tags_with_count() if t["slug"] == slug), slug)
    total = count_posts(tag=slug)
    pager = Pager(total, page, PAGE_SIZE)
    items = list_posts(page=pager.page, size=PAGE_SIZE, tag=slug)
    base = f"/tags/{quote(slug, safe='')}/page"
    return (
        meta_tags(f"{name} · 标签 · {SITE_NAME}"),
        navbar("/tags"),
        page_shell(
            Div(
                H1("#" + name, cls="page-title"),
                P(f"{total} 篇相关文章", cls="page-subtitle"),
                cls="page-head",
            ),
            *([post_card(p) for p in items] or [empty_state("这个标签下还没有文章。")]),
            pager_bar(pager, base=base),
            aside=sidebar_column(),
        ),
        footer(),
    )


@router("/tags/{slug}/page/{p}/")
def tag_page(slug: str, p: str = "1"):
    try:
        n = int(p)
    except ValueError:
        n = 1
    return tag(slug, n)
