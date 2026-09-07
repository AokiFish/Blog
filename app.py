"""兼容入口：保留 `uvicorn app:app` 的可用性，实际应用定义在 blog 包内。"""
from blog import app

__all__ = ["app"]
