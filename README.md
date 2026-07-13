# 🌏 全球永續準則與確信進度追蹤

追蹤 11 個轄區（日本、韓國、澳洲、歐盟、美國、加拿大、英國、新加坡、香港、馬來西亞、巴西）
＋ ISSB/IAASB 源頭的**永續揭露準則採用進度**與**永續確信要求**。

網站：https://shelly-awkward.github.io/sustainability-tracker/

## 資料分兩層

| 檔案 | 內容 | 誰更新 |
|------|------|--------|
| `data/status.json` | 各轄區狀態矩陣（準則、時程、確信要求、時間軸） | **人工**（經確認才改） |
| `data/updates.json` | 最新動態流（中英對照摘要） | **每週日 21:00（台灣時間）自動** |

自動流程只寫 `updates.json`；判定「可能影響狀態」的動態會標 `needs_review: true`，
在網站頂部顯示黃色待確認區塊，人工檢視來源後才更新 `status.json`。

## 自動更新流程

`.github/workflows/weekly_update.yml` → `scraper/weekly_update.py`：

1. 依 `status.json` 各轄區的 `search_query` 用 Tavily 搜尋最近 9 天新聞
2. URL 去重後，一次呼叫 Claude Haiku：過濾非官方雜訊、翻譯繁中標題與摘要、分類影響程度
3. 寫回 `updates.json` 並自動 commit

需要的 GitHub Secrets：`ANTHROPIC_API_KEY`、`TAVILY_API_KEY`。

## 手動更新

- 本機執行：`python scraper/weekly_update.py`（自動讀 `C:\Users\dinef\AI\keys\` 的金鑰）
- 或到 GitHub Actions 頁面手動 Run workflow
- 狀態矩陣：直接編輯 `data/status.json`（或請 Claude Code 代勞），改完把對應動態的
  `needs_review` 改為 `false`，並更新該轄區的 `last_reviewed`

## 費用

GitHub Actions 與 Pages 免費；每週 Tavily（免費額度內）＋ Claude Haiku 約 $0.05–0.2 美元。
