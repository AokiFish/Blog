"""首页与分页：/ 与 /page/{n}/"""
from fasthtml.common import APIRouter, A, B, Div, H1, P, Section, Span

from blog.config import PAGE_SIZE, SITE_NAME, SITE_TAGLINE, SINCE_YEAR
from blog.core import Pager
from categories.repos import categories_with_count
from posts.repos import count_posts, list_posts
from tags.repos import tags_with_count
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


def hero():
    """首页全幅主视觉：大字标题 + 标语 + 话题跑马灯 + 数据。"""
    cats = categories_with_count()
    tags = tags_with_count()
    topics = [c["name"] for c in cats] + [t["name"] for t in tags]
    if not topics:
        topics = ["Python", "Web", "AI", "工具", "数据库", "随笔"]
    topics = topics[:16]
    track = [Span(t, cls="marquee-item") for t in topics]
    total = count_posts()
    return Section(
        Div(
            P("PYTHON · WEB · AI — 学习与实践", cls="hero-eyebrow"),
            H1(SITE_NAME, cls="hero-title"),
            P(SITE_TAGLINE, cls="hero-sub"),
            Div(
                A("开始阅读", href="#posts", cls="hero-cta"),
                cls="hero-actions",
            ),
            Div(
                Div(
                    Div(*track, cls="marquee-track"),
                    Div(*track, cls="marquee-track", aria_hidden="true"),
                    cls="marquee-inner",
                ),
                cls="marquee",
            ),
            Div(
                Div(B(str(total)), Span("篇文章"), cls="hero-stat"),
                Div(B(str(len(cats))), Span("个分类"), cls="hero-stat"),
                Div(B(SINCE_YEAR), Span("年起记录"), cls="hero-stat"),
                cls="hero-stats",
            ),
            cls="hero-inner",
        ),
        cls="hero",
    )


def _render(page_no: int, base: str = "/page"):
    pager = Pager(count_posts(), page_no, PAGE_SIZE)
    items = list_posts(page=pager.page, size=PAGE_SIZE)
    body = [post_card(p) for p in items] if items else [empty_state("还没有发布任何文章。")]
    if pager_bar(pager, base=base):
        body.append(pager_bar(pager, base=base))
    return (
        meta_tags(f"{SITE_NAME} · 首页"),
        navbar("/"),
        hero(),
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
