"""文章模块：对外暴露仓库函数。"""
from posts.repos import (
    add_views,
    all_posts,
    count_posts,
    delete_all,
    delete_post,
    get_post,
    get_post_by_id,
    hot_posts,
    list_posts,
    neighbors,
    recent_posts,
    related_posts,
    save_post,
    search_posts,
    set_status,
)

__all__ = [
    "add_views", "all_posts", "count_posts", "delete_all", "delete_post",
    "get_post", "get_post_by_id", "hot_posts", "list_posts", "neighbors",
    "recent_posts", "related_posts", "save_post", "search_posts", "set_status",
]
