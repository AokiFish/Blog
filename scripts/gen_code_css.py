"""生成 static/css/code.css：Pygments 的亮/暗两套代码高亮配色。

默认主题使用 light 配色，[data-theme="dark"] 下覆盖为 dark 配色，
这样文章正文里的代码块可以跟着站点主题一起切换。
"""
import os

from pygments.formatters import HtmlFormatter
from pygments.styles import get_style_by_name

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE_DIR, "static", "css", "code.css")

LIGHT_STYLE = "default"
DARK_STYLE = "monokai"


def _safe(style: str, fallback: str) -> str:
    try:
        get_style_by_name(style)
        return style
    except Exception:  # noqa: BLE001
        return fallback


def _scoped(css: str, prefix: str) -> str:
    out = []
    for line in css.splitlines():
        line = line.rstrip()
        # 只保留 .highlight 作用域内的规则，避免污染全局 pre / table 样式
        if not line.startswith(".highlight"):
            continue
        out.append(f"{prefix} {line}" if prefix else line)
    return "\n".join(out)


def main() -> None:
    light = HtmlFormatter(style=_safe(LIGHT_STYLE, "default")).get_style_defs(".highlight")
    dark = HtmlFormatter(style=_safe(DARK_STYLE, "monokai")).get_style_defs(".highlight")

    parts = [
        "/* 自动生成：python scripts/gen_code_css.py —— 不要手改 */",
        "",
        "/* 浅色 */",
        _scoped(light, ""),
        "",
        "/* 深色 */",
        _scoped(dark, 'html[data-theme="dark"]'),
        "",
        "/* 代码块基础样式 */",
        ".highlight { background: var(--code-bg); }",
        ".highlight pre { margin: 0; }",
        ".markdown-body .highlight {",
        "  margin: 1.4em 0;",
        "  padding: 16px 18px;",
        "  border: 1px solid var(--border-soft);",
        "  border-radius: 10px;",
        "  overflow-x: auto;",
        "}",
        ".markdown-body .highlight code { background: none; border: 0; padding: 0; font-size: 13.6px; }",
        "",
    ]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"[gen] 已生成 {os.path.relpath(OUT, BASE_DIR)}")


if __name__ == "__main__":
    main()
