# LinkedIn 人才獵尋 Agent 架構規格

**版本：** v1.0  
**建立日期：** 2026-06-17  

---

## 系統架構總覽

```
┌──────────────────────────────────────────────────────────────┐
│                      每日排程（09:00）                         │
│                     Orchestrator Agent                         │
└───────┬──────────┬──────────┬──────────┬──────────┬──────────┘
        │          │          │          │          │
   ┌────▼───┐ ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────────┐
   │Apify   │ │Talent  │ │HR      │ │Talent  │ │Asana CRM   │
   │Scraper │ │Scout   │ │Coord.  │ │Auditor │ │Integration │
   │        │ │Agent   │ │Agent   │ │Agent   │ │            │
   └────┬───┘ └────┬───┘ └───┬────┘ └───┬────┘ └───┬────────┘
        │          │          │          │          │
        └──────────┴────┬─────┴──────────┘          │
                        │                            │
              ┌─────────▼──────────┐                │
              │  Candidate Dedup   │                │
              │  Layer             │                │
              └─────────┬──────────┘                │
                        │                            │
              ┌─────────▼──────────────────────────▼┐
              │           Asana CRM                   │
              │  候選人漏斗 / 階段追蹤 / 話術記錄      │
              └───────────────────────────────────────┘
```

---

## Agent 職責分工

### Apify Scraper（自動化）
- 每日根據各策略條件抓取 LinkedIn 候選人資料
- 輸出：JSON 格式候選人原始資料
- 觸發：排程 / 手動執行

### Talent-Scout Agent（`.claude/agents/talent-scout.md`）
- 輸入：候選人 LinkedIn 資料
- 輸出：候選人類型分析 + 三封信話術
- 觸發：新候選人加入名單時

### HR-Coordinator Agent（`.claude/agents/hr-coordinator.md`）
- 輸入：已回覆候選人資訊
- 輸出：面試邀請信、Offer 建議、拒絕信
- 觸發：候選人回覆 / 進入面試流程

### Talent-Auditor Agent（`.claude/agents/talent-auditor.md`）
- 輸入：Asana 漏斗數據 + 回覆記錄
- 輸出：每日回覆評分 + 週稽核報告
- 觸發：每日 18:00 / 每週五 17:00

---

## Asana CRM 結構

### Project 名稱：Talent Recruit Pipeline

#### Sections（對應漏斗階段）
```
01-Target      ← 已識別，尚未觸達
02-Contacted   ← 連線邀請已送出
03-Responded   ← 候選人有回應
04-Interview   ← 面試安排中/已面試
05-Offer       ← Offer 已發出
06-Hired       ← 錄用成功
07-Nurture     ← 培育（60天後重評）
```

#### Task 標準欄位
```
Task Name:     [候選人姓名] - [職位] - [公司]
Assignee:      負責 Recruiter
Due Date:      下一個跟進動作截止日
Tags:          S1 / S2 / S5 / S6（策略來源）
Custom Fields:
  - 候選人類型：A / B / C / D
  - 回覆評分：0–10
  - 職位目標：[職位名稱]
  - LinkedIn URL：[連結]
  - 觸達日期：[日期]
  - 上次接觸：[日期]
```

---

## 資料流

```
LinkedIn（Apify抓取）
        ↓
candidate-drafts/targets_[date].json
        ↓
talent_processor.py（ICP評分 + 話術生成）
        ↓
candidate-drafts/analyzed_[date].json
        ↓
asana_talent_dedup.py（去重 + 建立 Task）
        ↓
Asana CRM
        ↓
Expandi / 手動發送
        ↓
Talent-Auditor（追蹤回覆品質）
```

---

## 每日配額管理

| 資源 | 每日上限 | 說明 |
|------|---------|------|
| LinkedIn 連線邀請 | 20 人 | 週上限約 100 |
| LinkedIn 私訊 | 30 則 | 已連線後 |
| Apify 抓取 | 500 個 profile | API 成本控制 |
| 話術生成（Claude API） | 100 人 | 每人約 3 封信 |

---

## 告警機制

| 情況 | 告警方式 | 負責人 |
|------|---------|--------|
| 連線接受率 < 20% 連續 3 天 | Slack | Frank |
| 回覆率 < 10% 連續 1 週 | Slack | Frank |
| Asana 候選人 > 7 天無更新 | Asana 通知 | Recruiter |
| 面試爽約 | 即時通知 | Recruiter |
