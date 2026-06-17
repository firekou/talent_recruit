"""
候選人處理器：ICP 評分 + 候選人類型判斷 + 三封信話術生成
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OUTPUT_DIR = Path(__file__).parent.parent / "candidate-drafts"
OUTPUT_DIR.mkdir(exist_ok=True)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


ICP_SCORE_PROMPT = """你是一個招募系統，負責評估 LinkedIn 候選人是否符合我們的目標候選人輪廓（TCP）。

TCP 定義：
- 工作年資：3–10 年
- 地區：台灣
- 職位類型：BizDev / PM / Engineer / Marketing / Operations
- 加分：最近有更新 LinkedIn、有發文、公司有變動訊號

請根據以下候選人資料，輸出 JSON：
{{
  "icp_score": 0-100,
  "candidate_type": "A/B/C/D",
  "type_name": "職涯轉型者/成長停滯者/影響力驅動者/被動觀望者",
  "development_logic": "50字以內，職涯邏輯",
  "key_turning_point": "最關鍵的職涯轉折",
  "next_move": "他下一步可能走向哪裡",
  "approach_role": "我們應以什麼身份出現",
  "hook": "連線邀請的個人化切入點",
  "priority": "HIGH/MEDIUM/LOW"
}}

候選人資料：
{candidate_data}
"""

OUTREACH_PROMPT = """你是 Talent-Scout，專業的 LinkedIn 人才開發 Agent。

根據以下候選人分析，生成三封信序列。

候選人分析：
{analysis}

輸出格式：
【連線邀請】（≤200字）
[內容]

【第一封 Day 1】（≤300字）
[內容]

【第二封 有回覆版 Day 5-7】（≤300字）
[內容]

【第二封 無回覆追蹤版 Day 5-7】（≤250字）
[內容]

【第三封 引入機會 Day 8-12】（≤350字）
[內容]
"""


def score_candidate(candidate: dict) -> dict:
    """評估候選人 ICP 分數與類型"""
    candidate_summary = json.dumps(candidate, ensure_ascii=False, indent=2)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": ICP_SCORE_PROMPT.format(candidate_data=candidate_summary)
        }]
    )

    response_text = message.content[0].text
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        analysis = json.loads(response_text[start:end])
    except json.JSONDecodeError:
        analysis = {"raw_response": response_text, "icp_score": 0}

    analysis["candidate"] = {
        "name": candidate.get("fullName", ""),
        "title": candidate.get("headline", ""),
        "company": candidate.get("companyName", ""),
        "linkedin_url": candidate.get("profileUrl", ""),
    }

    return analysis


def generate_outreach(analysis: dict) -> str:
    """生成三封信話術"""
    analysis_text = json.dumps(analysis, ensure_ascii=False, indent=2)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": OUTREACH_PROMPT.format(analysis=analysis_text)
        }]
    )

    return message.content[0].text


def process_candidates(input_path: str, min_score: int = 60) -> str:
    """處理整批候選人"""
    with open(input_path, encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"[Process] 載入 {len(candidates)} 位候選人")

    results = []
    for i, candidate in enumerate(candidates, 1):
        print(f"[{i}/{len(candidates)}] 處理：{candidate.get('fullName', 'Unknown')}")

        analysis = score_candidate(candidate)

        if analysis.get("icp_score", 0) < min_score:
            print(f"  → ICP 分數 {analysis.get('icp_score')} < {min_score}，跳過")
            continue

        outreach = generate_outreach(analysis)
        analysis["outreach_drafts"] = outreach
        analysis["processed_at"] = datetime.now().isoformat()

        results.append(analysis)
        print(f"  → 類型 {analysis.get('candidate_type')}，分數 {analysis.get('icp_score')}，優先級 {analysis.get('priority')}")

    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = OUTPUT_DIR / f"analyzed_{date_str}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[Done] {len(results)} 位候選人通過篩選，結果儲存：{output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="候選人分析與話術生成")
    parser.add_argument("--input", required=True, help="輸入 JSON 檔案路徑")
    parser.add_argument("--min-score", type=int, default=60, help="最低 ICP 分數門檻")

    args = parser.parse_args()
    process_candidates(args.input, args.min_score)


if __name__ == "__main__":
    main()
