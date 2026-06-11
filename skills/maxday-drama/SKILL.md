---
name: maxday-drama
description: 用于操作 MaxDay AI 平台功能，包括批量项目管理、脚本处理、资产上传、批量生成图片/视频、组织和账单管理。当用户需要批量生成内容、管理MaxDay项目、或进行底层API操作时触发。
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "🎬",
        "requires":
          {
            "bins": ["python3"]
          }
      }
  }
---

# MaxDay Drama 技能

本技能专门用于通过底层的 `agent_skill.py` CLI 脚本，执行 MaxDay 平台的自动化、批量化操作。

Agent 应利用标准的循环控制结构和命令行脚本，直接帮助用户完成大批量的数据上传、处理、生图、生视频等任务。

## 核心功能与使用场景

- **登录与配置**: 初始化本地 token
- **项目管理**: 批量创建、切换、修改项目配置
- **脚本处理**: 上传脚本、提交 Agent 解析任务
- **资产管理**: 批量创建文件夹、批量上传参考图、音频、视频
- **批量生成 (核心)**: 使用循环批量提交图片生成或视频生成任务
- **查询与下载**: 轮询任务状态，批量下载生成结果到本地

## 前置要求

```bash
# 检查是否已登录
python3 {baseDir}/agent_skill.py config --json

# 登录流程 (如未登录)
python3 {baseDir}/agent_skill.py send-code --email user@example.com --json
python3 {baseDir}/agent_skill.py login --email user@example.com --code 123456 --save --json
```

## 批量操作指南

所有的操作都通过 `python3 {baseDir}/agent_skill.py [命令]` 完成。
在执行消耗额度、删除数据等敏感操作时，命令必须带上 `--yes` 参数。
**如果用户已明确表达了批量操作或自动化的意图，Agent 可以自动添加 `--yes` 并执行，无需在每一步或每一批操作前中断询问。图片和视频生成除外，必须先遵守“费用确认硬门槛”。**

### 费用确认硬门槛

对 `image-generate`、`video-generate`、`tools-image-generate` 和 `tools-video-generate`，发起任何生图或生视频请求前，必须向用户展示即将扣除的预计费用，并在用户明确确认后才能继续。

展示内容至少包括：模型名、数量、分辨率、时长或类别等影响价格的参数、单次预计费用、整批预计总费用。费用展示必须遵守“价格显示单位规则”。

面向用户的回复中不要展示 `modelId` 或 `modelPriceId`，包括费用确认、结果总结和普通说明。这两个字段只用于内部解析、CLI 参数和后端请求；需要说明模型时展示模型名即可。

生成命令必须带 `--estimated-price ESTIMATED_PRICE` 和 `--yes`。其中 `--estimated-price` 表示已经展示给用户并获得确认的预计总费用；`--yes` 只表示用户已确认这次展示的费用和生产操作，不得仅凭用户有批量生成意图就自动添加。

价格参数必须保留接口返回或计算得到的浮点数。传给 CLI 的 `--estimated-price` 和传给后端的 `estimatedPrice` 都使用美元浮点数；不要把价格四舍五入或转换为整数，也不要使用人民币换算后的展示值提交给后端。

批量生成时，可以先汇总整批任务的预计总费用，展示一次并获得用户确认；确认后再循环执行命令。若任一任务价格无法计算、为未知、或模型/价格 ID 为 `[0, 0]`，不要发起该批生成命令。

### 价格显示单位规则

所有展示给用户的价格都必须带单位。当前只允许展示两种单位：`人民币` 和 `美金`。所有接口返回的价格单位均视为美元，不要把接口返回的美元数值直接标成人民币。

根据用户使用的语言选择展示单位：中文用户显示为人民币；非中文用户显示为美金。中文包括简体中文、繁体中文，以及用户用中文提问或要求中文回复的场景。

人民币展示使用固定汇率换算：人民币 = 美金 * 7。非中文用户的美金展示直接使用接口返回或推导出的美元数值。换算只影响给用户看的文案；传给生成命令的 `--estimated-price ESTIMATED_PRICE` 仍使用接口返回或按接口价格推导出的美元数值。

### 图片生成前置硬门槛

对 `image-generate` 和 `tools-image-generate`，发起任何生图请求前，必须先运行 `model-prices --json` 并从返回的 `modelPriceList` 推导 `--model-id` 与 `--model-price-id`。不要先提交一次生图请求来试探参数。

推导规则：

