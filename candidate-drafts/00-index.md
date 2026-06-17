# Candidate Drafts — 索引

此目錄存放候選人資料與話術草稿。

## 檔案命名規則

| 檔案類型 | 命名格式 | 說明 |
|---------|---------|------|
| 原始抓取資料 | `targets_[策略]_[日期].json` | Apify 抓取的 LinkedIn 原始資料 |
| 分析結果 | `analyzed_[日期].json` | ICP 評分 + 候選人類型 + 話術草稿 |
| Watch List | `watch_list.json` | 長期監測的高潛力候選人 |
| 個別候選人草稿 | `candidate-[姓名].md` | 手動建立的候選人分析文件 |

## 目前狀態

> 尚未有任何候選人資料。執行 `scripts/apify_linkedin_talent.py` 開始抓取。

## Watch List 格式

```json
[
  {
    "name": "候選人姓名",
    "linkedin_url": "https://www.linkedin.com/in/xxx",
    "target_role": "目標職位",
    "added_date": "2026-06-17",
    "notes": "為什麼要長期追蹤這個人"
  }
]
```
