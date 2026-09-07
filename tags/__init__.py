"""标签模块：对外暴露仓库函数。"""
from tags.repos import ensure_tags, set_post_tags, tags_of_post, tags_with_count

__all__ = ["ensure_tags", "set_post_tags", "tags_of_post", "tags_with_count"]
