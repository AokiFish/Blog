"""热点文章：/hot/ —— 按阅读量降序排列。"""
from fasthtml.common import APIRouter, A, Div, H1, H2, NotStr, P, Span

from blog.config import SITE_NAME, SITE_TAGLINE
from posts.repos import hot_posts
from web import (
    empty_state,
    footer,
    meta_tags,
    navbar,
    page_shell,
    sidebar_column,
)

router = APIRouter()


def hot_card(post: dict):
    """热点文章卡片：带阅读量标识。"""
    tags = post.get("tags") or []
    return Div(
        Div(
            Span(f"👁 {post.get('views', 0)}", cls="hot-views"),
            cls="hot-badge",
        ),
        Div(
            Div(
                A(post.get("category_name", "未分类"), href=f"/categories/{post.get('category', '')}/", cls="card-cat"),
                Span("·", cls="dot"),
                Span(post.get("published_at", "")[:10], cls="card-date"),
                cls="card-meta",
            ),
            H2(A(post["title"], href=f"/posts/{post['slug']}/"), cls="card-title"),
            P(post.get("summary", ""), cls="card-summary"),
            Div(
                *[A("#" + t["name"], href=f"/tags/{t['slug']}/", cls="card-tag") for t in tags],
                cls="card-foot",
            ),
            cls="hot-body",
        ),
        cls="hot-card",
    )


def _render():
    items = hot_posts(limit=20)
    body = [
        Div(
            H1("热点文章", cls="page-title"),
            P("按阅读量排序，看看大家都在看什么。", cls="page-subtitle"),
            cls="page-head",
        )
    ]
    body += [hot_card(p) for p in items] if items else [empty_state("还没有足够的阅读数据。")]
    return (
        meta_tags(f"{SITE_NAME} · 热点文章"),
        navbar("/hot/"),
        page_shell(*body, aside=sidebar_column()),
        footer(),
    )


@router("/hot/")
def hot_index():
    return _render()
