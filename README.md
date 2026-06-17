# Talent Recruit

LinkedIn 人才主動開發系統  
管理：Frank

---

## 系統架構

```
四套並行策略 (S1 / S2 / S5 / S6)
         ↓
  Talent-Scout Agent 分析 + 三封信生成
         ↓
  Apify Scraper → ICP 評分 → 話術草稿
         ↓
  Asana CRM 追蹤 → Talent-Auditor 稽核
```

---

## 目錄結構

| 目錄 | 說明 |
|------|------|
| `.claude/agents/` | Claude Sub-agent 定義（Scout / Auditor / HR Coordinator） |
| `strategies/` | 四套 LinkedIn 人才開發策略 + 話術 SOP |
| `linkedin-outreach/` | Agent 架構規格、候選人類型矩陣、Phase 1 MVP |
| `scripts/` | Python 自動化腳本（Apify / Claude / Asana） |
| `candidate-drafts/` | 候選人資料與話術草稿 |

---

## Claude Agents

| Agent | 用途 |
|-------|------|
| `Talent-Scout` | 候選人職涯分析 + 三封信序列生成 |
| `Talent-Auditor` | 七層稽核 + 週報 + 回覆真實性評分 |
| `HR-Coordinator` | 面試安排 + Offer 談判 + 拒絕信撰寫 |

---

## 四套策略速查

| 代號 | 策略 | 觸發點 |
|------|------|--------|
| S1 | 直攻法 | 主動搜尋目標候選人 |
| S2 | 求職意圖法 | 候選人更新 LinkedIn / 開啟求職訊號 |
| S5 | 社群潛伏法 | LinkedIn 共同社群成員 |
| S6 | 競品挖角法 | 目標競品公司員工 |

詳細見 `strategies/` 目錄。

---

## 快速啟動

```bash
cd scripts/
cp .env.example .env
# 填入 APIFY_TOKEN, ANTHROPIC_API_KEY, ASANA_TOKEN

pip install -r requirements.txt

# 每日執行
python apify_linkedin_talent.py --mode search --role "Business Development Manager" --location "Taiwan" --limit 50
python talent_processor.py --input ../candidate-drafts/targets_s1_[日期].json
python asana_talent_dedup.py --input ../candidate-drafts/analyzed_[日期].json --strategy S1
```

詳細見 `scripts/HOWTO.md`。

---

## 候選人類型分類

| Type | 名稱 | 核心渴望 | 話術框架 |
|------|------|---------|---------|
| A | 職涯轉型者 | 新身份被行業認可 | 「這個職位是為你正在變成的人設計的」 |
| B | 成長停滯者 | 更快的晉升軌道 | 「你的能力已超出你現在的位置」 |
| C | 影響力驅動者 | 做有意義的事 | 「這個職位讓你真正影響到 [具體對象]」 |
| D | 被動觀望者 | 清楚的升級路徑且風險可控 | 「只是讓你知道這個選項存在」 |
