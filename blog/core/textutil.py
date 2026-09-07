"""文本与日期工具。"""
import re
import unicodedata

from datetime import datetime

DATE_FMT = "%Y-%m-%d %H:%M:%S"

_PUNCT_RE = re.compile(r"[^\w\u4e00-\u9fff\s-]", re.UNICODE)
_SPACE_RE = re.compile(r"[\s_]+")


def now_str() -> str:
    return datetime.now().strftime(DATE_FMT)


def slugify(value: str, fallback: str = "post") -> str:
    """中文友好的 slug：保留汉字/字母/数字，其余转连字符。"""
    value = unicodedata.normalize("NFKC", value or "")
    value = _PUNCT_RE.sub("", value)
    value = _SPACE_RE.sub("-", value.strip().lower())
    value = value.strip("-")
    return value or fallback


def truncate(text: str, length: int = 120, suffix: str = "…") -> str:
    text = (text or "").strip()
    return text if len(text) <= length else text[:length].rstrip() + suffix


def reading_minutes(md_text: str, words_per_min: int = 320) -> tuple[int, int]:
    """返回 (字数, 阅读分钟数)：中英文混排按字符粗算。"""
    plain = re.sub(r"```.*?```", "", md_text or "", flags=re.S)
    plain = re.sub(r"[#>*`\-_!\[\]()|]", " ", plain)
    words = len(re.sub(r"\s+", "", plain))
    return words, max(1, round(words / words_per_min))


def format_date(value: str, fmt: str = "%Y-%m-%d") -> str:
    """'2026-03-05 09:00:00' -> '2026-03-05'；解析失败原样返回。"""
    if not value:
        return ""
    raw = value[:19]
    for f in (DATE_FMT, "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, f).strftime(fmt)
        except ValueError:
            continue
    return value


def month_label(ym: str) -> str:
    """'2026-03' -> '2026 年 3 月'。"""
    try:
        d = datetime.strptime(ym, "%Y-%m")
        return f"{d.year} 年 {d.month} 月"
    except ValueError:
        return ym
