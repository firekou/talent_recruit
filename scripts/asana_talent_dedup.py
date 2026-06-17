"""
Asana 去重 + Task 建立腳本
確保同一候選人不會被重複觸達，並在 Asana 建立追蹤 Task
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

ASANA_TOKEN = os.getenv("ASANA_TOKEN")
ASANA_PROJECT_GID = os.getenv("ASANA_PROJECT_GID")

HEADERS = {
    "Authorization": f"Bearer {ASANA_TOKEN}",
    "Content-Type": "application/json",
}

BASE_URL = "https://app.asana.com/api/1.0"

SECTION_MAP = {
    "01-Target": None,
    "02-Contacted": None,
    "03-Responded": None,
    "04-Interview": None,
    "05-Offer": None,
    "06-Hired": None,
    "07-Nurture": None,
}


def get_project_sections() -> dict:
    """取得專案所有 Section"""
    url = f"{BASE_URL}/projects/{ASANA_PROJECT_GID}/sections"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()

    sections = {}
    for section in resp.json().get("data", []):
        sections[section["name"]] = section["gid"]

    return sections


def get_existing_tasks() -> set:
    """取得已存在的候選人名單（用 LinkedIn URL 或姓名去重）"""
    url = f"{BASE_URL}/projects/{ASANA_PROJECT_GID}/tasks"
    params = {"opt_fields": "name,notes"}
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()

    existing = set()
    for task in resp.json().get("data", []):
        name = task.get("name", "")
        existing.add(name)

    return existing


def create_task(candidate: dict, section_gid: str, strategy: str) -> dict:
    """在 Asana 建立候選人 Task"""
    name = candidate.get("candidate", {})
    candidate_name = name.get("name", "Unknown")
    title = name.get("title", "")
    company = name.get("company", "")
    linkedin_url = name.get("linkedin_url", "")

    task_name = f"{candidate_name} - {title} - {company}"

    notes = f"""LinkedIn: {linkedin_url}

候選人類型: {candidate.get('candidate_type', '')} - {candidate.get('type_name', '')}
ICP 分數: {candidate.get('icp_score', 0)}
優先級: {candidate.get('priority', '')}
策略來源: {strategy}

發展邏輯:
{candidate.get('development_logic', '')}

個人化鉤子:
{candidate.get('hook', '')}

---
處理時間: {candidate.get('processed_at', '')}
"""

    payload = {
        "data": {
            "name": task_name,
            "notes": notes,
            "projects": [ASANA_PROJECT_GID],
            "memberships": [{"project": ASANA_PROJECT_GID, "section": section_gid}],
        }
    }

    url = f"{BASE_URL}/tasks"
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()

    return resp.json().get("data", {})


def process_analyzed_file(input_path: str, strategy: str = "S1") -> None:
    """處理分析結果，去重後建立 Asana Tasks"""
    with open(input_path, encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"[Asana] 載入 {len(candidates)} 位候選人")

    sections = get_project_sections()
    target_section_gid = sections.get("01-Target")

    if not target_section_gid:
        print("[Warning] 找不到 '01-Target' Section，請先在 Asana 建立 Section")
        return

    existing_tasks = get_existing_tasks()
    print(f"[Asana] 已有 {len(existing_tasks)} 個現有 Task")

    created = 0
    skipped = 0

    for candidate in candidates:
        name_info = candidate.get("candidate", {})
        candidate_name = name_info.get("name", "Unknown")
        title = name_info.get("title", "")
        company = name_info.get("company", "")
        task_name = f"{candidate_name} - {title} - {company}"

        if task_name in existing_tasks:
            print(f"  [Skip] {candidate_name}（已存在）")
            skipped += 1
            continue

        task = create_task(candidate, target_section_gid, strategy)
        print(f"  [Created] {candidate_name} → Task {task.get('gid')}")
        created += 1

    print(f"\n[Done] 新增 {created} 個 Task，跳過 {skipped} 個重複")


def main():
    parser = argparse.ArgumentParser(description="Asana 去重 + Task 建立")
    parser.add_argument("--input", required=True, help="analyzed_*.json 檔案路徑")
    parser.add_argument("--strategy", default="S1", choices=["S1", "S2", "S5", "S6"],
                        help="策略來源標記")

    args = parser.parse_args()
    process_analyzed_file(args.input, args.strategy)


if __name__ == "__main__":
    main()
