"""分页器：根据总数与每页条数算出页码信息。"""


class Pager:
    def __init__(self, total: int, page: int = 1, size: int = 10, window: int = 2):
        self.total = max(0, int(total))
        self.size = max(1, int(size))
        self.pages = max(1, (self.total + self.size - 1) // self.size)
        self.page = min(max(1, int(page)), self.pages)
        self.offset = (self.page - 1) * self.size
        self.window = window

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def prev_page(self) -> int:
        return max(1, self.page - 1)

    @property
    def next_page(self) -> int:
        return min(self.pages, self.page + 1)

    def page_numbers(self) -> list[int]:
        """首页/尾页 + 当前页附近 window 页，中间用 0 表示省略号。"""
        pages = set([1, self.pages])
        for p in range(self.page - self.window, self.page + self.window + 1):
            if 1 <= p <= self.pages:
                pages.add(p)
        ordered = sorted(pages)
        out, last = [], 0
        for p in ordered:
            if last and p - last > 1:
                out.append(0)
            out.append(p)
            last = p
        return out

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"<Pager page={self.page}/{self.pages} total={self.total}>"
