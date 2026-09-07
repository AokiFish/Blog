"""分类页：/categories/ 总览，/categories/{slug}/ 单分类文章列表。"""
from urllib.parse import quote

from fasthtml.common import APIRouter, A, Div, H1, P, Span

from blog.config import PAGE_SIZE, SITE_NAME
from blog.core import Pager
from categories.repos import categories_with_count
from posts.repos import count_posts, list_posts
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


@router("/categories/")
def index():
    cats = categories_with_count()
    body = [
        Div(
            H1("分类", cls="page-title"),
            P(f"共 {len(cats)} 个分类。", cls="page-subtitle"),
            cls="page-head",
        )
    ]
    if cats:
        body.append(
            Div(
                *[
                    A(
                        Div(c["name"], cls="cat-name"),
                        P(c.get("description") or "", cls="cat-desc") if c.get("description") else None,
                        Span(f"{c['count']} 篇", cls="cat-count"),
                        href=f"/categories/{quote(c['slug'], safe='')}/",
                        cls="cat-card",
                    )
                    for c in cats
                ],
                cls="cat-grid",
            )
        )
    else:
        body.append(empty_state("还没有任何分类。"))

    return (
        meta_tags(f"分类 · {SITE_NAME}"),
        navbar("/categories"),
        page_shell(*body, aside=sidebar_column()),
        footer(),
    )


@router("/categories/{slug}/")
def category(slug: str, page: int = 1):
    name = next((c["name"] for c in categories_with_count() if c["slug"] == slug), slug)
    total = count_posts(category=slug)
    pager = Pager(total, page, PAGE_SIZE)
    items = list_posts(page=pager.page, size=PAGE_SIZE, category=slug)
    base = f"/categories/{quote(slug, safe='')}/page"
    return (
        meta_tags(f"{name} · 分类 · {SITE_NAME}"),
        navbar("/categories"),
        page_shell(
            Div(
                H1(name, cls="page-title"),
                P(f"{total} 篇文章", cls="page-subtitle"),
                cls="page-head",
            ),
            *([post_card(p) for p in items] or [empty_state("这个分类下还没有文章。")]),
            pager_bar(pager, base=base),
            aside=sidebar_column(),
        ),
        footer(),
    )


@router("/categories/{slug}/page/{p}/")
def category_page(slug: str, p: str = "1"):
    try:
        n = int(p)
    except ValueError:
        n = 1
    return category(slug, n)
