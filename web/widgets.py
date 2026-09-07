"""侧边栏卡片与列表组件：近期文章 / 标签 / 归档 / 分类 / 目录 / 分页。"""
from urllib.parse import quote

from fasthtml.common import (
    A, Article, Details, Div, Form, H2, H3, Input, Li, NotStr, P, Script,
    Section, Span, Summary, Ul,
)

from blog.core import format_date, month_label
from archive.repos import archive_months
from categories.repos import categories_with_count
from posts.repos import recent_posts
from tags.repos import tags_with_count


def _tag_url(slug: str) -> str:
    return f"/tags/{quote(slug, safe='')}/"


def _cat_url(slug: str) -> str:
    return f"/categories/{quote(slug, safe='')}/"


# ------------------------------------------------------------ 侧边栏卡片 ----


def recent_card(limit: int = 6, exclude_slug: str = ""):
    items = recent_posts(limit, exclude_slug)
    if not items:
        return None
    return Section(
        H3("近期文章", cls="card-title"),
        Ul(
            *[
                Li(
                    A(
                        Span(format_date(p["published_at"], "%m-%d"), cls="item-date"),
                        Span(p["title"], cls="item-text"),
                        href=f"/posts/{p['slug']}/",
                        cls="item-link",
                    )
                )
                for p in items
            ],
            cls="recent-list",
        ),
        cls="card",
    )


def tag_cloud(limit: int = 0):
    items = tags_with_count()
    if limit:
        items = items[:limit]
    if not items:
        return None
    return Section(
        H3("标签", cls="card-title"),
        Div(
            *[
                A(
                    t["name"],
                    Span(str(t["count"]), cls="tag-count"),
                    href=_tag_url(t["slug"]),
                    cls="tag-chip",
                    title=f"{t['count']} 篇文章",
                )
                for t in items
            ],
            cls="tag-cloud",
        ),
        cls="card",
    )


def archive_card():
    months = archive_months()
    if not months:
        return None
    total = sum(m["count"] for m in months)
    return Details(
        Summary("归档", cls="card-head"),
        Div(
            Ul(
                *[
                    Li(
                        A(
                            Span(month_label(m["ym"]), cls="item-text"),
                            Span(str(m["count"]), cls="item-count"),
                            href=f"/archives/{m['ym']}/",
                            cls="item-link",
                        )
                    )
                    for m in months
                ],
                cls="archive-list",
            ),
            P(f"共 {total} 篇文章", cls="card-foot-note"),
            cls="card-body",
        ),
        cls="card collapse-card",
        open=True,
    )


def categories_card():
    cats = categories_with_count()
    if not cats:
        return None
    return Details(
        Summary("分类", cls="card-head"),
        Div(
            Ul(
                *[
                    Li(
                        A(
                            Span(c["name"], cls="item-text"),
                            Span(str(c["count"]), cls="item-count"),
                            href=_cat_url(c["slug"]),
                            cls="item-link",
                        )
                    )
                    for c in cats
                ],
                cls="category-list",
            ),
            cls="card-body",
        ),
        cls="card collapse-card",
        open=True,
    )


def sidebar_column(*, toc=None, exclude_slug: str = ""):
    """组合右侧栏：顶部槽位（文章页为目录，其他页为近期文章）+ 标签 / 归档 / 分类。

    toc: 传入 toc_sidebar(toc) 的结果，文章详情页使用。
    """
    cards = []
    if toc is not None:
        cards.append(toc)
    else:
        cards.append(recent_card(6, exclude_slug))
    cards.extend(
        [
            tag_cloud(),
            archive_card(),
            categories_card(),
        ]
    )
    return Div(*[c for c in cards if c is not None], cls="sidebar-inner")


# -------------------------------------------------------------- 文章卡片 ----
def post_card(post: dict):
    tags = post.get("tags") or []
    return Article(
        Div(
            A(post.get("category_name", "未分类"), href=_cat_url(post.get("category", "")), cls="card-cat"),
            Span("·", cls="dot"),
            Span(format_date(post["published_at"]), cls="card-date"),
            Span("·", cls="dot"),
            Span(f"{post.get('minutes', 1)} 分钟", cls="card-min"),
            cls="card-meta",
        ),
        H2(A(post["title"], href=f"/posts/{post['slug']}/"), cls="card-title"),
        P(post.get("summary", ""), cls="card-summary"),
        Div(
            *[A("#" + t["name"], href=_tag_url(t["slug"]), cls="card-tag") for t in tags],
            A("阅读全文 →", href=f"/posts/{post['slug']}/", cls="card-more"),
            cls="card-foot",
        ),
        cls="post-card",
    )


