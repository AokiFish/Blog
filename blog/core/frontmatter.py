"""轻量 front-matter 解析（不引入 YAML 依赖）。

支持：
    ---
    title: 文章标题
    date: 2026-03-05 09:00:00
    category: Python
    tags: [Python, Web]
    summary: 一句话摘要
    pinned: true
    ---
"""
import re

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.S)


def _split_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [x.strip().strip("'\"") for x in value.split(",") if x.strip()]


def parse(text: str) -> tuple[dict, str]:
    """返回 (元数据 dict, 正文)。没有 front-matter 时元数据为空 dict。"""
    if not text:
        return {}, ""
    m = FM_RE.match(text.lstrip("\ufeff"))
    if not m:
        return {}, text
    meta: dict = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if not value:
            continue
        if key in ("tags", "keywords"):
            meta[key] = _split_list(value)
        elif value.lower() in ("true", "false"):
            meta[key] = value.lower() == "true"
        else:
            meta[key] = value
    return meta, text[m.end():]
