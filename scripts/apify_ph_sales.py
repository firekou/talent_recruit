#!/usr/bin/env python3
"""
菲律賓網路業務銷售人員 LinkedIn 抓取腳本
Actor: bestscrapers/sales-navigator-scraper-by-filters
地區: Philippines (geo_code: 103121230)

目標候選人定義：
  - 大學應屆或畢業 0–3 年的新鮮人
  - 背景與 IT / 資訊科技相關
  - 或對藝術創作 / 電商 / AI 部門有興趣
  - 有 IT 背景、從事業務或業務相關工作者
"""

import os
import csv
import json
import time
import logging
from datetime import datetime
from pathlib import Path

try:
    from apify_client import ApifyClient
    from dotenv import load_dotenv
except ImportError:
    print("請先安裝依賴套件：pip install -r requirements.txt")
    raise

load_dotenv()
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
if not APIFY_TOKEN:
    raise SystemExit("❌ 缺少 APIFY_TOKEN，請在 .env 檔設定")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

ACTOR_ID = "bestscrapers/sales-navigator-scraper-by-filters"
PH_GEO = 103121230  # Philippines LinkedIn geo code

OUTPUT_DIR = Path(__file__).parent.parent / "candidate-drafts"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── 搜尋組合（針對菲律賓應屆/資淺業務人才）──────────────────
SEARCH_COMBOS = [
    {
        "name": "組合A：IT背景業務（應屆–3年）",
        "code": "ph_combo_A",
        "priority": "P1",
        "input": {
            "geo_codes": [PH_GEO],
            "title_keywords": [
                "IT Sales", "Technical Sales", "IT Solutions Sales",
                "Software Sales", "Technology Sales", "SaaS Sales",
                "Sales Engineer", "Pre-Sales", "IT Account Manager",
            ],
            "company_headcounts": ["1-10", "11-50", "51-200"],
            "functions": ["Sales", "Information Technology"],
            "seniority_levels": ["Entry Level", "Senior"],
            "years_of_experience": "0-3",
            "posted_on_linkedin": "true",
            "limit": 80,
        },
    },
    {
        "name": "組合B：電商業務 / 數位銷售（應屆–3年）",
        "code": "ph_combo_B",
        "priority": "P1",
        "input": {
            "geo_codes": [PH_GEO],
            "title_keywords": [
                "E-commerce Sales", "Online Sales", "Digital Sales",
                "Marketplace Sales", "Shopify", "Lazada", "Shopee",
                "Online Business Development", "E-commerce Specialist",
            ],
            "company_headcounts": ["1-10", "11-50", "51-200"],
            "functions": ["Sales", "Business Development"],
            "seniority_levels": ["Entry Level", "Senior"],
            "years_of_experience": "0-3",
            "posted_on_linkedin": "true",
            "limit": 70,
        },
    },
    {
        "name": "組合C：AI / 創意部門業務（應屆–3年）",
        "code": "ph_combo_C",
        "priority": "P2",
        "input": {
            "geo_codes": [PH_GEO],
            "title_keywords": [
                "AI Sales", "AI Solutions Sales", "Creative Sales",
                "Content Sales", "Digital Content Sales",
                "Agency Sales", "Creative Agency", "Media Sales",
                "Advertising Sales", "Marketing Sales",
            ],
            "company_headcounts": ["1-10", "11-50", "51-200"],
            "functions": ["Sales", "Marketing", "Business Development"],
            "seniority_levels": ["Entry Level", "Senior"],
            "years_of_experience": "0-3",
            "posted_on_linkedin": "true",
            "limit": 60,
        },
    },
    {
        "name": "組合D：IT背景 + 業務轉型（應屆–3年）",
        "code": "ph_combo_D",
        "priority": "P2",
        "input": {
            "geo_codes": [PH_GEO],
            "title_keywords": [
                "Business Development Representative", "BDR",
                "Sales Development Representative", "SDR",
                "Account Executive", "Junior Sales",
                "Sales Associate", "Sales Coordinator",
            ],
            "company_headcounts": ["11-50", "51-200"],
            "functions": ["Sales", "Information Technology"],
            "seniority_levels": ["Entry Level"],
            "years_of_experience": "0-3",
            "posted_on_linkedin": "true",
            "limit": 80,
        },
    },
    {
        "name": "組合E：應屆畢業生 IT/商業相關科系",
        "code": "ph_combo_E",
        "priority": "P3",
        "input": {
            "geo_codes": [PH_GEO],
            "title_keywords": [
                "Fresh Graduate", "Junior", "Associate",
                "Sales Trainee", "Sales Intern",
                "IT Graduate", "Computer Science Graduate",
            ],
            "company_headcounts": ["1-10", "11-50"],
            "functions": ["Sales", "Information Technology", "Business Development"],
            "seniority_levels": ["Entry Level"],
            "years_of_experience": "0-1",
            "posted_on_linkedin": "true",
            "limit": 50,
        },
    },
]

