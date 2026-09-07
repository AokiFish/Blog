"""全站搜索 /search?q=：标题 + 摘要 + 正文的 LIKE 匹配。"""
from fasthtml.common import APIRouter, Div, H1, P

from blog.config import PAGE_SIZE, SITE_NAME
from blog.core import Pager
from posts.repos import count_posts, list_posts
from web import (
    empty_state,
    footer,
    meta_tags,
    navbar,
    page_shell,
    pager_bar,
    post_card,
    search_client,
    sidebar_column,
)

router = APIRouter()


@router("/search")
def search(q: str = "", page: int = 1):
    q = (q or "").strip()
    total = count_posts(q=q) if q else 0
    pager = Pager(total, page, PAGE_SIZE)
    items = list_posts(page=pager.page, size=PAGE_SIZE, q=q) if q else []

    return (
        meta_tags(f"搜索 {q} · {SITE_NAME}"),
        navbar(""),
        page_shell(
            Div(
                H1("搜索", cls="page-title"),
                P(f"关键词「{q}」共找到 {total} 篇文章。" if q else "输入关键词开始搜索。", cls="page-subtitle"),
                cls="page-head",
            ),
            *([post_card(p) for p in items] or [empty_state("没有匹配的文章，换个关键词试试。") if q else empty_state()]),
            pager_bar(pager, base="/search/page", query=f"q={q}" if q else ""),
            aside=sidebar_column(),
        ),
        footer(),
    )


@router("/search/")
def client_search(q: str = ""):
    """客户端搜索页（依赖 /search-index.json）：静态部署后同样可用。"""
    return (
        meta_tags(f"搜索 · {SITE_NAME}"),
        navbar(""),
        page_shell(
            Div(H1("搜索", cls="page-title"), cls="page-head"),
            search_client(),
            aside=sidebar_column(),
        ),
        footer(),
    )


@router("/search/page/{p}/")
def search_page(p: str = "1", q: str = ""):
    try:
        n = int(p)
    except ValueError:
        n = 1
    return search(q, n)
