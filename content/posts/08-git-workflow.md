---
slug: git-workflow
title: 一个人的 Git 工作流：够用就好
date: 2025-12-15 08:40:00
category: 工具
tags: [Git, 工具, 效率]
summary: 没有团队协作的约束之后，我反而更需要一套纪律。这是我用了一年多、几乎没有出过事故的流程。
---

团队协作需要 Git 规范，这很好理解。但一个人写代码时，很多人会退化成「`git commit -m update` 然后推上去」，直到某天需要回滚却找不到是哪个提交引入的问题。

我现在的流程很简单，只有四条规则。

## 规则一：主干只有一个，且永远可部署

`main` 分支上的每个提交都应该能正常运行。功能没写完怎么办？用开关，或者干脆别提交。

这条规则最大的收益是心理上的：**任何时候我都能放心地切回 main 去看代码**，不用先猜「这个提交是不是半成品」。

## 规则二：commit message 只回答「为什么」

我不写「修改了 bug」这种信息——代码本身已经说了改了什么。message 应该记录代码里看不出来的东西：

```bash
git commit -m "修复归档页月份排序错误

SQLite 的 substr 返回文本，'2026-9' 会排在 '2026-10' 后面，
改成在 Python 侧补零后再分组。"
```

第一段是摘要，空一行之后写原因。半年后我翻 log 时，真正有价值的永远是那段原因。

!!! note "一个偷懒技巧"
    如果实在想不出「为什么」，说明这个改动可能不值得单独成一个提交——合并到相邻的提交里。

## 规则三：用 `fixup` 保持历史干净

发现上一个提交漏了个文件，不要新建「补充文件」提交：

```bash
git add .
git commit --fixup HEAD
git rebase -i --autosquash main
```

`--autosquash` 会自动把 fixup 提交挪到对应提交下面并合并。历史里就不会留下「修改一下」「再改一次」这种噪音。

## 规则四：重要节点打 tag

博客每次内容结构变化、依赖升级前，我会打个 tag：

```bash
git tag -a v0.3-before-static-export -m "静态导出改造前的最后一个版本"
git push --tags
```

回滚时只需要：

```bash
git checkout v0.3-before-static-export
```

比在几十个提交里翻哈希值快得多。

## 几个高频命令

| 目的 | 命令 |
| --- | --- |
| 看看改了什么（ staged 区） | `git diff --cached` |
| 撤销最后一次提交但保留改动 | `git reset --soft HEAD~1` |
| 临时切走又不想提交 | `git stash push -u` |
| 找回误删的提交 | `git reflog` |
| 只看某个文件的历史 | `git log -p -- path/to/file` |

`git reflog` 值得单独说一句：只要提交过（哪怕后来 reset 掉了），它都记得。有次我误操作 `reset --hard` 丢了两天的改动，就是靠 reflog 找回来的。

## 关于 `.gitignore`

个人项目也值得认真写。我习惯先加一个最小集：

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
.env
data/*.db
dist/
.DS_Store
```

`.env` 和数据库文件**必须在第一次提交之前**就写进去。一旦推上去过，再删也只是删掉了未来，历史里还在。
