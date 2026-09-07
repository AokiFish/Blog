"""管理后台：登录 / 文章列表 / 写文章 / 发布 / 删除 / 重新构建。

访问 /admin/ 进入；首次需输入 .env 里的 ADMIN_TOKEN 作为密码登录（写入 cookie）。
所有写操作以 content/posts/{slug}.md 为源，落库到数据库，并可在后台一键重建静态站。
"""
import hashlib
import hmac
import os
import re

from fasthtml.common import (
    APIRouter, A, Button, Div, Form, H1, H2, Input, Label, P, Span, Td, Textarea,
    Title, NotStr, Tr,
)
from starlette.requests import Request
from starlette.responses import RedirectResponse

from blog.config import ADMIN_ENABLED, ADMIN_TOKEN, POSTS_DIR, SECRET_KEY, SITE_NAME
from blog.core.frontmatter import parse as parse_frontmatter
from blog.core.textutil import now_str, slugify
from posts.repos import all_rows, count_all_rows, delete_post, get_post, save_post, set_status
from blog.services.importer import import_file

router = APIRouter()

# 后台列表每页文章数
ADMIN_PAGE_SIZE = 20


# ----------------------------------------------------------------- 鉴权 ----
def _session_token() -> str:
    return hmac.new(SECRET_KEY.encode(), b"admin-session", hashlib.sha256).hexdigest()


def _authorized(req: Request) -> bool:
    if not ADMIN_ENABLED:
        return False
    return bool(ADMIN_TOKEN) and req.cookies.get("admin_session") == _session_token()


def _deny() -> RedirectResponse:
    return RedirectResponse("/admin/?msg=" + _q("请先登录"), status_code=303)


def _q(text: str) -> str:
    from urllib.parse import quote

    return quote(text)


# --------------------------------------------------------------- 工具 ----
def _post_path(slug: str) -> str:
    os.makedirs(POSTS_DIR, exist_ok=True)
    return os.path.join(POSTS_DIR, f"{slug}.md")


def _dump_md(data: dict) -> str:
    """把文章字段序列化为带 front-matter 的 Markdown 文本。"""
    def fmt(v) -> str:
        if isinstance(v, (list, tuple)):
            inner = ", ".join(str(x).strip() for x in v if str(x).strip())
            return f"[{inner}]"
        return str(v)

    meta_lines = [
        "---",
        f"title: {data.get('title', '')}",
        f"slug: {data.get('slug', '')}",
        f"date: {data.get('date', '')}",
        f"category: {data.get('category', '')}",
        f"tags: {fmt(data.get('tags', []))}",
        f"summary: {data.get('summary', '')}",
        f"status: {data.get('status', 'published')}",
        f"pinned: {str(bool(data.get('pinned'))).lower()}",
        f"cover: {data.get('cover', '')}",
        "---",
        "",
        data.get("body", ""),
    ]
    return "\n".join(meta_lines)


def _write_and_import(slug: str, data: dict) -> None:
    with open(_post_path(slug), "w", encoding="utf-8") as f:
        f.write(_dump_md(data))
    import_file(_post_path(slug))


