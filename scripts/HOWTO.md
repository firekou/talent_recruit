# 操作說明 — Talent Recruit LinkedIn 系統

## 初次設定

```bash
cd scripts/
cp .env.example .env
# 填入以下金鑰：
# - ANTHROPIC_API_KEY
# - APIFY_TOKEN
# - ASANA_TOKEN + ASANA_PROJECT_GID

pip install -r requirements.txt
```

---

## 每日標準流程

### Step 1：抓取候選人名單（S1 直攻法）

```bash
python apify_linkedin_talent.py \
  --mode search \
  --role "Business Development Manager,Product Manager" \
  --location "Taiwan" \
  --limit 50
# 輸出：candidate-drafts/targets_s1_[日期].json
```

### Step 2：分析 + 生成話術

```bash
python talent_processor.py \
  --input ../candidate-drafts/targets_s1_[日期].json \
  --min-score 60
# 輸出：candidate-drafts/analyzed_[日期].json
```

### Step 3：匯入 Asana（去重）

```bash
python asana_talent_dedup.py \
  --input ../candidate-drafts/analyzed_[日期].json \
  --strategy S1
# 在 Asana 建立 Task，自動跳過重複候選人
```

### Step 4：審核話術並發送

1. 打開 `candidate-drafts/analyzed_[日期].json`
2. 找到 `priority: HIGH` 的候選人
3. 審核 `outreach_drafts` 中的連線邀請話術
4. 手動在 LinkedIn 發送（或匯入 Expandi）

---

## S2 意圖法流程

```bash
# 先建立 Watch List
# candidate-drafts/watch_list.json 格式：
# [{"name": "候選人姓名", "linkedin_url": "https://linkedin.com/in/xxx"}]

python apify_linkedin_talent.py \
  --mode intent_scan \
  --list ../candidate-drafts/watch_list.json
# 輸出：candidate-drafts/targets_s2_intent_[日期].json
```

---

## S6 競品挖角法流程

```bash
python apify_linkedin_talent.py \
  --mode company \
  --company "競品公司名稱" \
  --role "Business Development,Product Manager" \
  --limit 100
# 輸出：candidate-drafts/targets_s6_[日期].json
```

---

## 常見問題

**Q: Apify 抓不到資料？**
A: 確認 `APIFY_TOKEN` 正確，且帳號有足夠 compute units（每次約消耗 0.1–0.5 CU）

**Q: Claude 生成的話術太通用？**
A: 確認輸入的候選人資料有足夠欄位（fullName, headline, about, experience）

**Q: Asana 找不到 Section？**
A: 手動在 Asana 建立以下 Section：
   - 01-Target
   - 02-Contacted
   - 03-Responded
   - 04-Interview
   - 05-Offer
   - 06-Hired
   - 07-Nurture

---

## 每日時間預估

| 任務 | 時間 |
|------|------|
| 抓取 + 分析（50人） | ~15 分鐘（自動） |
| 話術審核（20人） | ~30 分鐘 |
| LinkedIn 發送（20人） | ~20 分鐘 |
| Asana 更新 | ~10 分鐘 |
| **合計** | **~75 分鐘/天** |