# ── ICP 評分（菲律賓應屆/資淺業務人才版）─────────────────────
IT_BACKGROUND_KW = [
    "information technology", "computer science", "it", "software",
    "programming", "coding", "developer", "engineer", "tech",
    "computer", "network", "cybersecurity", "data", "systems",
    "bs it", "bsit", "bscs", "bsis", "bs computer",
]

ECOMMERCE_KW = [
    "e-commerce", "ecommerce", "shopee", "lazada", "shopify", "amazon",
    "online store", "marketplace", "digital commerce", "online business",
]

AI_CREATIVE_KW = [
    "ai", "artificial intelligence", "machine learning", "chatgpt",
    "creative", "content creation", "design", "media", "advertising",
    "graphic", "photography", "video", "digital art", "animation",
    "canva", "figma", "adobe",
]

SALES_EXEC_KW = [
    "sales", "business development", "account", "client", "customer",
    "revenue", "quota", "pipeline", "leads", "outreach", "cold call",
    "prospecting", "closing", "negotiat",
]

FRESH_GRAD_KW = [
    "fresh graduate", "entry level", "junior", "trainee", "intern",
    "newly graduated", "0-1 year", "less than a year",
]


def icp_score_ph(title: str, about: str) -> int:
    """
    菲律賓應屆/資淺業務人才 ICP 評分（總分上限 100）：
      1. IT背景訊號     0-25（核心條件）
      2. 業務意圖訊號   0-25（有在做或想做業務）
      3. 電商/AI/創意   0-20（加分領域）
      4. 應屆/資淺訊號  0-15（年資符合）
      5. 活躍度         15（固定）
    """
    t = title.lower()
    a = (about or "").lower()
    txt = t + " " + a

    # 1. IT 背景訊號
    it_hits = sum(1 for kw in IT_BACKGROUND_KW if kw in txt)
    it_pts = min(it_hits * 5, 25)

    # 2. 業務意圖訊號
    sales_hits = sum(1 for kw in SALES_EXEC_KW if kw in txt)
    sales_pts = min(sales_hits * 5, 25)

    # 3. 電商 / AI / 創意領域加分
    ec_hits = sum(1 for kw in ECOMMERCE_KW if kw in txt)
    ai_hits = sum(1 for kw in AI_CREATIVE_KW if kw in txt)
    domain_pts = min((ec_hits + ai_hits) * 4, 20)

    # 4. 應屆/資淺訊號
    fresh_hits = sum(1 for kw in FRESH_GRAD_KW if kw in txt)
    # Entry-level 職稱也加分
    if any(kw in t for kw in ["entry", "junior", "associate", "trainee", "fresh"]):
        fresh_hits += 2
    fresh_pts = min(fresh_hits * 5, 15)

    # 5. 活躍度（固定）
    activity_pts = 15

    return min(it_pts + sales_pts + domain_pts + fresh_pts + activity_pts, 100)


def classify(score: int) -> str:
    if score >= 65:
        return "HOT"
    elif score >= 45:
        return "WARM"
    return "COLD"


def run_combo(combo: dict, client: ApifyClient) -> list:
    log.info(f"▶ 啟動 {combo['name']}")
    try:
        run = client.actor(ACTOR_ID).call(run_input=combo["input"])
    except Exception as e:
        log.error(f"  ✗ 初始化失敗：{e}")
        return []

    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    if not items:
        log.warning("  ⚠ 無回應")
        return []

    first = items[0]
    request_id = first.get("request_id")

    if not request_id:
        data = first.get("data", [])
        log.info(f"  ✓ 同步取回 {len(data)} 筆")
        return data

    log.info(f"  ✓ 初始化 request_id={request_id}，等待 7 分鐘...")
    time.sleep(420)

    all_data = []
    for page in range(1, 26):
        log.info(f"  第 {page} 頁...")
        try:
            pr = client.actor(ACTOR_ID).call(run_input={"request_id": request_id, "page": page})
            pi = list(client.dataset(pr["defaultDatasetId"]).iterate_items())
        except Exception as e:
            log.error(f"  ✗ 第 {page} 頁失敗：{e}")
            break
        if not pi:
            break
        page_data = pi[0].get("data", [])
        if not page_data:
            break
        all_data.extend(page_data)
        log.info(f"  累計 {len(all_data)} 筆")
        if len(page_data) < 100 or len(all_data) >= combo["input"]["limit"]:
            break
        time.sleep(5)
    return all_data


