#!/usr/bin/env python3
"""
plan_weekly_campaign.py — Frontier-Grade Weekly Campaign Planner for Fanvue & Bluesky.
Uses OpenRouter to access uncensored frontier models (Hermes 3 70B/405B, DeepSeek V3)
to generate synchronized 7-day paired campaigns:
  - Fanvue Exclusive Drop (full high-res image/video prompt + caption)
  - Bluesky Teaser Drop (soft-NSFW crop prompt + hook + matching truthful CTA)
Enforces all canonical rules from qwen_fanvue_operator_prompt.md.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request
import urllib.error

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
PROMPT_FILE = GROWTH_DIR / "qwen_fanvue_operator_prompt.md"
SCHEDULE_OUTPUT = GROWTH_DIR / "schedule_assets" / "campaign_schedule.json"

DEFAULT_MODEL = "nousresearch/hermes-3-llama-3.1-70b"

PLANNER_SYSTEM_PROMPT = """You are the Lead Creative Director and Campaign Strategist for Seo-yeon Han (@syeon.hn on Fanvue, @syeonhn.bsky.social on Bluesky).
Your task is to plan a complete 7-day synchronized content calendar where Bluesky teasers and Fanvue exclusive drops are 100% paired and truth-aligned.

CRITICAL PAIRING RULE (Truth in Advertising):
- If the Bluesky post says "shared the full morning set on my private feed", the Fanvue post MUST be that exact morning set.
- NEVER claim "fully uncensored" or "towel drop" unless the paired Fanvue post explicitly contains that exact content.
- Every single day has TWO linked drops:
  1. FANVUE EXCLUSIVE DROP: What paying subscribers receive ($9.99/mo or PPV unlock).
  2. BLUESKY TEASER DROP: The organic soft-NSFW hook on Bluesky driving traffic to Fanvue via tracking link (https://www.fanvue.com/syeon.hn?c=fv-4).

PROMPT CREATION RULES (Anti-Defect):
1. Zero body/waist prompting: Never describe waist, midriff, or body curves in prompts. Rely 100% on master references (c5_relax_front, a1_front).
2. Relaxed neck and shoulders: Always specify relaxed neck and shoulders, soft natural clavicles with zero strained cords.
3. Flawless decoupled hands: Exactly five natural fingers on phone hand; other arm resting casually.
4. Phone hardware: White iPhone 15 Pro with white back glass, natural titanium edges, and clear transparent case.
5. Realistic sensor: Flat natural contrast, low saturation, natural matte skin texture with real visible pores, zero CGI gloss.
6. Background variety: Varied aesthetic private environments (sunlit bedroom, cozy living room, morning kitchen, bathroom, balcony, boutique suite, moody lamplight).

OUTPUT FORMAT:
You MUST respond with a pure JSON array containing exactly 7 objects (Monday to Sunday).
Do NOT include markdown backticks around the JSON. Output raw JSON only.

Schema for each day:
{
  "day": "Monday",
  "theme": "Concept Name",
  "fanvue_drop": {
    "media_type": "image",
    "prompt": "Detailed photorealistic Seedream 5 Pro prompt for the full Fanvue asset...",
    "caption": "lowercase intimate caption in Seo-yeon's voice...",
    "audience": "subscribers",
    "price_cents": 0
  },
  "bluesky_teaser": {
    "media_type": "image",
    "prompt": "Detailed photorealistic prompt for the soft-NSFW teaser/crop...",
    "hook_text": "candid lowercase hook for Bluesky...",
    "cta_reply_text": "threaded reply with truth-aligned CTA pointing to https://www.fanvue.com/syeon.hn?c=fv-4",
    "time_kst": "08:30"
  }
}
"""

def get_openrouter_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return key

def call_openrouter(prompt: str, model: str, api_key: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4096
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Protoxid/seoyeon-bluesky",
            "X-Title": "Seoyeon Twin-Drop Campaign Planner"
        },
        method="POST"
    )
    
    print(f"[*] Querying frontier model '{model}' via OpenRouter...")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        sys.exit(f"OpenRouter HTTP Error {e.code}: {err_msg}")
    except Exception as e:
        sys.exit(f"Network error contacting OpenRouter: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate 7-day synchronized Fanvue & Bluesky campaign.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"OpenRouter model slug (default: {DEFAULT_MODEL})")
    parser.add_argument("--focus", default="autumn morning intimates, silk slips, rainy evening loungewear, and 1 video diary", help="Weekly theme focus")
    parser.add_argument("--output", default=str(SCHEDULE_OUTPUT), help="Path to save output JSON")
    args = parser.parse_args()

    api_key = get_openrouter_key()
    if not api_key:
        print("\n[!] OPENROUTER_API_KEY environment variable is not set.")
        print("    To use frontier uncensored planning (Hermes 3 70B/405B, DeepSeek V3):")
        print("    1. Sign up at https://openrouter.ai and generate an API key.")
        print("    2. Set it in your terminal:")
        print("       $env:OPENROUTER_API_KEY = 'sk-or-v1-...'")
        print("    3. Re-run this script.\n")
        sys.exit(1)

    user_prompt = f"Please generate a complete 7-day synchronized campaign for next week focusing on: {args.focus}. Make sure one day (Friday) features a video clip for both Fanvue and Bluesky."
    
    raw_response = call_openrouter(user_prompt, args.model, api_key)
    
    # Strip markdown backticks if present
    cleaned = raw_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        schedule_data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[!] Warning: Failed to parse raw JSON: {e}")
        print("--- RAW RESPONSE ---")
        print(raw_response)
        sys.exit(1)

    out_path = pathlib.Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(schedule_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"\n[+] Successfully generated 7-day synchronized campaign!")
    print(f"[+] Saved to: {out_path.resolve()}")
    print("\nSummary of Drops:")
    for item in schedule_data:
        day = item.get("day")
        theme = item.get("theme")
        fv = item.get("fanvue_drop", {})
        bsky = item.get("bluesky_teaser", {})
        print(f"  [{day}] {theme}")
        print(f"     Fanvue: {fv.get('media_type')} | {fv.get('caption', '')[:50]}...")
        print(f"     Bluesky: {bsky.get('time_kst')} KST | Hook: \"{bsky.get('hook_text', '')[:40]}...\"")
        print(f"     CTA: \"{bsky.get('cta_reply_text', '')[:60]}...\"")
        print()

if __name__ == "__main__":
    main()
