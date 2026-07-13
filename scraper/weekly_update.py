# -*- coding: utf-8 -*-
"""每週永續準則動態更新腳本。

流程：
1. 讀 data/status.json 取得各轄區的搜尋關鍵字
2. Tavily 搜尋最近 9 天新聞，依 URL 去重
3. Claude Haiku 一次過濾＋翻譯摘要＋分類（一般動態 / 可能影響狀態）
4. 寫回 data/updates.json；「可能影響狀態」標 needs_review=true，等人工確認後才改 status.json

金鑰：環境變數 ANTHROPIC_API_KEY / TAVILY_API_KEY 優先（GitHub Actions），
否則讀本機 C:\\Users\\dinef\\AI\\keys\\ 下的檔案。
"""
import json
import os
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = ROOT / "data" / "status.json"
UPDATES_FILE = ROOT / "data" / "updates.json"
LOCAL_KEYS = Path(r"C:\Users\dinef\AI\keys")
MAX_UPDATES = 500
SEARCH_DAYS = 9  # 每週跑一次，多抓兩天避免漏接
CLAUDE_MODEL = "claude-haiku-4-5-20251001"


def get_key(env_name, local_file):
    val = os.environ.get(env_name, "").strip()
    if val:
        return val
    path = LOCAL_KEYS / local_file
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    raise SystemExit(f"找不到金鑰：環境變數 {env_name} 或 {path}")


def tavily_search(api_key, query):
    resp = requests.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "query": query,
            "topic": "news",
            "days": SEARCH_DAYS,
            "max_results": 5,
            "search_depth": "basic",
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def classify_with_claude(api_key, items):
    """一次呼叫處理全部新項目：過濾、翻譯、分類。回傳與 items 等長的清單。"""
    payload = [
        {
            "index": i,
            "jurisdiction": it["jurisdiction_id"],
            "title": it["title_en"],
            "snippet": it.get("snippet", "")[:500],
        }
        for i, it in enumerate(items)
    ]
    prompt = f"""你是永續揭露法規追蹤助理。以下是本週搜尋到的新聞項目（JSON）：

{json.dumps(payload, ensure_ascii=False)}

對每一項判斷並輸出：
- keep：只保留「主管機關、準則制定者（ISSB/IAASB/SSBJ/KSSB/AASB/EFRAG/SEC/CARB/CSSB/CSA/DBT/FCA/FRC/ACRA/SGX/FSA/FSC 等）或立法機關」有關永續揭露準則或永續確信的實質進展；廠商行銷文、webinar／活動宣傳、partner content、一般 ESG 評論、與準則進度無關者一律 false
- jurisdiction：這則新聞實際屬於哪個轄區，從 {json.dumps(sorted({it["jurisdiction_id"] for it in items}))} 中選一個（可以和輸入的 jurisdiction 不同，例如 ISSB 查詢查到的歐盟新聞應改為 eu）
- date：若能從標題或內文判斷事件發生日期，給 YYYY-MM-DD；判斷不出給空字串
- title_zh：繁體中文標題（keep=false 可給空字串）
- summary_zh：一到兩句繁體中文摘要，說清楚「誰、做了什麼、影響哪個時程」（keep=false 可給空字串）
- impact："status_change"（涉及時程變動、範圍變動、法規定案/撤回/暫停等會改變各國狀態者）或 "info"（一般進展）

只輸出 JSON 陣列（與輸入等長、含 index），不要任何其他文字或 markdown 圍欄。"""
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": CLAUDE_MODEL,
            "max_tokens": 8000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=180,
    )
    resp.raise_for_status()
    text = resp.json()["content"][0]["text"].strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("["):text.rfind("]") + 1]
    return json.loads(text)


def main():
    tavily_key = get_key("TAVILY_API_KEY", "Tavily_search_API.txt")
    claude_key = get_key("ANTHROPIC_API_KEY", "claude_api.txt")

    status = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    updates_doc = json.loads(UPDATES_FILE.read_text(encoding="utf-8"))
    updates = updates_doc.get("updates", [])
    known_urls = {u["url"] for u in updates}

    candidates = []
    for j in status["jurisdictions"]:
        query = j.get("search_query")
        if not query:
            continue
        try:
            results = tavily_search(tavily_key, query)
        except Exception as e:
            print(f"[warn] {j['id']} 搜尋失敗：{e}")
            continue
        for r in results:
            url = (r.get("url") or "").strip()
            if not url or url in known_urls:
                continue
            known_urls.add(url)
            pub = (r.get("published_date") or "")[:10]
            try:
                datetime.strptime(pub, "%Y-%m-%d")
            except ValueError:
                pub = date.today().isoformat()
            candidates.append({
                "jurisdiction_id": j["id"],
                "title_en": r.get("title", "").strip(),
                "snippet": r.get("content", ""),
                "url": url,
                "date": pub,
            })
        print(f"[info] {j['id']}: 取得 {len(results)} 筆")

    if not candidates:
        print("[info] 本週沒有新項目，結束。")
        return

    print(f"[info] 共 {len(candidates)} 筆新項目，交給 Claude 過濾分類…")
    verdicts = classify_with_claude(claude_key, candidates)
    verdict_by_index = {v["index"]: v for v in verdicts if isinstance(v, dict)}

    added = 0
    for i, item in enumerate(candidates):
        v = verdict_by_index.get(i)
        if not v or not v.get("keep"):
            continue
        impact = v.get("impact") if v.get("impact") in ("status_change", "info") else "info"
        valid_ids = {j["id"] for j in status["jurisdictions"]}
        jur = v.get("jurisdiction") if v.get("jurisdiction") in valid_ids else item["jurisdiction_id"]
        item_date = item["date"]
        v_date = (v.get("date") or "").strip()
        try:
            datetime.strptime(v_date, "%Y-%m-%d")
            item_date = v_date
        except ValueError:
            pass
        updates.append({
            "id": uuid.uuid4().hex[:12],
            "date": item_date,
            "jurisdiction_id": jur,
            "title_en": item["title_en"],
            "title_zh": v.get("title_zh") or item["title_en"],
            "summary_zh": v.get("summary_zh", ""),
            "url": item["url"],
            "impact": impact,
            "needs_review": impact == "status_change",
        })
        added += 1

    updates.sort(key=lambda u: u.get("date", ""), reverse=True)
    updates_doc["updates"] = updates[:MAX_UPDATES]
    UPDATES_FILE.write_text(
        json.dumps(updates_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    pending = sum(1 for u in updates_doc["updates"] if u.get("needs_review"))
    print(f"[done] 新增 {added} 筆（過濾掉 {len(candidates) - added} 筆）；待人工確認共 {pending} 筆。")


if __name__ == "__main__":
    main()
