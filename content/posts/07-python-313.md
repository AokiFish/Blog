---
slug: python-313
title: Python 3.13 里那些真正影响日常的小改动
date: 2026-01-22 11:00:00
category: Python
tags: [Python, 新特性]
summary: 不去谈 JIT 和自由线程这些大新闻，只挑几个我每天写代码时确实会用到的变化。
---

每次 Python 发新版，公众号都在讲 JIT、讲 free-threading。这些当然重要，但对日常工作流的改变至少要等一两年。反而是一些不起眼的小改动，每天都在省我的时间。

## 错误提示会直接给你建议

以前拼错模块里的属性，解释器只会说「没有这个属性」。现在它会猜：

```python
>>> import http
>>> http.client
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: module 'http' has no attribute 'client'. Did you mean: 'from http import client'?
```

对新手这是救命的，对老手则是少一次查文档。

## `TypeError` 会指出具体是哪个参数

```python
>>> def greet(name, greeting="你好"):
...     return f"{greeting}, {name}"
>>> greet("world", greeting=123, nickname="x")
TypeError: greet() got an unexpected keyword argument 'nickname'. Did you mean 'greeting'?
```

参数多的函数调用出错时，这条提示能省掉一轮阅读函数签名。

## `copy.replace()`：改一个字段的不可变对象

以前想改 `namedtuple` 的某个字段，要么转 dict 再转回来，要么手动构造。现在标准库给了统一入口：

```python
from copy import replace

@dataclass(frozen=True)
class Config:
    host: str
    port: int
    debug: bool

base = Config("localhost", 8000, False)
prod = replace(base, host="0.0.0.0", debug=False)
```

它对 `namedtuple`、`dataclass`、`functools.partial` 等一众类型都有效，不用再记每种类型各自的 `_replace` / `dataclasses.replace`。

## 交互式解释器终于能用了

3.13 的 REPL 默认启用了新 shell，几个立竿见影的改进：

- 多行编辑：写函数时可以上下移动光标修改任意一行
- 直接按 F1 进帮助浏览器
- 粘贴代码不会自动执行（以前粘一段带空行的代码经常出错）
- 历史记录持久化到 `~/.python_history`

| 操作 | 快捷键 |
| --- | --- |
| 打开帮助 | `F1` |
| 清屏 | `Ctrl+L` |
| 粘贴模式 | `F3` |
| 退出 | `Ctrl+D` |

!!! note "不习惯可以退回旧版"
    设置 `PYTHON_BASIC_REPL=1` 就能用回原来的 REPL。

## `pathlib` 也能匹配大小写了

```python
from pathlib import Path

Path(".").glob("*.py", case_sensitive=False)   # 新增参数
```

在 Windows 上这个参数默认生效（因为文件系统本身不区分大小写），在 Linux/macOS 上可以显式打开。跨平台脚本少了一个坑。

## 关于 JIT 和自由线程

这两个都还是实验特性：

```bash
python -X gil=0 script.py          # 自由线程构建
PYTHON_JIT=1 python script.py      # 复制-补丁 JIT
```

!!! warning "别急着在生产环境用"
    实测下来，JIT 在纯计算密集的任务上有 5%~15% 的提升，但 Web 应用这类 IO 密集场景几乎没有变化，个别情况还因为编译开销略微变慢。自由线程则要求你用的所有 C 扩展都重新编译，生态还没跟上。

我的建议是：**日常开发照常用稳定特性，把实验特性当成一个可以随手开关的开关**，等生态准备好再切。Python 的版本升级从来不是用新语法，而是这些让你每天少敲几十次键的细节。
