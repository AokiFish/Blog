"""web 渲染包：聚合所有页面路由，并统一再导出常用 UI 组件。

注意导入顺序：先导入 layout / widgets（定义好再导出），再导入各页面路由模块，
避免路由模块 `from web import xxx` 时尚未定义。
"""
from fasthtml.common import APIRouter

# 1) 先导入 UI 组件层（它们只依赖 blog.config / blog.core / *repos，不会回环）
from web.layout import footer, meta_tags, navbar, page_shell, theme_script
from web.widgets import (
    archive_card,
    categories_card,
    empty_state,
    pager_bar,
    post_card,
    recent_card,
    search_client,
    sidebar_column,
    tag_cloud,
    toc_sidebar,
)

# 2) 再导入页面路由模块（post 必须在 archive / tags 之前，后者引用其 not_found_page）
from web import about, admin, archive, categories, feed, home, hot, post, search, tags

# 3) 聚合所有子路由
router = APIRouter()
for _mod in (home, hot, post, about, archive, tags, categories, search, feed, admin):
    router.routes.extend(_mod.router.routes)

__all__ = [
    "router", "footer", "meta_tags", "navbar", "page_shell", "theme_script",
    "archive_card", "categories_card", "empty_state", "pager_bar", "post_card",
    "recent_card", "search_client", "sidebar_column", "tag_cloud",
    "toc_sidebar",
]
