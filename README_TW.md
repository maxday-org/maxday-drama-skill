<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/maxday-icon.svg" />
    <source media="(prefers-color-scheme: light)" srcset="assets/maxday-icon-dark.svg" />
    <img src="assets/maxday-icon-dark.svg" width="96" height="96" alt="MaxDay" />
  </picture><br/>
  <strong>maxday-drama-skill</strong><br/><br/>
  <a href="README.md">简体中文</a> | <a href="README_EN.md">English</a> | <strong>繁體中文</strong> | <a href="README_JA.md">日本語</a>
</p>
<br/>

## 一行指令，讓 MaxDay 進入你的 Agent 工作流

### 透過 AI Agent 安裝（推薦）

將下面這段話直接發給你的 AI 助手（Codex CLI / App、Claude Code、Kimi Code/Claw、MiniMax Agent、Trae 等），它會自動幫你完成安裝和初始化。

**提示詞：**
> 請幫我安裝 maxday-drama-skill：`https://www.maxday.ai/maxday-drama-skill.zip`

### 手動安裝

在終端機執行：
```bash
npx skills add maxday-org/maxday-drama-skill
```
環境需求：Python 3.8+，無需安裝額外依賴。
首次使用時，Agent 會引導你透過 Email 驗證碼登入 MaxDay。

## 讓每個 AI Agent 完美駕馭 MaxDay

你的 AI Agent 已經很會想創意、寫腳本、拆分鏡、改 prompt，但它還缺少一個真正進入創作平台的入口。

maxday-drama-skill 就是這個入口。裝上之後，Agent 不再停留在「給你一段建議」或「讓你複製一段 prompt」，而是可以直接在 MaxDay 中建立專案、上傳劇本、管理素材、批次生成圖片和影片、追蹤任務進度、下載生成結果。

以前是你手動把想法搬進 MaxDay；現在可以透過 Agent 直接把創作過程落到 MaxDay 裡。你只需要**提出方向、確認動作、繼續創作。**

## 能做什麼

| 你想要 | Agent 透過 Skill 可以做什麼 |
|---|---|
| 做一部短劇 | 建立專案、上傳劇本、提取角色/場景、批次生圖、批次生影片、下載成片 |
| 批次生成角色圖 | 查詢模型價格、迴圈提交生圖任務、追蹤進度、批次下載結果 |
| 批次生成影片 | 上傳參考圖/音訊/影片、迴圈提交生影片任務、輪詢狀態、下載 |
| 上傳劇本並提取資產 | 上傳劇本檔案、觸發 AI Agent 解析、查詢提取任務狀態 |
| 管理專案素材 | 建立資料夾、批次上傳圖片/影片/音訊、查看資源、刪除和恢復 |
| 專案內快速出圖/出影片 | 在專案中建立任務、批次生成並下載 |
| 追蹤生成進度 | 查詢專案、任務狀態、定位失敗任務 |
| 查看消耗和帳務 | 查看餘額、AI 消耗記錄、交易歷史、微信充值 |
| 管理組織和錢包 | 查看組織、成員、錢包匯總、錢包流水、轉帳 |

## 可以直接這樣用

下面這些是你在登入 MaxDay 後，可以直接發給 Agent 的完整任務示例。

### 1. 短劇批次製作

```
用 maxday-drama，製作一個短劇專案，專案叫「都市暗戀」，劇本在 ./script.docx。

請幫我：
1. 在 MaxDay 建立一個新專案，畫幅 9:16，風格設為「電影感真人」；
2. 上傳劇本並提取所有角色、場景和道具資產；
3. 等資產提取完成後，給每個主角生成一張直式角色主視覺；
4. 然後給前 3 個場景各生成一段 5 秒開場影片；
5. 所有生成完成後，把結果下載到 ~/Documents/dramas/都市暗戀/。
```

### 2. 批次生圖

```
用 maxday-drama，生成 5 張圖。

要求：
- 專案使用/建立「霓虹概念圖專案」
- 畫幅 9:16
- 風格 1：賽博朋克霓虹燈光
- 風格 2：柔光自然寫實
- 用最便宜的可用模型
- 提示詞：賽博朋克城市雨夜，霓虹燈倒映在濕潤街道上，電影感構圖，細節豐富
```

### 3. 單條影片生成

```
用 maxday-drama，生成一個影片。

要求：
- 專案使用/建立「霓虹短影片專案」
- 模型用 seedance2-pro-vvip
- 畫幅 9:16
- 時長 5 秒
- 清晰度 480p
- 提示詞：賽博朋克城市雨夜，霓虹燈倒映在濕潤街道上，鏡頭緩慢推進，電影感光影
```

### 4. 批次角色圖生成

```
用 maxday-drama，給目前專案的 8 個角色各生成 2 張不同風格的肖像圖。

要求：
- 專案使用/建立「霓虹角色肖像集」
- 畫幅 9:16
- 風格 1：賽博朋克霓虹燈光
- 風格 2：柔光自然寫實
- 用最便宜的可用模型
- 全部生成後下載到桌面的 characters 資料夾
```

### 5. 批次影片生成

```
用 maxday-drama，把 ./storyboard/ 目錄下的 10 張分鏡圖批次生成影片。

請幫我：
1. 專案使用/建立「分鏡動態影片集」；
2. 把這些圖片全部上傳到該專案的 image 資料夾；
3. 用每張圖作為起始幀，各生成一段 5 秒的影片；
4. prompt 統一用「cinematic camera movement, dramatic lighting」；
5. 生成完成後批次下載到 ./output/videos/。
```

### 6. 專案內快速出圖

```
用 maxday-drama，快速生成 4 張概念圖。

請幫我：
1. 專案使用/建立「概念圖探索集」；
2. 在該專案中生成 4 張概念圖，主題分別是：
   - 賽博朋克城市街景，雨夜，霓虹反射
   - 古風庭院，月下獨酌
   - 太空站內部，失重漂浮的太空人
   - 海底古城遺跡，光線穿透水面
3. 全部生完後下載到桌面。
```

### 7. 查看消耗和充值

```
用 maxday-drama，幫我查一下：
1. 目前帳戶餘額；
2. 最近的 AI 消耗記錄，按專案匯總；
3. 如果餘額低於 10 元，幫我建立一個 50 元的微信充值訂單。
```

### 8. 組織錢包管理

```
用 maxday-drama，幫我管理一下組織錢包：
1. 查看我的組織列表；
2. 看一下主組織的錢包餘額和最近流水；
3. 給成員 alice@example.com 轉 100 積分。
```

## 安全說明

所有消耗積分、刪除資料、建立支付單、轉帳或觸發 AI 生成的操作，Agent 都會在執行前向你確認。當你明確表達了批次操作的意圖時（比如「幫我批次生成」），Agent 會自動執行而不逐條詢問。
