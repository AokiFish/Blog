"""站点全局配置：读取 .env，集中管理路径、密钥与站点信息。

所有可变项都放 .env，代码里不出现硬编码密钥。
"""
import os

from dotenv import load_dotenv

# blog/ 是应用包，项目根目录是其父目录（静态资源 / 内容 / 构建产物都在项目根）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"))


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _env_int(key: str, default: int) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, "1" if default else "0").lower() in ("1", "true", "yes", "on")


# ------------------------------------------------------------ 站点信息 ----
SITE_NAME = _env("SITE_NAME", "技术笔记")
SITE_TAGLINE = _env("SITE_TAGLINE", "记录 Python · Web · AI 的学习与实践")
SITE_URL = _env("SITE_URL", "https://blog.272314369.xyz").rstrip("/")
AUTHOR = _env("AUTHOR", "博主")
AUTHOR_BIO = _env("AUTHOR_BIO", "")
AUTHOR_AVATAR = _env("AUTHOR_AVATAR", "/static/img/avatar.svg")
ICP = _env("ICP", "")
SINCE_YEAR = _env("SINCE_YEAR", "2026")

# ------------------------------------------------------------ 数据/密钥 ----
DB_PATH = os.path.join(BASE_DIR, _env("DB_PATH", "data/blog.db"))
DATABASE_URL = _env("DATABASE_URL", "")
SECRET_KEY = _env("SECRET_KEY", "dev-secret")
ADMIN_TOKEN = _env("ADMIN_TOKEN", "dev-token")
ADMIN_ENABLED = _env_bool("ADMIN_ENABLED", True)

# -------------------------------------------------------------- 运行态 ----
HOST = _env("HOST", "127.0.0.1")
PORT = _env_int("PORT", 5000)
DEBUG = _env_bool("DEBUG", True)
PAGE_SIZE = _env_int("PAGE_SIZE", 10)

# -------------------------------------------------------------- 目录常量 ----
STATIC_DIR = os.path.join(BASE_DIR, "static")
CONTENT_DIR = os.path.join(BASE_DIR, "content")
POSTS_DIR = os.path.join(CONTENT_DIR, "posts")
DIST_DIR = os.path.join(BASE_DIR, "build")

# 内容默认值：新站首启时用示例文章填充，可在 .env 关闭
AUTO_SEED = _env_bool("AUTO_SEED", True)

NAV_ITEMS = (
    ("/", "首页"),
    ("/about/", "关于"),
)
