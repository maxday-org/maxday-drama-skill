<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/maxday-icon.svg" />
    <source media="(prefers-color-scheme: light)" srcset="assets/maxday-icon-dark.svg" />
    <img src="assets/maxday-icon-dark.svg" width="96" height="96" alt="MaxDay" />
  </picture><br/>
  <strong>maxday-drama-skill</strong><br/><br/>
  <strong>简体中文</strong> | <a href="README_EN.md">English</a> | <a href="README_TW.md">繁體中文</a> | <a href="README_JA.md">日本語</a>
</p>
<br/>

## 一行指令，让 MaxDay 进入你的 Agent 工作流

### 通过 AI Agent 安装（推荐）

将下面这段话直接发给你的 AI 助手（Codex CLI / App、Claude Code、Kimi Code/Claw、MiniMax Agent、Trae 等），它会自动帮你完成安装和初始化。

**提示词：**
> 请帮我安装 maxday-drama-skill：`https://www.maxday.ai/maxday-drama-skill.zip`

### 手动安装

在终端执行：
```bash
npx skills add maxday-org/maxday-drama-skill
```
环境要求：Python 3.8+，无需安装额外依赖。
首次使用时，Agent 会引导你通过邮箱验证码登录 MaxDay。

## 让每个 AI Agent 完美驾驭 MaxDay

你的 AI Agent 已经很会想创意、写脚本、拆分镜、改 prompt，但它还缺少一个真正进入创作平台的入口。

maxday-drama-skill 就是这个入口。装上之后，Agent 不再停留在"给你一段建议"或"让你复制一段 prompt"，而是可以直接在 MaxDay 中创建项目、上传剧本、管理素材、批量生成图片和视频、追踪任务进度、下载生成结果。

以前是你手动把想法搬进 MaxDay；现在可以通过 Agent 直接把创作过程落到 MaxDay 里。你只需要**提出方向、确认动作、继续创作。**

## 能做什么

| 你想要 | Agent 通过 Skill 可以做什么 |
|---|---|
| 做一部短剧 | 创建项目、上传剧本、提取角色/场景、批量生图、批量生视频、下载成片 |
| 批量生成角色图 | 查询模型价格、循环提交生图任务、追踪进度、批量下载结果 |
| 批量生成视频 | 上传参考图/音频/视频、循环提交生视频任务、轮询状态、下载 |
| 上传剧本并提取资产 | 上传剧本文件、触发 AI Agent 解析、查询提取任务状态 |
| 管理项目素材 | 创建文件夹、批量上传图片/视频/音频、查看资源、删除和恢复 |
| 项目内快速出图/出视频 | 在项目中创建任务、批量生成并下载 |
| 追踪生成进度 | 查询项目、任务状态、定位失败任务 |
| 查看消耗和账务 | 查看余额、AI 消耗记录、交易历史、微信充值 |
| 管理组织和钱包 | 查看组织、成员、钱包汇总、钱包流水、转账 |

## 可以直接这样用

下面这些是你在登录 MaxDay 后，可以直接发给 Agent 的完整任务示例。

### 1. 短剧批量制作

```
用 maxday-drama，制作一个短剧项目，项目叫"都市暗恋"，剧本在 ./script.docx。

请帮我：
1. 在 MaxDay 创建一个新项目，画幅 9:16，风格设为"电影感真人"；
2. 上传剧本并提取所有角色、场景和道具资产；
3. 等资产提取完成后，给每个主角生成一张竖版角色主视觉；
4. 然后给前 3 个场景各生成一段 5 秒开场视频；
5. 所有生成完成后，把结果下载到 ~/Documents/dramas/都市暗恋/。
```

### 2. 批量生图

```
用 maxday-drama，生成 5 张图。

要求：
- 项目使用/创建 “霓虹概念图项目”
- 画幅 9:16
- 风格 1：赛博朋克霓虹灯光
- 风格 2：柔光自然写实
- 用最便宜的可用模型
- 提示词：赛博朋克城市雨夜，霓虹灯倒映在湿润街道上，电影感构图，细节丰富
```

### 3. 单条视频生成

```
用 maxday-drama，生成一个视频。

要求：
- 项目使用/创建 “霓虹短视频项目”
- 模型用 seedance2-pro-vvip
- 画幅 9:16
- 时长 5 秒
- 清晰度 480p
- 提示词：赛博朋克城市雨夜，霓虹灯倒映在湿润街道上，镜头缓慢推进，电影感光影
```

### 4. 批量角色图生成

```
用 maxday-drama，给当前项目的 8 个角色各生成 2 张不同风格的肖像图。

要求：
- 项目使用/创建 “霓虹角色肖像集”
- 画幅 9:16
- 风格 1：赛博朋克霓虹灯光
- 风格 2：柔光自然写实
- 用最便宜的可用模型
- 全部生成后下载到桌面的 characters 文件夹
```

### 5. 批量视频生成

```
用 maxday-drama，把 ./storyboard/ 目录下的 10 张分镜图批量生成视频。

请帮我：
1. 项目使用/创建 “分镜动态视频集”；
2. 把这些图片全部上传到该项目的 image 文件夹；
3. 用每张图作为起始帧，各生成一段 5 秒的视频；
4. prompt 统一用"cinematic camera movement, dramatic lighting"；
5. 生成完成后批量下载到 ./output/videos/。
```

### 6. 项目内快速出图

```
用 maxday-drama，快速生成 4 张概念图。

请帮我：
1. 项目使用/创建 “概念图探索集”；
2. 在该项目中生成 4 张概念图，主题分别是：
   - 赛博朋克城市街景，雨夜，霓虹反射
   - 古风庭院，月下独酌
   - 太空站内部，失重漂浮的宇航员
   - 海底古城遗迹，光线穿透水面
3. 全部生完后下载到桌面。
```

### 7. 查看消耗和充值

```
用 maxday-drama，帮我查一下：
1. 当前账户余额；
2. 最近的 AI 消耗记录，按项目汇总；
3. 如果余额低于 10 元，帮我创建一个 50 元的微信充值订单。
```

### 8. 组织钱包管理

```
用 maxday-drama，帮我管理一下组织钱包：
1. 查看我的组织列表；
2. 看一下主组织的钱包余额和最近流水；
3. 给成员 alice@example.com 转 100 积分。
```

## 安全说明

所有消耗积分、删除数据、创建支付单、转账或触发 AI 生成的操作，Agent 都会在执行前向你确认。当你明确表达了批量操作的意图时（比如"帮我批量生成"），Agent 会自动执行而不逐条询问。
