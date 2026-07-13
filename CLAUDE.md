# CLAUDE.md — 永續準則進度追蹤網站

## 這是什麼

追蹤 8 轄區＋ISSB/IAASB 的永續揭露準則與確信進度。
- 獨立 git repo → GitHub `Shelly-awkward/sustainability-tracker`（**不屬於外層 mops-daily repo**，不要把這裡的檔案 commit 到外層）
- GitHub Pages：https://shelly-awkward.github.io/sustainability-tracker/
- GitHub Actions 每週日台灣時間 21:00 自動更新動態流

## 鐵律

1. `data/status.json`（狀態矩陣）**只能人工／在對話中經用戶確認後修改**——自動腳本永遠不碰它。
2. 改 `status.json` 時：一併更新該轄區 `last_reviewed`，並把觸發修改的動態（`data/updates.json`）之 `needs_review` 改為 `false`。
3. `updates.json` 由每週腳本維護，手動加項目時格式照舊（id 隨意唯一、date 用 YYYY-MM-DD）。
   **整理動態時不要刪除項目**——URL 一刪就退出去重名單，下週會被重新抓回來；改設 `"hidden": true`（網頁會跳過、去重仍有效）。
4. 所有檔案存 UTF-8。

## 常用操作

```bash
# 本機手動跑一次每週更新（讀 keys\ 的 Tavily 與 Claude 金鑰）
python scraper/weekly_update.py

# 本機預覽網站
python -m http.server 8000   # 然後開 http://localhost:8000
```

## 用戶說「更新永續追蹤網站」時

1. 看網站待確認區塊（或 `updates.json` 裡 `needs_review: true` 的項目）
2. 逐項開來源連結查證，判斷 `status.json` 哪些欄位要改（status_level / status_zh / timeline / scope 等）
3. 跟用戶確認後修改、把 `needs_review` 關掉、更新 `last_reviewed` 與根層 `last_updated`
4. commit + push（會自動觸發 Pages 重新部署）

## 狀態等級（status_level）

`mandatory` 已強制｜`adopted` 已定案｜`proposed` 草案／研議中｜`voluntary` 自願適用｜`mixed` 分歧｜`paused` 暫停／倒退