1. 在 `modelPriceList` 中查找 `displayName` 等于用户选择的模型名、且 `category` 等于 `image` 的模型项。
2. 如果该模型项存在 `uniformPrice`，使用 `--model-id <modelItem.id>` 与 `--model-price-id 0`；预估价格为 `uniformPrice * count`。
3. 如果没有模型级 `uniformPrice`，但 `prices` 非空，优先选择 `resolution` 等于本次生图分辨率的价格项；找不到匹配分辨率时使用 `prices[0]`。使用 `--model-id <modelItem.id>` 与 `--model-price-id <price.id>`；预估价格为 `(price.uniformPrice || price.price) * count`。
4. 如果找不到可用模型项或价格项，视为价格 `0`、ID 为 `[0, 0]`，不要发起实际生图命令，先提示用户模型或分辨率不可用。

禁止的兜底路径：

- 不要用 `model-price` 查询来替代 `model-prices` 解析生图模型 ID；`model-price` 不是按独立工具生图模型名反查 ID 的入口。
- `--model` 仅为兼容字段，不能依赖后端用 `--model` 解析价格；生图时仍必须传入已解析的 `--model-id` 和 `--model-price-id`。
- 遇到 `Invalid parameter`、`价格未定义`、`Not Found` 时，停止继续猜字段或换接口重试；重新执行 `model-prices --json`，按上面的规则定位模型和价格项。

### 视频生成前置硬门槛

对 `video-generate` 和 `tools-video-generate`，发起任何生视频请求前，必须先运行 `model-prices --json` 并从返回的 `modelPriceList` 推导 `--model-id` 与 `--model-price-id`。不要先提交一次生视频请求来试探参数。

视频模型查找规则：

1. 在 `modelPriceList` 中查找 `displayName` 等于用户选择的模型名、且 `category` 等于本次视频生成类别 `category` 的模型项。项目素材区通常对应 `--type video`；如果价格表里有更细的分类，以 `model-prices --json` 返回的 `category` 为准。
2. 如果 `typeof modelItem.uniformPrice === "number"`，使用 `--model-id <modelItem.id>` 与 `--model-price-id 0`；预估价格为 `uniformPrice * count`。
3. 如果存在 `uniformFormula`，使用 `--model-id <modelItem.id>` 与 `--model-price-id 0`；用公式计算 `ESTIMATED_PRICE`，项目素材区 `video-generate` 需要同时传 `--estimated-price ESTIMATED_PRICE`。
4. `uniformFormula` 的变量按前端规则提供：`videoCount = totalDuration > 0 ? 1 : 0`，`inputDuration = totalDuration || 0`，`duration = Number(duration || 0)`，`aspectRatio = aspectRatio || "16:9"`，`resolution = resolution || "720p"`，`upscaleFactor = Number(upscaleFactor || 0)`，`fps = Number(fps || 0)`。
5. 如果没有模型级统一价格或公式，但 `prices` 非空，先找 `resolution` 与 `duration` 同时匹配的价格项；找不到再按 `duration` 匹配；再找 `resolution` 匹配；最后使用 `prices[0]`。使用 `--model-id <modelItem.id>` 与 `--model-price-id <price.id>`；预估价格为 `(price.uniformPrice || price.price) * count`。
6. 如果找不到可用模型项或价格项，视为价格 `0`、ID 为 `[0, 0]`，不要发起实际生视频命令，先提示用户模型、类别、时长或分辨率不可用。

视频接口同样不要用 `model-price` 查询替代 `model-prices` 解析，不要依赖 `--model` 让后端解析价格。遇到 `Invalid parameter`、`价格未定义`、`Not Found` 时，停止继续猜字段或换接口重试；重新执行 `model-prices --json` 并按上面的规则定位模型和价格项。

### 生成完成后的项目地址回传规则

每次生图或生视频任务生成完成后，如果本次操作有对应项目 ID，必须在给用户的结果总结中返回项目地址。项目地址拼接方式固定为：`https://www.maxday.ai/project/{项目ID}`。

对应项目 ID 可以来自用户提供的 `--project-id`、`project-create` 返回的项目 ID、本地 `active_project`、或 `project-get` / `folders` / `agent-task` 等命令返回的项目字段。若 `--project-id` 省略但操作使用了活动项目，先通过 `config --json`、`project-get --json` 或相关命令返回值确认项目 ID；不要凭项目名猜测 ID。批量生成涉及多个项目时，逐个列出项目地址。没有项目 ID 的独立工具任务无需返回项目地址。

