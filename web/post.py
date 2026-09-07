"""文章详情页 /posts/{slug}/：正文 + 目录 + 上一篇/下一篇 + 相关文章。"""
import json
import re

from fasthtml.common import (
    APIRouter, A, Article, Div, H1, NotStr, P, Section, Span,
)

# 页面顶部已由模板渲染 <h1 class="post-title">；正文中手写的重复一级标题（# 标题）需剔除，避免出现两个大标题
_DUP_H1_RE = re.compile(r"<h1[^>]*>.*?</h1>", re.S)
from fasthtml.core import FtResponse
from starlette.responses import RedirectResponse

from blog.core import format_date
from blog.config import SITE_NAME
from posts.repos import add_views, get_post, neighbors, related_posts
from web import (
    footer,
    meta_tags,
    navbar,
    page_shell,
    post_card,
    sidebar_column,
    toc_sidebar,
)

router = APIRouter()


def post_detail(slug: str):
    post = get_post(slug)
    if not post:
        return not_found_page()

    try:
        toc = json.loads(post.get("toc") or "[]")
    except (ValueError, TypeError):
        toc = []

    prev_post, next_post = neighbors(post)
    related = related_posts(post, 3)

    head = Div(
        Div(
            A(post.get("category_name", "未分类"), href=f"/categories/{post.get('category','')}/", cls="post-cat"),
            Span("·", cls="dot"),
            Span(format_date(post["published_at"]), cls="post-date"),
            Span("·", cls="dot"),
            Span(f"约 {post.get('minutes', 1)} 分钟", cls="post-min"),
            Span("·", cls="dot"),
            Span(f"{post.get('words', 0)} 字", cls="post-words"),
            cls="post-meta",
        ),
        H1(post["title"], cls="post-title"),
        cls="post-head",
    )

    # 正文 HTML：标题已显示在上方，去掉正文里第一个重复的 <h1>（如手写的 # 标题）
    content_html = _DUP_H1_RE.sub("", post.get("content_html", ""), count=1)

    body = Article(
        head,
        Div(NotStr(content_html), cls="post-body markdown-body"),
        Div(
            *[A("#" + t["name"], href=f"/tags/{t['slug']}/", cls="post-tag") for t in post.get("tags", [])],
            cls="post-tags",
        ) if post.get("tags") else None,
        cls="post-article",
    )

    nav = Div(
        Div(
            A("← " + prev_post["title"], href=f"/posts/{prev_post['slug']}/", cls="nav-post prev")
            if prev_post else Span("已经是第一篇了", cls="nav-post prev is-empty"),
            A(next_post["title"] + " →", href=f"/posts/{next_post['slug']}/", cls="nav-post next")
            if next_post else Span("已经是最后一篇了", cls="nav-post next is-empty"),
            cls="post-nav",
        ),
    )

    sections = [body, nav]
    if related:
        sections.append(
            Section(
                Div("相关文章", cls="section-title"),
                *[post_card(p) for p in related],
                cls="related-block",
            )
        )

    return (
        meta_tags(f"{post['title']} · {SITE_NAME}", post.get("summary", "")),
        navbar("/archives"),
        page_shell(
            Div(*sections, cls="post-main"),
            aside=sidebar_column(toc=toc_sidebar(toc), exclude_slug=slug),
        ),
        footer(),
    )


@router("/posts/")
def posts_list():
    """/posts/ 不是列表页（列表在首页 / 与 /page/{n}/），301 到首页避免 404。"""
    return RedirectResponse("/", status_code=301)


@router("/posts")
def posts_list_no_slash():
    return RedirectResponse("/", status_code=301)


@router("/posts/{slug}/")
def detail(slug: str):
    try:
        add_views(slug)
    except Exception:  # noqa: BLE001  阅读量失败不影响正文
        pass
    return post_detail(slug)


def not_found_page():
    return FtResponse(
        (
            meta_tags("页面不存在 · " + SITE_NAME),
            navbar(""),
            page_shell(
                Div(
                    Div("404", cls="code"),
                    P("没有找到这个页面，文章可能已经被删除或移到别处了。"),
                    A("回到首页", href="/", cls="btn"),
                    cls="notfound",
                ),
                aside=sidebar_column(),
            ),
            footer(),
        ),
        status_code=404,
    )