def normalize(raw: dict, combo: dict) -> dict:
    title   = raw.get("job_title") or raw.get("title") or ""
    about   = raw.get("about") or ""
    name    = raw.get("full_name") or raw.get("name") or ""
    company = raw.get("company") or ""
    score   = icp_score_ph(title, about)
    cls     = classify(score)
    return {
        "lead_id":           raw.get("profile_id") or raw.get("id") or "",
        "name":              name,
        "title":             title,
        "company":           company,
        "location":          raw.get("location") or "",
        "linkedin_url":      raw.get("linkedin_url") or raw.get("profileUrl") or "",
        "nationality":       "Philippines",
        "lead_source":       "PH-Sales-Scout/Apify",
        "icp_score":         score,
        "classification":    cls,
        "search_combo":      combo["code"],
        "combo_name":        combo["name"],
        "priority":          combo["priority"],
        "connection_status": "待發送",
        "reply_status":      "未回覆",
        "summary_snippet":   about[:200],
        "scrape_date":       datetime.now().strftime("%Y-%m-%d"),
        "asana_task_name":   f"[{cls}-{score}] {name} | {title[:35]} | {company[:22]} | PH",
    }


def deduplicate(leads: list) -> list:
    seen = {}
    for lead in leads:
        key = lead["linkedin_url"] or lead["lead_id"]
        if not key:
            continue
        if key not in seen or lead["icp_score"] > seen[key]["icp_score"]:
            seen[key] = lead
    return list(seen.values())


def save(leads: list) -> tuple:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    csv_path  = OUTPUT_DIR / f"targets_ph_{ts}.csv"
    json_path = OUTPUT_DIR / f"targets_ph_{ts}.json"
    if leads:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(leads[0].keys()))
            w.writeheader()
            w.writerows(leads)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)
    return csv_path, json_path


def print_summary(leads: list):
    hot  = [l for l in leads if l["classification"] == "HOT"]
    warm = [l for l in leads if l["classification"] == "WARM"]
    cold = [l for l in leads if l["classification"] == "COLD"]
    combo_counts = {}
    for l in leads:
        combo_counts[l["combo_name"]] = combo_counts.get(l["combo_name"], 0) + 1
    print("\n" + "=" * 65)
    print("  菲律賓業務人才抓取結果（應屆/資淺 × IT/電商/AI/創意）")
    print("=" * 65)
    print(f"  總候選人（去重）：{len(leads)} 筆")
    print(f"  HOT（≥65）：{len(hot)} 筆  ← 優先觸達")
    print(f"  WARM（45-64）：{len(warm)} 筆  ← 次批次")
    print(f"  COLD（<45）：{len(cold)} 筆  ← 培育池")
    print()
    for n, count in combo_counts.items():
        print(f"  {n}：{count} 筆")
    print()
    top = sorted(hot + warm, key=lambda x: -x["icp_score"])[:10]
    if top:
        print("  Top 10 HOT/WARM：")
        for l in top:
            print(f"    [{l['icp_score']}分 {l['classification']}] "
                  f"{l['name']} | {l['title'][:30]} | {l['company'][:20]}")
    print("=" * 65)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="菲律賓應屆/資淺業務人才 LinkedIn 抓取")
    parser.add_argument("--limit", type=int, default=80, help="每個搜尋組合的抓取上限")
    parser.add_argument("--combo", choices=["A", "B", "C", "D", "E", "all"], default="all",
                        help="執行指定組合（預設 all）")
    args = parser.parse_args()

    combos = SEARCH_COMBOS
    if args.combo != "all":
        combos = [c for c in SEARCH_COMBOS if c["code"].endswith(f"combo_{args.combo}")]

    for combo in combos:
        combo["input"]["limit"] = args.limit

    client = ApifyClient(APIFY_TOKEN)
    all_leads = []

    for i, combo in enumerate(combos):
        if i > 0:
            log.info("⏳ 間隔 10 秒...")
            time.sleep(10)
        raw_items = run_combo(combo, client)
        normalized = [normalize(r, combo) for r in raw_items if r]
        log.info(f"  → 標準化 {len(normalized)} 筆")
        all_leads.extend(normalized)

    log.info(f"📊 合併前 {len(all_leads)} 筆，本地去重中...")
    unique = deduplicate(all_leads)
    unique.sort(key=lambda x: -x["icp_score"])
    log.info(f"📊 去重後 {len(unique)} 筆")

    csv_path, json_path = save(unique)
    log.info(f"💾 CSV：{csv_path}")
    log.info(f"💾 JSON：{json_path}")
    print_summary(unique)
    log.info(f"✅ 下一步：")
    log.info(f"   python talent_processor.py --input {json_path}")
    log.info(f"   python asana_talent_dedup.py --input <analyzed_json> --strategy S1")


if __name__ == "__main__":
    main()