### 1. 批量管理项目与资产

```bash
# 切换项目
python3 {baseDir}/agent_skill.py project-switch --project-id PROJECT_ID --json

# 批量创建文件夹并上传资产 (可用 Shell 循环)
python3 {baseDir}/agent_skill.py folder-create --project-id PROJECT_ID --type image --name References --json
python3 {baseDir}/agent_skill.py folder-upload --project-id PROJECT_ID --type image --file /path/to/image1.png --json
```

### 2. 批量生成图片 / 视频

在执行生图或生视频前，先使用 `model-prices` 查询模型和价格信息。生图必须遵守“图片生成前置硬门槛”，生视频必须遵守“视频生成前置硬门槛”，两者都必须遵守“费用确认硬门槛”。示例里的 `MODEL_ID`、`MODEL_PRICE_ID` 与 `ESTIMATED_PRICE` 必须来自 `model-prices --json` 的解析结果，并且已展示给用户确认。

```bash
# 批量生成图片 (请结合脚本或循环执行多条)
python3 {baseDir}/agent_skill.py image-generate --project-id PROJECT_ID \
  --name "Shot_01" --prompt "cinematic lighting, close up" \
  --model-id MODEL_ID --model-price-id MODEL_PRICE_ID \
  --estimated-price ESTIMATED_PRICE --count 1 --yes --json

# 批量生成视频
python3 {baseDir}/agent_skill.py video-generate --project-id PROJECT_ID \
  --name "Scene_01" --prompt "camera pans left" \
  --model-id MODEL_ID --model-price-id MODEL_PRICE_ID \
  --duration 5 --estimated-price ESTIMATED_PRICE --yes --json
```

### 3. 使用独立工具 (Standalone Tools)

如果不需要进入完整的 Drama 项目，可以使用独立工具进行快速的批量生成：

```bash
# 生成独立工具图片
python3 {baseDir}/agent_skill.py tools-image-generate --conversation-id CONV_ID \
  --prompt "cyberpunk city" \
  --model-id MODEL_ID --model-price-id MODEL_PRICE_ID \
  --estimated-price ESTIMATED_PRICE --count 4 --yes --json

# 生成独立工具视频
python3 {baseDir}/agent_skill.py tools-video-generate --conversation-id CONV_ID \
  --prompt "camera pans left" \
  --model-id MODEL_ID --model-price-id MODEL_PRICE_ID \
  --estimated-price ESTIMATED_PRICE --duration 5 --yes --json
```

### 4. 批量下载

当通过 `folders` 或 `agent-task` 查询到生成结果的 URL 后，可以批量下载：

```bash
python3 {baseDir}/agent_skill.py download --urls URL1 URL2 URL3 --output-dir /tmp/maxday_batch --json
```

## CLI 接口清单

调用格式：

```bash
python3 {baseDir}/agent_skill.py [--api-base-url URL] [--timeout SECONDS] <command> [options] [--json]
```

通用规则：

- `--json` 可用于所有子命令，输出机器可读 JSON。
- `--project-id` 省略时，项目级命令会使用本地 `active_project`；如果本地没有活动项目，先运行 `projects`、`project-add` 或 `project-switch`。
- `--type` 在文件夹和素材命令中通常使用 `image`、`video`、`audio` 等平台素材类型；具体值以平台返回为准。
- 所有消耗额度、删除数据、发起 AI 任务、支付、转账等生产操作必须带 `--yes`。

### 认证、配置与通用文件

| 命令 | 后端接口 | 用途 | 关键参数 |
|---|---|---|---|
| `config` | 本地状态 | 查看或设置 CLI 配置、登录状态、活动项目和缓存会话 | `[--set-api-base-url URL]` |
| `send-code` | `/user/email/sendCode` | 发送邮箱验证码 | `--email` |
| `login` | `/user/login` | 使用验证码登录；加 `--save` 保存 token | `--email`, `--code`, `[--save]` |
| `user` | `/user/get` | 获取当前用户信息和余额相关数据 | 无 |
| `upload` | `/common/file/upload/url/get` + 存储 PUT | 上传单个本地文件并返回平台文件 URL | `--file` |
| `download` | 直接下载 URL | 批量下载平台返回的图片、视频、音频等 URL | `--urls URL...`, `[--output-dir]`, `[--prefix]` |

### 项目、设置与剧本

