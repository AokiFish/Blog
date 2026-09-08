---
slug: cloudflare-r2-static-blog
title: 用 Cloudflare R2 托管静态博客：比 S3 更省钱的方案
date: 2026-09-04 10:15:00
category: Web
tags: [Cloudflare, R2, 静态站点, 部署]
summary: S3 的出站流量费用让人头疼，R2 零 egress 费用是个更好的选择。记录从 S3 迁移到 R2 的全过程。
cover: /static/img/cover-pages.svg
---

把静态博客托管在对象存储上是最常见的方案，但 S3 的出站流量费用（$0.09/GB）在访问量上来之后会很明显。Cloudflare R2 的卖点就是**零 egress 费用**，这对博客这种读多写少的场景很有吸引力。

## 为什么选 R2

| 费用项 | S3 | R2 |
| --- | --- | --- |
| 存储 | $0.023/GB/月 | $0.015/GB/月 |
| 出站流量 | $0.09/GB | **免费** |
| API 请求 | $0.0004/1000 次 | $0.36/100 万次 |

博客的流量特征决定了 R2 更划算：一次构建生成几百个 HTML 文件，用户访问时主要消耗的是出站流量，而这部分 R2 免费。

## 创建 R2 Bucket

```bash
# 安装 wrangler
npm install -g wrangler

# 登录
wrangler login

# 创建 bucket
wrangler r2 bucket create blog-static
```

## 配置静态网站托管

R2 支持直接托管静态网站，和 S3 类似：

```bash
# 设置索引文档
wrangler r2 bucket website set blog-static --index-document index.html

# 设置 404 文档
wrangler r2 bucket website set blog-static --error-document 404.html
```

## 部署静态文件

用 `r2-sync` 或者直接用 `aws-cli` 配合 R2 的 S3 兼容接口：

```bash
# 用 aws-cli 部署（需要配置 R2 的 Access Key）
aws s3 sync ./build s3://blog-static \
  --endpoint-url https://<account-id>.r2.cloudflarestorage.com
```

## 绑定自定义域名

R2 静态站点会给你一个 `*.r2.dev` 的默认域名，比如 `blog-static.r2.dev`。要绑定自定义域名：

1. 在 Cloudflare DNS 添加 CNAME：
   ```
   blog  CNAME  blog-static.r2.dev
   ```
2. 在 R2 bucket 设置里绑定域名

## 配合 Cloudflare Pages 的替代方案

如果你已经在用 Pages，其实不需要 R2。Pages 自带 CDN 和自定义域名支持，而且构建流程更简单。R2 更适合：

- 已经有现成的静态文件需要托管
- 需要 S3 兼容 API 供其他服务访问
- 不想被 Pages 的构建流程绑定

## 迁移经验

从 S3 迁移到 R2 几乎零成本，因为接口兼容。唯一需要注意的是：

- R2 没有 S3 的「存储类别」（标准/低频/归档），所有对象都是同一级别
- R2 的跨区域复制需要额外配置
- R2 的 API 延迟比 S3 略高，但对博客来说无感知

如果你的博客月访问量在 10 万 PV 以下，R2 的免费额度完全够用，而且没有出站流量焦虑。
