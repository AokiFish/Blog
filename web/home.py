"""首页与分页：/ 与 /page/{n}/"""
from fasthtml.common import APIRouter, Div, H1, NotStr, P

from blog.config import PAGE_SIZE, SITE_NAME, SITE_TAGLINE
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
    sidebar_column,
)

router = APIRouter()


def _render(page_no: int, base: str = "/page"):
    total = count_posts()
    pager = Pager(total, page_no, PAGE_SIZE)
    items = list_posts(page=pager.page, size=PAGE_SIZE)
    body = [
        Div(
            H1("最新文章", cls="page-title"),
            P(SITE_TAGLINE, cls="page-subtitle"),
            cls="page-head",
        )
    ]
    body += [post_card(p) for p in items] if items else [empty_state("还没有发布任何文章。")]
    if pager_bar(pager, base=base):
        body.append(pager_bar(pager, base=base))
    return (
        meta_tags(f"{SITE_NAME} · 首页"),
        navbar("/"),
        page_shell(*body, aside=sidebar_column()),
        footer(),
    )


@router("/")
def index(page: int = 1):
    return _render(page)


@router("/page/{p}/")
def page_no(p: str = "1"):
    try:
        n = int(p)
    except ValueError:
        n = 1
    return _render(n)