# ------------------------------------------------------------- 布局 ----
ADMIN_CSS = """
.admin-wrap{max-width:960px;margin:40px auto;padding:0 20px;font-family:system-ui,'PingFang SC','Microsoft YaHei',sans-serif;}
.admin-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;}
.admin-head h1{font-size:22px;margin:0;}
.admin-bar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;}
.btn{border:1px solid var(--border, #ddd);background:var(--card,#fff);color:var(--text,#222);
  padding:8px 14px;border-radius:8px;cursor:pointer;text-decoration:none;font-size:13px;}
.btn-primary{background:#3b82f6;color:#fff;border-color:#3b82f6;}
.btn-danger{background:#ef4444;color:#fff;border-color:#ef4444;}
.btn-sm{padding:4px 10px;font-size:12px;}
.admin-msg{padding:10px 14px;border-radius:8px;margin-bottom:16px;background:#e0f2fe;color:#075985;}
.admin-table{width:100%;border-collapse:collapse;background:var(--card,#fff);border-radius:10px;overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,.08);}
.admin-table th,.admin-table td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--border-soft,#eee);font-size:13px;}
.admin-table th{background:#f8fafc;font-weight:600;}
.tag-draft{color:#b45309;background:#fef3c7;padding:2px 8px;border-radius:6px;font-size:12px;}
.tag-pub{color:#047857;background:#d1fae5;padding:2px 8px;border-radius:6px;font-size:12px;}
.login-box{max-width:360px;margin:80px auto;padding:28px;background:var(--card,#fff);border-radius:12px;
  box-shadow:0 4px 16px rgba(0,0,0,.1);}
.login-box h1{font-size:20px;margin:0 0 18px;text-align:center;}
.field{margin-bottom:14px;display:flex;flex-direction:column;gap:6px;}
.field label{font-size:13px;font-weight:600;}
.field input,.field textarea,.field select{border:1px solid #d1d5db;border-radius:8px;padding:9px 11px;font-size:14px;
  font-family:inherit;background:#fff;color:#111;}
.field textarea{min-height:340px;resize:vertical;line-height:1.6;font-family:ui-monospace,Menlo,Consolas,monospace;}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;}
.editor-wrap{max-width:1000px;margin:30px auto;padding:0 20px;}
.editor-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;}
.hint{font-size:12px;color:#94a3b8;}
.upload-card{border:1px dashed #94a3b8;border-radius:10px;padding:12px 14px;margin-bottom:18px;
  background:var(--card,#fff);}
.upload-card form{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.upload-card input[type=file]{font-size:13px;flex:1;min-width:220px;padding:6px 0;}
.upload-card .hint{width:100%;margin:6px 0 0;flex-basis:100%;}
.admin-pager{display:flex;gap:6px;align-items:center;justify-content:center;
  padding:14px 0 6px;flex-wrap:wrap;}
.admin-pager a,.admin-pager span{min-width:30px;height:30px;line-height:30px;
  text-align:center;padding:0 9px;border:1px solid #d1d5db;border-radius:6px;
  font-size:13px;color:#334155;text-decoration:none;box-sizing:border-box;}
.admin-pager a:hover{border-color:#2563eb;color:#2563eb;}
.admin-pager .cur{background:#2563eb;border-color:#2563eb;color:#fff;font-weight:600;}
.admin-pager .off{color:#cbd5e1;pointer-events:none;}
.admin-pager .dots{border:none;min-width:auto;padding:0 2px;background:transparent;color:#94a3b8;}
.admin-meta{font-size:12px;color:#94a3b8;margin:0 0 10px;}
"""


def _flatten(items):
    """递归展开嵌套的 list/tuple，跳过 None/空串，返回可序列化组件列表。"""
    for it in items:
        if it is None:
            continue
        if isinstance(it, (list, tuple)):
            yield from _flatten(it)
        else:
            yield it


def _admin_page(*body, title: str = "管理后台") -> NotStr:
    return NotStr(
        f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{title} · {SITE_NAME}</title><style>{ADMIN_CSS}</style></head>"
        f"<body>{''.join(str(b) for b in _flatten(body))}</body></html>"
    )