| 命令 | 后端接口 | 用途 | 关键参数 |
|---|---|---|---|
| `projects` | `/drama/project/list` | 查询项目列表，并写入本地项目缓存 | `[--query-flag]` |
| `project-add` | 本地状态 | 手动把已有项目 ID 加入本地缓存并设为活动项目 | `--project-id`, `[--name]` |
| `project-switch` | 本地状态 | 切换本地活动项目 | `--project-id` |
| `project-create` | `/drama/project/save` | 创建项目；成功后自动设为活动项目 | `--name`, `[--description]`, `[--org-id]`, `[--use-org-wallet]`, `[--members-json]`, `[--cover]` |
| `project-get` | `/drama/project/get` | 获取项目详情，可控制是否返回剧本文本 | `[--project-id]`, `[--script-content-flag]` |
| `project-delete` | `/drama/project/delete` | 删除项目并移除本地缓存 | `[--project-id]`, `--yes` |
| `project-copy` | `/drama/project/copy` | 复制项目 | `[--project-id]` |
| `project-settings` | `/drama/assets/analyse` | 保存项目分析和制作设置 | `[--project-id]`, `--title`, `--historical-background`, `--visual-style`, `[--aspect-ratio]`, `[--duration]`, `[--episode-count]`, `[--language]`, `[--prompt-language]`, `[--story]` |
| `script-save` | `/drama/file/script/save` | 保存剧本文本或上传剧本文件；`--extract` 会触发 MaxDay AI Agent 解析 | `[--project-id]`, `--script-content` 或 `--script-file`, `[--aspect-ratio]`, `[--language]`, `[--prompt-language]`, `[--extract --yes]` |
| `agent-task` | `/drama/file/agent/task/get` | 查询剧本解析 / Agent 任务状态 | `[--project-id]` |

### 模型与价格

| 命令 | 后端接口 | 用途 | 关键参数 |
|---|---|---|---|
| `model-prices` | `/common/model/price/list` | 查询全部可用模型和价格配置 | 无 |
| `model-price` | `/common/model/price/get` | 查询指定模型、任务类型、数量和时长的价格 | `--model`, `--type 1|2|3|4`, `[--count]`, `[--duration]` |

### 项目素材、生成与回收站

| 命令 | 后端接口 | 用途 | 关键参数 |
|---|---|---|---|
| `folders` | `/drama/file/folder/list` | 查询项目素材文件夹或文件夹内资源 | `[--project-id]`, `--type`, `[--folder-id]`, `[--query-type]` |
| `folder-create` | `/drama/file/folder/add` | 创建素材文件夹或子文件夹 | `[--project-id]`, `--type`, `--name`, `[--folder-id]` |
| `folder-upload` | `/drama/file/folder/upload` | 上传本地图片、视频或音频到项目素材文件夹 | `[--project-id]`, `--type`, `--file`, `[--name]`, `[--folder-id]`, `[--source]` |
| `image-generate` | `/drama/file/folder/image/generate` | 在项目素材区发起图片生成任务 | `[--project-id]`, `[--type]`, `[--folder-id]`, `--name`, `--prompt`, `--model-id`, `--model-price-id` 必须先由 `model-prices` 解析, `--estimated-price` 必须先展示并经用户确认, `[--count]`, `[--aspect-ratio]`, `[--resolution]`, `[--ref-images]`, `[--source]`, `--yes` |
| `video-generate` | `/drama/file/folder/video/generate` | 在项目素材区发起视频生成任务 | `[--project-id]`, `[--type]`, `[--folder-id]`, `--name`, `--prompt`, `--model-id`, `--model-price-id` 必须先由 `model-prices` 解析, `--estimated-price` 必须先展示并经用户确认, `[--count]`, `[--duration]`, `[--aspect-ratio]`, `[--resolution]`, `[--ref-images]`, `[--ref-videos]`, `[--ref-audios]`, `[--start-image]`, `[--end-image]`, `[--source]`, `--yes` |
| `resource-get` | `/drama/file/folder/resource/get` | 获取单个素材资源详情 | `--resource-id` |
| `resource-delete` | `/drama/file/folder/resource/delete` | 删除一个或多个素材资源 | `--ids`, `--yes` |
| `trash` | `/drama/file/folder/recycleBin/list` | 查询项目回收站 | `[--project-id]` |
| `restore` | `/drama/file/folder/recycleBin/restore` | 从回收站恢复文件夹或资源 | `[--project-id]`, `[--folder-id]`, `[--resource-id]` |

### 项目聊天与 MaxDay AI Agent

