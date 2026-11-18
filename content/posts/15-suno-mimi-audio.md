---
slug: suno-mimi-audio
title: Suno 音频本地保存：suno-mimi-audio 扩展使用教程
date: 2026-11-18 10:23:00
category: 工具
tags: [Suno, Chrome 扩展, 音频, 工具]
summary: Suno 上刷到喜欢的歌，找不到下载按钮？用开源扩展 suno-mimi-audio，只要在页面播放过就能抓成音频文件存到本地。装好三步，边听边存。
cover: /static/img/suno-capture-save.jpg
---

在 Suno 上刷到喜欢的歌，想存下来却发现没有下载按钮？这里介绍一个开源 Chrome 扩展 **suno-mimi-audio**：只要在页面上播放过，它就能把音频抓成文件，保存到你本地。

## 它能做什么

- **开源免费**：[GitHub 仓库](https://github.com/AokiFish/suno-mimi-audio) MIT 协议，免费使用。
- **本地处理**：整个捕获过程都在你自己的浏览器里完成，不上传账号信息。
- **即播即存**：不用整首听完，播放过就能抓。

仓库 README 里有完整的实现说明：

![suno-mimi-audio 仓库 README](/static/img/suno-repo-readme.jpg)

## 安装

### 1. 下载源码

打开 [GitHub 仓库](https://github.com/AokiFish/suno-mimi-audio) 页面，点 `Code` → `Download ZIP`。下载到「下载」目录：

![下载目录里的 ZIP 压缩包](/static/img/suno-download-zip.jpg)

解压到一个**固定文件夹**——后面加载扩展一直要用这个目录，别随便删。

### 2. 加载扩展

1. 地址栏输入 `chrome://extensions`
2. 右上角打开「开发者模式」
3. 点「加载已解压的扩展程序」
4. 选中刚才解压出来的文件夹，插件即装好

装好后会在扩展列表里看到 `Mimi Audio`：

![Chrome 扩展管理页，Mimi Audio 已加载](/static/img/suno-load-extension.jpg)

## 使用

### 1. 开启捕获

打开 Suno 页面，**刷新一次**，确认插件面板里 **Capture is on** 处于开启状态。

### 2. 播放歌曲

随便点一首歌播放，不用整首听完。播放过程中插件在后台自动捕获音频。列表里出现这首歌、状态变成 **Ready to save**，就说明抓到了。

### 3. 保存文件

- **单曲**：点 `Save audio` 直接保存。
- **多首**：点 `Download all` 一次性全部下载。
- **清理列表**：不需要的条目点 `Clear all` 清空。

![插件面板：Capture 开关、Ready to save 状态与 Save audio 按钮](/static/img/suno-capture-save.jpg)

捕获多首时，面板顶部会显示 `Download all (N)`：

![捕获多首歌曲，Download all 批量下载](/static/img/suno-download-all.jpg)

## 文件在哪

保存下来的音频文件在本机「下载」目录里。注意：关闭或刷新 Suno 标签页**之前先保存**，否则捕获列表会丢失。

## 注意

- 仅供技术学习和研究使用。
- 请遵守平台服务条款和版权规定。
- 觉得有用，去 [GitHub 仓库](https://github.com/AokiFish/suno-mimi-audio) 点个星。
