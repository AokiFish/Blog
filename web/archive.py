"""归档页：/archives/ 按年分组时间线，/archives/{ym}/ 单月列表。"""
from fasthtml.common import APIRouter, A, Div, H1, H2, Li, P, Span, Ul
from fasthtml.core import FtResponse

from blog.config import PAGE_SIZE, SITE_NAME
from blog.core import Pager, format_date, month_label
from archive.repos import archive_months
from posts.repos import count_posts, list_posts
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


@router("/archives/")
def index():
    months = archive_months()
    # 按年份分组：{2026: [{ym,count}, ...]}
    by_year: dict[str, list] = {}
    for m in months:
        by_year.setdefault(m["ym"][:4], []).append(m)

    blocks = []
    for year in sorted(by_year, reverse=True):
        items = by_year[year]
        blocks.append(
            Div(
                H2(year, cls="year-title"),
                Ul(
                    *[
                        Li(
                            A(
                                Span(month_label(m["ym"]), cls="item-text"),
                                Span(f"{m['count']} 篇", cls="item-count"),
                                href=f"/archives/{m['ym']}/",
                                cls="item-link",
                            )
                        )
                        for m in items
                    ],
                    cls="archive-list",
                ),
                cls="year-block",
            )
        )
    total = sum(m["count"] for m in months)

    return (
        meta_tags(f"归档 · {SITE_NAME}"),
        navbar("/archives"),
        page_shell(
            Div(
                H1("归档", cls="page-title"),
                P(f"共 {total} 篇文章，按月份归档。", cls="page-subtitle"),
                cls="page-head",
            ),
            *(blocks or [empty_state("还没有归档内容。")]),
            aside=sidebar_column(),
        ),
        footer(),
    )


@router("/archives/{ym}/")
def month(ym: str, page: int = 1):
    if len(ym) != 7 or ym[4] != "-":
        return not_found_page()
    months = archive_months()
    if not any(m["ym"] == ym for m in months):
        return not_found_page()

    total = count_posts(ym=ym)
    pager = Pager(total, page, PAGE_SIZE)
    items = list_posts(page=pager.page, size=PAGE_SIZE, ym=ym)
    return (
        meta_tags(f"{month_label(ym)} 归档 · {SITE_NAME}"),
        navbar("/archives"),
        page_shell(
            Div(
                H1(month_label(ym), cls="page-title"),
                P(f"{total} 篇文章", cls="page-subtitle"),
                cls="page-head",
            ),
            *([post_card(p) for p in items] or [empty_state()]),
            pager_bar(pager, base=f"/archives/{ym}/page"),
            aside=sidebar_column(),
        ),
        footer(),
    )


@router("/archives/{ym}/page/{p}/")
def month_page(ym: str, p: str = "1"):
    try:
        n = int(p)
    except ValueError:
        n = 1
    return month(ym, n)