def _admin_pager(page: int, pages: int):
    """后台列表分页条：‹ 页码… ›；单页时返回 None。"""
    if pages <= 1:
        return None

    def _btn(n: int, label: str, cur: bool = False, disabled: bool = False):
        if cur:
            return NotStr(f"<span class='cur'>{label}</span>")
        if disabled:
            return NotStr(f"<span class='off'>{label}</span>")
        return A(label, href=f"/admin/?page={n}")

    # 页码窗口：过多时只保留首/尾/当前及邻页，其余用省略号
    if pages <= 9:
        seq: list[int | None] = list(range(1, pages + 1))
    else:
        seq = []
        prev = 0
        for n in sorted(x for x in {1, pages, page - 1, page, page + 1} if 1 <= x <= pages):
            if n - prev > 1:
                seq.append(None)
            seq.append(n)
            prev = n

    items = [_btn(page - 1, "‹ 上一页", disabled=page <= 1)]
    for n in seq:
        items.append(NotStr("<span class='dots'>…</span>") if n is None else _btn(n, str(n), cur=(n == page)))
    items.append(_btn(page + 1, "下一页 ›", disabled=page >= pages))
    return Div(*items, cls="admin-pager")


def _login_page(msg: str = "") -> NotStr:
    box = Div(
        H1("登录管理后台"),
        P(msg, cls="admin-msg") if msg else None,
        Form(
            Div(
                Label("管理密码（ADMIN_TOKEN）", **{"for": "token"}),
                Input(type="password", name="token", id="token", required=True, placeholder="在 .env 的 ADMIN_TOKEN 中设置"),
                cls="field",
            ),
            Button("登 录", type="submit", cls="btn btn-primary", style="width:100%"),
            method="post",
            action="/admin/login",
        ),
        cls="login-box",
    )
    return _admin_page(box, title="登录")


# ------------------------------------------------------- 路由：登录 ----
@router("/admin/login")
async def login(req: Request):
    if req.method == "GET":
        return _login_page()
    form = dict(await req.form())
    if not ADMIN_ENABLED or not ADMIN_TOKEN or form.get("token") != ADMIN_TOKEN:
        return _login_page("密码错误或未启用管理后台。")
    resp = RedirectResponse("/admin/", status_code=303)
    resp.set_cookie("admin_session", _session_token(), httponly=True, samesite="lax")
    return resp


@router("/admin/logout")
def logout():
    resp = RedirectResponse("/admin/", status_code=303)
    resp.delete_cookie("admin_session")
    return resp


