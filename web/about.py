"""关于页面 /about/：内容来自 content/about.md。"""
from fasthtml.common import APIRouter, Article, Div, H1, NotStr

from blog.config import SITE_NAME
from blog.services.importer import load_about
from web import footer, meta_tags, navbar, page_shell, sidebar_column

router = APIRouter()


@router("/about/")
def about():
    html, _ = load_about()
    return (
        meta_tags(f"关于 · {SITE_NAME}"),
        navbar("/about"),
        page_shell(
            Div(
                H1("关于", cls="page-title"),
                Article(NotStr(html), cls="post-body markdown-body"),
                cls="about-page",
            ),
            aside=sidebar_column(),
        ),
        footer(),
    )