def pager_bar(pager, base: str = "/", root: str = "", suffix: str = "", query: str = ""):
    """分页条。base：数字页前缀，形如 '/page'、'/archives/2026-09/page'。

    root：第 1 页（及「上一页」回退到首页时）指向的列表根地址。
    缺省时自动推导：去掉 base 尾部的 '/page'（如 '/page' -> '/')。
    query：附加到链接的查询串（如 'q=xxx'）。
    """
    if pager.pages <= 1:
        return None
    qs = f"?{query}" if query else ""
    if not root:
        root = base[:-5] if base.endswith("/page") else base  # 去掉尾部 '/page'
    root = root.rstrip("/")

    def href(page_no: int) -> str:
        if page_no <= 1:
            return f"{root}/{qs}" if root else f"/{qs}"
        return f"{base}/{page_no}/{qs}"

    items = []
    if pager.has_prev:
        items.append(A("上一页", href=href(pager.prev_page), cls="page-btn"))
    for p in pager.page_numbers():
        if p == 0:
            items.append(Span("…", cls="page-dots"))
        elif p == pager.page:
            items.append(Span(str(p), cls="page-btn is-current"))
        else:
            items.append(A(str(p), href=href(p), cls="page-btn"))
    if pager.has_next:
        items.append(A("下一页", href=href(pager.next_page), cls="page-btn"))
    return Div(*items, cls="pager")


def empty_state(text: str = "这里还没有内容。"):
    return Div(P(text, cls="muted"), cls="empty-state")


def toc_sidebar(toc: list[dict]):
    """文章详情页目录：放在右侧栏顶部，随侧栏 sticky 固定，不遮挡正文。"""
    if not toc:
        return None
    items = [
        Li(
            A(t["text"], href="#" + t["id"]),
            cls=f"toc-item toc-l{t.get('level', 2)}",
        )
        for t in toc
    ]
    return Section(
        H3("目录", cls="card-title"),
        Div(Ul(*items, cls="toc-list"), cls="toc-scroll"),
        cls="card toc-card",
        id="toc",
    )


# ------------------------------------------------------- 客户端搜索（/search/）----
SEARCH_JS = """
(function(){
  var box=document.getElementById('search-results');
  var input=document.getElementById('q');
  var q=new URLSearchParams(location.search).get('q')||'';
  if(input) input.value=q;
  function esc(s){return String(s).replace(/[&<>"']/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function render(items,kw){
    if(!kw){box.innerHTML='<p class="muted">输入关键词开始搜索（标题 / 摘要 / 标签 / 分类）。</p>';return;}
    if(!items.length){box.innerHTML='<div class="empty-state">没有匹配的文章，换个关键词试试。</div>';return;}
    box.innerHTML='<p class="page-subtitle">共找到 '+items.length+' 篇文章</p>'+items.map(function(it){
      return '<article class="post-card"><div class="card-meta"><span class="card-cat">'+esc(it.category)+
        '</span><span class="dot">·</span><span class="card-date">'+esc(it.date)+
        '</span></div><h2 class="card-title"><a href="'+esc(it.url)+'">'+esc(it.title)+
        '</a></h2><p class="card-summary">'+esc(it.summary)+'</p></article>';
    }).join('');
  }
  fetch('/search-index.json').then(function(r){return r.json();}).then(function(all){
    var kw=q.trim().toLowerCase();
    if(!kw){render([],'');return;}
    var hits=all.filter(function(it){
      return (it.title+' '+it.summary+' '+(it.tags||[]).join(' ')+' '+it.category).toLowerCase().indexOf(kw)>=0;
    });
    render(hits,q);
  }).catch(function(){
    box.innerHTML='<div class="empty-state">搜索索引加载失败。</div>';
  });
})();
"""


def search_client():
    """客户端搜索页：读取 /search-index.json，静态部署同样可用。"""
    return Div(
        Form(
            Input(
                type="search",
                id="q",
                name="q",
                placeholder="搜索标题 / 摘要 / 标签…",
                aria_label="搜索文章",
                cls="search-input is-wide",
            ),
            action="/search/",
            method="get",
            cls="search-form is-page",
        ),
        Div("正在加载索引…", id="search-results", cls="search-results"),
        Script(NotStr(SEARCH_JS)),
        cls="search-page",
    )
