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
4. 第二步（`--review`）：把 `needs_review: true` 的動態連同該轄區狀態交給 Claude Opus 5.5，
   它會打開來源連結查證，提出「建議修改＋來源連結」，自動開成 Pull Request（標籤 `status-review`）
5. 你在 PR 頁面點開來源確認後按合併：狀態修改、`needs_review` 改 `false`、`last_reviewed` 更新一次生效；
   關閉 PR 則什麼都不改。已有未處理的審查 PR 時，下週會跳過第二步

需要的 GitHub Secrets：`ANTHROPIC_API_KEY`、`TAVILY_API_KEY`。

## 手動更新

- 本機執行：`python scraper/weekly_update.py`（自動讀 `C:\Users\dinef\AI\keys\` 的金鑰）
- 或到 GitHub Actions 頁面手動 Run workflow
- 狀態矩陣：直接編輯 `data/status.json`（或請 Claude Code 代勞），改完把對應動態的
  `needs_review` 改為 `false`，並更新該轄區的 `last_reviewed`

## 費用

GitHub Actions 與 Pages 免費；每週 Tavily（免費額度內）＋ Claude 分類約 $0.05–0.2 美元。
第二步審查依待確認數量與來源網頁長短而定，每個轄區約數毛到 1 美元（未實測）；第一次要清掉累積的待確認項目，會比平常多。
