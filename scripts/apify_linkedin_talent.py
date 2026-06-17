"""
LinkedIn 候選人資料抓取腳本
使用 Apify LinkedIn Profile Scraper 抓取符合條件的候選人
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
OUTPUT_DIR = Path(__file__).parent.parent / "candidate-drafts"
OUTPUT_DIR.mkdir(exist_ok=True)

ACTOR_ID = "2SyF0bVxmgGr8IVCZ"  # LinkedIn Profile Scraper


def scrape_by_search(roles: list[str], location: str, limit: int = 50) -> list[dict]:
    """S1 直攻法：依職稱 + 地區搜尋候選人"""
    client = ApifyClient(APIFY_TOKEN)

    search_queries = []
    for role in roles:
        search_queries.append(f'site:linkedin.com/in "{role}" "{location}"')

    run_input = {
        "searchUrl": f"https://www.linkedin.com/search/results/people/?keywords={roles[0]}&location={location}",
        "maxResults": limit,
        "proxyConfiguration": {"useApifyProxy": True},
    }

    print(f"[Apify] 搜尋條件：{roles} @ {location}，上限 {limit} 人")
    run = client.actor(ACTOR_ID).call(run_input=run_input)

    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)

    print(f"[Apify] 抓取完成，共 {len(results)} 筆")
    return results


def scrape_by_company(company: str, roles: list[str], limit: int = 100) -> list[dict]:
    """S6 競品挖角法：依公司名稱搜尋員工"""
    client = ApifyClient(APIFY_TOKEN)

    run_input = {
        "searchUrl": f"https://www.linkedin.com/search/results/people/?currentCompany={company}&keywords={','.join(roles)}",
        "maxResults": limit,
        "proxyConfiguration": {"useApifyProxy": True},
    }

    print(f"[Apify] 搜尋公司：{company}，職位：{roles}")
    run = client.actor(ACTOR_ID).call(run_input=run_input)

    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)

    print(f"[Apify] 抓取完成，共 {len(results)} 筆")
    return results


def scan_intent_signals(watch_list_path: str) -> list[dict]:
    """S2 意圖法：掃描 Watch List 中候選人的最新動態"""
    with open(watch_list_path) as f:
        watch_list = json.load(f)

    client = ApifyClient(APIFY_TOKEN)
    updated_profiles = []

    profile_urls = [p["linkedin_url"] for p in watch_list if p.get("linkedin_url")]

    run_input = {
        "profileUrls": profile_urls,
        "proxyConfiguration": {"useApifyProxy": True},
    }

    print(f"[Apify] 掃描 Watch List，共 {len(profile_urls)} 人")
    run = client.actor(ACTOR_ID).call(run_input=run_input)

    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        updated_profiles.append(item)

    return updated_profiles


def save_results(results: list[dict], mode: str) -> str:
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = OUTPUT_DIR / f"targets_{mode}_{date_str}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[Save] 結果已儲存：{output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="LinkedIn 候選人抓取")
    parser.add_argument("--mode", choices=["search", "company", "intent_scan"],
                        default="search", help="抓取模式")
    parser.add_argument("--role", type=str, help="目標職稱（逗號分隔）")
    parser.add_argument("--location", type=str, default="Taiwan", help="地區")
    parser.add_argument("--company", type=str, help="目標公司（S6 模式）")
    parser.add_argument("--limit", type=int, default=50, help="抓取上限")
    parser.add_argument("--list", type=str, help="Watch List 路徑（S2 模式）")

    args = parser.parse_args()

    roles = [r.strip() for r in args.role.split(",")] if args.role else \
            os.getenv("TARGET_ROLES", "Business Development Manager").split(",")

    if args.mode == "search":
        results = scrape_by_search(roles, args.location, args.limit)
        save_results(results, "s1")

    elif args.mode == "company":
        if not args.company:
            print("[Error] --company 為必填（S6 模式）")
            return
        results = scrape_by_company(args.company, roles, args.limit)
        save_results(results, "s6")

    elif args.mode == "intent_scan":
        if not args.list:
            print("[Error] --list 為必填（S2 模式）")
            return
        results = scan_intent_signals(args.list)
        save_results(results, "s2_intent")


if __name__ == "__main__":
    main()
