"""页面骨架：导航栏 / 页脚 / 三栏布局 / 主题脚本。"""
from fasthtml.common import (
    A, Aside, Button, Div, Footer, Form, Header, Input, Main, Meta, Nav, NotStr,
    P, Script, Span, Title,
)

from blog.config import AUTHOR, NAV_ITEMS, SITE_NAME, SINCE_YEAR, SITE_TAGLINE, SITE_URL

# 站点 logo：天青色扁平笔记图标（与 favicon.svg 同源），内联到导航栏，避免外部图标缓存。
LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" aria-hidden="true">'
    '<rect width="64" height="64" rx="16" fill="#3f9688"/>'
    '<rect x="19" y="15" width="26" height="34" rx="4" fill="#ffffff"/>'
    '<path d="M37 15 h8 v8 z" fill="#bfe0d8"/>'
    '<rect x="24" y="28" width="16" height="2.8" rx="1.4" fill="#3f9688"/>'
    '<rect x="24" y="35" width="16" height="2.8" rx="1.4" fill="#3f9688"/>'
    '<rect x="24" y="42" width="10" height="2.8" rx="1.4" fill="#3f9688"/>'
    '</svg>'
)

# 主题初始化脚本：放到 <head> 里，避免刷新时闪白。
# 主题「切换」逻辑已统一移到 static/js/app.js（含 View Transitions 圆形转场），
# 此处不再内联，避免重复绑定导致点两次才生效。
THEME_BOOT_JS = """
(function(){
  try{
    var saved=localStorage.getItem('theme');
    var mode=saved||(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
    document.documentElement.setAttribute('data-theme',mode);
  }catch(e){document.documentElement.setAttribute('data-theme','light');}
})();
"""


def theme_script():
    # 仅保留「无闪烁初始化」脚本；主题切换（含 View Transitions 圆形转场）
    # 统一由 static/js/app.js 接管，避免与内联脚本重复绑定导致点两次才生效。
    return Script(NotStr(THEME_BOOT_JS))


def meta_tags(title: str, description: str = "", url: str = ""):
    return (
        Title(title),
        Meta(name="description", content=description or SITE_TAGLINE),
        Meta(property="og:title", content=title),
        Meta(property="og:description", content=description or SITE_TAGLINE),
        Meta(property="og:type", content="website"),
        Meta(property="og:url", content=url or SITE_URL),
    )


# 内联 SVG 图标（lucide 风格，避免 emoji 图标）
_SEARCH_ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"'
    ' stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    ' aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>'
)
_RSS_ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"'
    ' stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    ' aria-hidden="true"><path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/>'
    '<circle cx="5" cy="19" r="1"/></svg>'
)
_SUN_ICON = (
    '<svg class="ico-sun" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"'
    ' stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    ' aria-hidden="true"><circle cx="12" cy="12" r="4"/>'
    '<path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
)
_MOON_ICON = (
    '<svg class="ico-moon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"'
    ' stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    ' aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
)


def navbar(active: str = ""):
    """现代深色标题栏：左导航 / 中站名 / 右搜索 · RSS · 主题。"""
    nav_links = [
        A(
            label,
            href=href,
            cls="banner-link" + (
                " is-active"
                if active == href or (href != "/" and active.startswith(href))
                else ""
            ),
        )
        for href, label in NAV_ITEMS
    ]

    # 右侧操作区：内联搜索框 + RSS + 主题切换
    right = [
        Form(
            NotStr(_SEARCH_ICON),
            Input(
                type="search",
                name="q",
                placeholder="搜索文章…",
                aria_label="搜索文章",
                autocomplete="off",
                cls="header-search-input",
            ),
            action="/search/",
            method="get",
            role="search",
            cls="header-search",
            title="站内搜索",
        ),
        A(
            NotStr(_RSS_ICON),
            "RSS",
            href="/feed.xml",
            cls="banner-link rss-link",
            title="RSS 订阅",
        ),
        Button(
            NotStr(_SUN_ICON),
            NotStr(_MOON_ICON),
            type="button",
            id="theme-toggle",
            cls="theme-toggle",
            title="切换深色 / 浅色阅读",
            aria_label="切换深色或浅色主题",
        ),
    ]

    return Header(
        Div(
            # 左：站点 logo（点击返回首页） + 导航链接（首页 / 关于）
            Div(
                A(
                    NotStr(LOGO_SVG),
                    href="/",
                    cls="banner-brand",
                    title=SITE_NAME + " · 首页",
                    aria_label=SITE_NAME,
                ),
                Nav(*nav_links, cls="banner-side"),
                cls="banner-side banner-left",
            ),
            # 右：操作区
            Div(*right, cls="banner-side banner-right"),
            cls="banner-inner",
        ),
        cls="site-header",
    )


def footer():
    year = SINCE_YEAR
    return Footer(
        Div(
            P(f"© {year} · {SITE_NAME} · {AUTHOR}", cls="footer-line"),
            P(
                "Powered by ",
                A("FastHTML", href="https://fastht.ml", rel="noopener", target="_blank"),
                " + ",
                A("fastlite", href="https://github.com/AnswerDotAI/fastlite", rel="noopener", target="_blank"),
                cls="footer-line muted",
            ),
            cls="footer-inner",
        ),
        cls="site-footer",
    )


def page_shell(*body, aside=None, cls: str = ""):
    """内容区：左侧正文 + 右侧边栏（aside 为空时单栏）。"""
    main = Main(Div(*body, cls="content"), cls="main-content", id="posts")
    grain = Div(cls="grain", aria_hidden="true")
    if aside is None:
        layout = Div(main, cls="layout layout-single " + cls)
    else:
        layout = Div(main, Aside(aside, cls="sidebar"), cls="layout " + cls)
    # 单元素返回，避免路由层对嵌套元组的展平歧义
    return Div(grain, layout)