# ------------------------------------------------------- 路由：仪表盘 ----
@router("/admin/")
def dashboard(req: Request):
    if not _authorized(req):
        msg = req.query_params.get("msg", "")
        return _login_page(msg)
    msg = req.query_params.get("msg", "")
    try:
        page = max(1, int(req.query_params.get("page", "1")))
    except ValueError:
        page = 1
    total = count_all_rows()
    pages = max(1, -(-total // ADMIN_PAGE_SIZE))  # ceil(total/20)
    page = min(page, pages)
    posts = all_rows(limit=ADMIN_PAGE_SIZE, offset=(page - 1) * ADMIN_PAGE_SIZE)
    rows = []
    for p in posts:
        status = p.get("status")
        tag = Span("草稿", cls="tag-draft") if status != "published" else Span("已发布", cls="tag-pub")
        actions = [
            A("编辑", href=f"/admin/edit/{p['slug']}/", cls="btn btn-sm"),
            A("查看", href=f"/posts/{p['slug']}/", cls="btn btn-sm", target="_blank"),
        ]
        if status == "published":
            actions.append(A("下架", href=f"/admin/unpublish/{p['slug']}/", cls="btn btn-sm"))
        else:
            actions.append(A("发布", href=f"/admin/publish/{p['slug']}/", cls="btn btn-sm btn-primary"))
        actions.append(A("删除", href=f"/admin/delete/{p['slug']}/", cls="btn btn-sm btn-danger"))
        rows.append(
            Tr(
                Td(A(p["title"], href=f"/admin/edit/{p['slug']}/")),
                Td(p.get("category_name", "未分类")),
                Td(tag),
                Td(str(p.get("views", 0))),
                Td(p.get("published_at", "")[:10]),
                Td(*actions, cls="row-actions"),
            )
        )

    bar = Div(
        A("＋ 新建文章", href="/admin/new/", cls="btn btn-primary"),
        A("↻ 重新构建静态站", href="/admin/rebuild/", cls="btn",
          **{"onclick": "return confirm('将重新生成 build/ 静态站点，确定？')"}),
        A("退出登录", href="/admin/logout/", cls="btn"),
        cls="admin-bar",
    )
    upload_card = Div(
        Form(
            Input(type="file", name="md", id="md-upload",
                  accept=".md,text/markdown", required=True),
            Button("上传并导入", type="submit", cls="btn btn-primary"),
            P("选择本地 .md 文件（含 front-matter：title/date/category/tags/summary/status），"
              "上传后自动解析并入库，同 slug 文章会被覆盖更新。", cls="hint"),
            method="post",
            action="/admin/upload",
            enctype="multipart/form-data",
        ),
        cls="upload-card",
    )
    msg_el = P(msg, cls="admin-msg") if msg else None
    if rows:
        info_el = P(f"共 {total} 篇文章，第 {page} / {pages} 页", cls="admin-meta")
        body = [
            bar, upload_card, msg_el, info_el,
            Div(
                NotStr("<table class='admin-table'><thead><tr>"
                       "<th>标题</th><th>分类</th><th>状态</th><th>阅读</th><th>发布日期</th><th>操作</th>"
                       "</tr></thead><tbody>"),
                *rows,
                NotStr("</tbody></table>"),
            ),
            _admin_pager(page, pages),
        ]
    else:
        body = [bar, upload_card, msg_el, P("还没有文章，点「新建文章」或上传 .md 文件开始吧。")]
    head = Div(H1("管理后台"), cls="admin-head")
    return _admin_page(head, body, title="仪表盘")


# ------------------------------------------------------- 路由：编辑器 ----
def _editor(post: dict | None = None, slug: str = "") -> NotStr:
    p = post or {}
    is_edit = bool(p)
    title = p.get("title", "")
    slug_val = p.get("slug", slug)
    cat = p.get("category_name", "")
    tags = ", ".join(t["name"] for t in p.get("tags", []))
    summary = p.get("summary", "")
    status = p.get("status", "published")
    pinned = bool(p.get("pinned"))
    cover = p.get("cover", "")
    body = p.get("content_md", "")
    date_val = p.get("published_at", "")[:19]

    form = Form(
        Div(
            Div(
                Label("标题", **{"for": "title"}),
                Input(type="text", name="title", id="title", value=title, required=True),
                cls="field",
            ),
            Div(
                Label("slug（URL 标识，留空自动生成）", **{"for": "slug"}),
                Input(type="text", name="slug", id="slug", value=slug_val,
                      **({"disabled": "disabled"} if is_edit else {})),
                cls="field",
            ),
            cls="row2",
        ),
        Div(
            Div(Label("分类", **{"for": "category"}),
                Input(type="text", name="category", id="category", value=cat), cls="field"),
            Div(Label("标签（逗号分隔）", **{"for": "tags"}),
                Input(type="text", name="tags", id="tags", value=tags), cls="field"),
            cls="row2",
        ),
        Div(
            Div(Label("状态", **{"for": "status"}),
                _select("status", [("published", "发布"), ("draft", "草稿")], status), cls="field"),
            Div(Label("发布时间 (YYYY-MM-DD HH:MM:SS)", **{"for": "date"}),
                Input(type="text", name="date", id="date", value=date_val,
                      placeholder="留空取当前时间"), cls="field"),
            Div(Label("封面图 URL", **{"for": "cover"}),
                Input(type="text", name="cover", id="cover", value=cover), cls="field"),
            cls="row3",
        ),
        Div(
            Label("摘要（留空自动截取）", **{"for": "summary"}),
            Textarea(p.get("summary", ""), name="summary", id="summary",
                     style="min-height:70px"),
            cls="field",
        ) if not summary else Div(
            Label("摘要（留空自动截取）", **{"for": "summary"}),
            Textarea(summary, name="summary", id="summary", style="min-height:70px"),
            cls="field",
        ),
        Div(
            Label("正文（Markdown）", **{"for": "body"}),
            Textarea(body, name="body", id="body"),
            P("支持 Markdown / 代码高亮 / 提示块 / 任务列表。", cls="hint"),
            cls="field",
        ),
        Div(
            Label(Input(type="checkbox", name="pinned", value="1",
                        **({"checked": "checked"} if pinned else {})),
                  " 置顶文章", style="display:flex;gap:6px;align-items:center;font-weight:600;"),
            cls="field",
        ),
        Div(
            Button("保存", type="submit", cls="btn btn-primary"),
            A("取消", href="/admin/", cls="btn"),
            style="display:flex;gap:10px;",
        ),
        method="post",
        action="/admin/save",
    )
    head = Div(
        H1("编辑文章" if is_edit else "新建文章"),
        A("← 返回列表", href="/admin/", cls="btn"),
        cls="editor-head",
    )
    return _admin_page(head, Div(form, cls="editor-wrap"), title="编辑器")


def _select(name: str, options: list[tuple[str, str]], current: str):
    from fasthtml.common import Option, Select

    return Select(
        *[Option(label, value=val, **({"selected": "selected"} if val == current else {})) for val, label in options],
        name=name, id=name,
    )


@router("/admin/new/")
def new_article(req: Request):
    if not _authorized(req):
        return _deny()
    return _editor()


@router("/admin/edit/{slug}/")
def edit_article(req: Request, slug: str):
    if not _authorized(req):
        return _deny()
    post = get_post(slug)
    if not post:
        return RedirectResponse("/admin/?msg=" + _q("文章不存在"), status_code=303)
    return _editor(post)


# ------------------------------------------------------- 路由：保存 ----
@router("/admin/save")
async def save(req: Request):
    if not _authorized(req):
        return _deny()
    form = dict(await req.form())
    title = (form.get("title") or "").strip()
    if not title:
        return _editor(msg="标题不能为空")
    raw_slug = (form.get("slug") or "").strip()
    slug = slugify(raw_slug, fallback=slugify(title))
    # 编辑时 slug 由隐藏/禁用字段提供，这里直接信任原 slug
    is_edit = bool(raw_slug) and get_post(raw_slug)
    if is_edit:
        slug = raw_slug

    body = form.get("body") or ""
    date_val = (form.get("date") or "").strip() or now_str()[:19]
    data = {
        "title": title,
        "slug": slug,
        "category": (form.get("category") or "未分类").strip(),
        "tags": [t.strip() for t in (form.get("tags") or "").split(",") if t.strip()],
        "summary": (form.get("summary") or "").strip(),
        "status": (form.get("status") or "published").lower(),
        "pinned": form.get("pinned") == "1",
        "cover": (form.get("cover") or "").strip(),
        "date": date_val,
        "body": body,
    }
    try:
        _write_and_import(slug, data)
    except Exception as e:  # noqa: BLE001
        return _editor(msg=f"保存失败：{e!r}")
    return RedirectResponse(f"/admin/?msg=" + _q(f"已保存《{title}》"), status_code=303)


# ------------------------------------------------------- 路由：上传 .md ----
@router("/admin/upload")
async def upload_md(req: Request):
    """接收本地 .md 文件：解析 front-matter 取 slug → 落盘 content/posts/ → 导入数据库。"""
    if not _authorized(req):
        return _deny()
    form = await req.form()
    up = form.get("md")
    if up is None:
        return RedirectResponse("/admin/?msg=" + _q("请选择要上传的 .md 文件"), status_code=303)
    filename = getattr(up, "filename", "") or "post.md"
    if not filename.lower().endswith(".md"):
        return RedirectResponse("/admin/?msg=" + _q("只支持 .md 文件"), status_code=303)
    try:
        raw = await up.read()
    except Exception:  # noqa: BLE001
        raw = up.file.read() if hasattr(up, "file") else b""
    if not raw:
        return RedirectResponse("/admin/?msg=" + _q("文件内容为空"), status_code=303)

    # 编码探测：优先 utf-8（容忍 BOM），失败再试 gbk
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return RedirectResponse("/admin/?msg=" + _q("无法识别文件编码（请用 UTF-8 保存）"), status_code=303)

    meta, _body = parse_frontmatter(text)
    stem = re.sub(r"^\d{1,3}\s*[-_]\s*", "", os.path.splitext(os.path.basename(filename))[0])
    slug = (meta.get("slug") or "").strip() or slugify(meta.get("title") or stem)
    existed = bool(get_post(slug))
    os.makedirs(POSTS_DIR, exist_ok=True)
    path = os.path.join(POSTS_DIR, f"{slug}.md")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        post = import_file(path) or {}
    except Exception as e:  # noqa: BLE001
        return RedirectResponse("/admin/?msg=" + _q(f"导入失败：{e!r}"), status_code=303)
    title = post.get("title") or meta.get("title") or slug
    tip = "已覆盖更新" if existed else "已上传并导入"
    return RedirectResponse(f"/admin/?msg=" + _q(f"{tip}《{title}》（{filename}）"), status_code=303)


# ------------------------------------------------------- 路由：发布/下架/删除 ----
@router("/admin/publish/{slug}/")
def publish(req: Request, slug: str):
    if not _authorized(req):
        return _deny()
    post = get_post(slug)
    if post:
        post["status"] = "published"
        _write_and_import(slug, _post_to_data(post))
    return RedirectResponse("/admin/?msg=" + _q(f"已发布《{post['title'] if post else slug}》"), status_code=303)


@router("/admin/unpublish/{slug}/")
def unpublish(req: Request, slug: str):
    if not _authorized(req):
        return _deny()
    post = get_post(slug)
    if post:
        post["status"] = "draft"
        _write_and_import(slug, _post_to_data(post))
    return RedirectResponse("/admin/?msg=" + _q("已下架"), status_code=303)


@router("/admin/delete/{slug}/")
def delete_article(req: Request, slug: str):
    if not _authorized(req):
        return _deny()
    delete_post(slug)
    path = _post_path(slug)
    file_removed = True
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            # 个别环境（如沙箱/只读盘）禁止删除，DB 已移除，提示用户手动清理即可
            file_removed = False
    if file_removed:
        return RedirectResponse("/admin/?msg=" + _q(f"已删除《{slug}》"), status_code=303)
    return RedirectResponse(
        "/admin/?msg=" + _q(f"已从列表删除《{slug}》，但源文件 {os.path.basename(path)} 未能自动移除，请手动清理。"),
        status_code=303,
    )


def _post_to_data(post: dict) -> dict:
    return {
        "title": post.get("title", ""),
        "slug": post.get("slug", ""),
        "category": post.get("category_name", "未分类"),
        "tags": [t["name"] for t in post.get("tags", [])],
        "summary": post.get("summary", ""),
        "status": post.get("status", "published"),
        "pinned": bool(post.get("pinned")),
        "cover": post.get("cover", ""),
        "date": (post.get("published_at") or now_str())[:19],
        "body": post.get("content_md", ""),
    }


# ------------------------------------------------------- 路由：重建静态站 ----
@router("/admin/rebuild/")
def rebuild(req: Request):
    if not _authorized(req):
        return _deny()
    try:
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "build_static", os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "build_static.py")
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["build_static"] = mod
        spec.loader.exec_module(mod)
        n = mod.build()
        return RedirectResponse("/admin/?msg=" + _q(f"已重建静态站，生成 {int(n)} 个页面"), status_code=303)
    except Exception as e:  # noqa: BLE001
        return RedirectResponse("/admin/?msg=" + _q(f"重建失败：{e!r}"), status_code=303)
