---
slug: sqlite-scale
title: SQLite 不是玩具：单文件数据库能撑到什么规模
date: 2026-08-18 20:10:00
category: 数据库
tags: [SQLite, 数据库, 性能]
summary: 我把博客从 PostgreSQL 迁到 SQLite 之后，页面反而更快了。这篇记录几个关键配置，以及什么时候你不该这么做。
cover: /static/img/cover-sqlite.svg
---

「SQLite 只适合做原型」这句话我信了很多年，直到我看见一个日 PV 三十万的站点跑在 SQLite 上，而且跑得很稳。

## 关键不是引擎，是模式

SQLite 默认配置偏向安全与省电，直接拿来跑 Web 会踩坑。真正需要改的只有三个参数：

```sql
PRAGMA journal_mode = WAL;      -- 读写不互相阻塞
PRAGMA synchronous = NORMAL;    -- WAL 下的性价比最优解
PRAGMA busy_timeout = 5000;     -- 遇到写锁等 5 秒而不是立刻报错
```

`journal_mode = WAL` 是分水岭。默认的 rollback journal 模式下，写操作会锁住整库，读请求全部排队；切到 WAL 之后，读者完全不阻塞写者，这对博客这种「写一次读一万次」的场景几乎是量身定制。

## 一组实测数据

在我这台机器上，5000 篇文章、每张表都建了索引的情况下：

| 操作 | 平均耗时 |
| --- | --- |
| 首页列表查询（8 条 + count） | 0.42 ms |
| 按标签过滤 | 0.61 ms |
| 全文 LIKE 搜索 | 3.8 ms |
| 单篇详情 | 0.19 ms |

3.8 毫秒的 LIKE 搜索是最差的一项，但注意这是**没有建任何全文索引**的结果。真要做搜索，加一张 FTS5 虚拟表就能把它压到亚毫秒级：

```sql
CREATE VIRTUAL TABLE posts_fts USING fts5(title, summary, body, content='posts');
```

## 什么时候别用 SQLite

!!! warning "三条硬边界"
    1. **多机部署**。SQLite 的文件锁只在单机有效，一旦你的应用跑在两个容器里并且都要写，就必须换 Postgres。
    2. **高并发写入**。WAL 只有一个写者，每秒几百次以上的持续写入会开始排队。
    3. **需要细粒度权限**。SQLite 没有用户体系，谁拿到文件谁就是 root。

博客、内部看板、小型 SaaS 的元数据、边缘节点上的缓存——这些场景里 SQLite 不仅够用，而且因为没有网络往返，通常比同机的 Postgres 更快。

## 备份比你想的简单

因为整个数据库就是一个文件，备份可以退化成一行 shell：

```bash
sqlite3 blog.db ".backup '/backup/blog-$(date +%F).db'"
```

`.backup` 是官方推荐的在线备份方式，不需要停服，也不会破坏事务一致性。对比一下 `pg_dump` 加定时任务的组合，这种简单本身就是一种可靠性。