| 命令 | 后端接口 | 用途 | 关键参数 |
|---|---|---|---|
| `chat-create` | `/chat/session/create` | 为项目创建聊天会话，并缓存会话 ID | `[--project-id]` |
| `chat-list` | `/chat/session/list` | 查询项目聊天会话列表 | `[--project-id]` |
| `chat-send` | `/chat/message/send` | 向会话发送消息，可能触发 MaxDay AI Agent 行为 | `--session-id`, `--message`, `--yes` |
| `chat-history` | `/chat/message/history` | 查询会话消息历史 | `--session-id` |

### 独立工具接口

| 命令 | 后端接口 | 用途 | 关键参数 |
|---|---|---|---|
| `tools-conversations` | `/tools/conversation/list` | 查询独立工具会话列表 | 无 |
| `tools-conversation-save` | `/tools/conversation/save` | 新建或更新独立工具会话 | `--name`, `[--description]`, `[--conversation-id]` |
| `tools-assets` | `/tools/asset/list` | 查询独立工具会话资产 | `--conversation-id`, `[--type]` |
| `tools-image-generate` | `/tools/image/generate` | 不进入项目，直接发起独立图片生成任务 | `[--conversation-id]`, `--prompt`, `--model-id`, `--model-price-id` 必须先由 `model-prices` 解析, `--estimated-price` 必须先展示并经用户确认, `[--model]` 仅为兼容字段, `[--count]`, `[--aspect-ratio]`, `[--resolution]`, `[--ref-images]`, `--yes` |
| `tools-video-generate` | `/tools/video/generate` | 不进入项目，直接发起独立视频生成任务 | `[--conversation-id]`, `--prompt`, `--model-id`, `--model-price-id` 必须先由 `model-prices` 解析, `--estimated-price` 必须先展示并经用户确认, `[--model]` 仅为兼容字段, `[--count]`, `[--duration]`, `[--aspect-ratio]`, `[--resolution]`, `[--start-image]`, `[--end-image]`, `[--ref-images]`, `[--ref-videos]`, `[--ref-audios]`, `--yes` |

### 消耗、支付与余额

| 命令 | 后端接口 | 用途 | 关键参数 |
|---|---|---|---|
| `costs` | `/drama/costs/list` | 查询 AI 消耗明细 | `[--page-no]`, `[--page-size]`, `[--project-id]`, `[--email]`, `[--model-id]` |
| `costs-user` | `/drama/costs/user` | 查询用户维度消耗统计 | `[--project-id]` |
| `pay-history` | `/pay/history/list` | 查询支付 / 充值历史 | `[--page-no]`, `[--page-size]` |
| `recharge-wechat` | `/pay/wechat/pay/generate` | 创建微信充值订单 | `--amount-yuan`, `--yes` |
| `pay-query` | `/pay/wechat/order/query` | 查询微信支付订单状态 | `--order-no` |
| `balance-transfer` | `/user/balance/transfer` | 给指定邮箱转移余额 / 积分 | `--email`, `--coins`, `--yes` |

### 组织与组织钱包

| 命令 | 后端接口 | 用途 | 关键参数 |
|---|---|---|---|
| `organizations` | `/organization/my/list` | 查询我的组织列表 | 无 |
| `organization-create` | `/organization/create` | 创建组织 | `--name`, `[--description]`, `[--cover]`, `[--members-json]` |
| `organization-join` | `/organization/join` | 申请加入组织 | `--org-no`, `[--remark]` |
| `organization-members` | `/organization/member/list` | 查询组织成员 | `--org-id` |
| `organization-wallet-summary` | `/organization/wallet/summary` | 查询组织钱包汇总 | `--org-id` |
| `organization-wallet-accounts` | `/organization/wallet/account/list` | 查询组织钱包账户列表 | `--org-id` |
| `organization-wallet-logs` | `/organization/wallet/logs` | 查询组织钱包流水 | `--org-id`, `[--consume-flag]`, `[--page-no]`, `[--page-size]`, `[--project-id]`, `[--model-id]`, `[--type]`, `[--uid]` |
| `organization-transfer-to-member` | `/organization/wallet/transfer-to-member` | 从组织钱包转给成员 | `--org-id`, `--amount`, `--email` 或 `--uid`, `--yes` |
| `organization-return-to-wallet` | `/organization/wallet/return-to-organization` | 从成员账户退回组织钱包 | `--org-id`, `--amount`, `--email` 或 `--uid`, `--yes` |
