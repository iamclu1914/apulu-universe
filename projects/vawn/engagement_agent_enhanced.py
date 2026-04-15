"""
engagement_agent_enhanced.py — Enhanced monitoring with API health checking for APU-37.
Monitors and responds to comments across all 5 platforms with improved status reporting.
Created by: Dex - Community Agent (APU-37)
"""

import json
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
import requests
from datetime import datetime
from vawn_config import (
    get_anthropic_client, load_json, save_json, CREDS_FILE,
    ENGAGEMENT_LOG, VAWN_PROFILE, log_run, today_str,
)

BASE_URL = "https://apulustudio.onrender.com/api"
MAX_REPLIES_PER_RUN = 10
SKIP_PATTERNS = ["follow me", "check my", "dm me", "collab?", "promo"]


def refresh_token():
    creds = load_json(CREDS_FILE)
    r = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": creds["refresh_token"]})
    if r.status_code != 200:
        raise RuntimeError(f"Token refresh failed: {r.status_code}")
    data = r.json()
    creds["access_token"] = data["access_token"]
    creds["refresh_token"] = data["refresh_token"]
    save_json(CREDS_FILE, creds)
    return data["access_token"]


def check_api_health(access_token):
    """Check if comments API is available and measure response time."""
    headers = {"Authorization": f"Bearer {access_token}"}
    start_time = datetime.now()

    try:
        r = requests.get(f"{BASE_URL}/posts/comments", headers=headers, timeout=10)
        response_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "available": r.status_code != 404,
            "status_code": r.status_code,
            "response_time_ms": int(response_time),
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.RequestException as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "available": False,
            "error": str(e),
            "response_time_ms": int(response_time),
            "timestamp": datetime.now().isoformat()
        }


def fetch_comments_enhanced(access_token):
    """Enhanced comment fetching with detailed status reporting."""
    # First check API health
    health_status = check_api_health(access_token)

    if not health_status["available"]:
        if "error" in health_status:
            status_detail = f"API connection error: {health_status['error']}"
        else:
            status_detail = f"Comments endpoint unavailable (HTTP {health_status['status_code']})"

        return {
            "comments": [],
            "status": "api_unavailable",
            "status_detail": status_detail,
            "health": health_status
        }

    # API is available, fetch comments
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(f"{BASE_URL}/posts/comments", headers=headers, timeout=30)
        r.raise_for_status()
        comments = r.json().get("comments", [])

        return {
            "comments": comments,
            "status": "success",
            "status_detail": f"Retrieved {len(comments)} comments successfully",
            "health": health_status
        }

    except requests.exceptions.RequestException as e:
        return {
            "comments": [],
            "status": "fetch_error",
            "status_detail": f"Error fetching comments: {e}",
            "health": health_status
        }


def is_spam(comment_text):
    text_lower = comment_text.lower()
    if len(text_lower) <= 3:
        return True
    if all(c in "🔥💯❤️👏🙏💪👀😤🤝✊" for c in text_lower.replace(" ", "")):
        return True
    return any(p in text_lower for p in SKIP_PATTERNS)


def already_replied(comment_id, log):
    replied = log.get("replied_ids", [])
    return comment_id in replied


def generate_reply(client, comment_text, post_caption=""):
    prompt = f"""You are replying to a social media comment as Vawn.

VAWN'S VOICE:
{VAWN_PROFILE}
- Replies are warm but not soft. Brooklyn/ATL. Lyrical when it fits.
- Short: 1-3 sentences max.
- Never promotional in replies. Just human connection.
- Acknowledge what the commenter actually said.
- Never reveal you're AI. Never say "I appreciate your support" or generic phrases.

ORIGINAL POST CAPTION (for context):
{post_caption[:200] if post_caption else "(no caption available)"}

COMMENT TO REPLY TO:
{comment_text}

Write a reply. Plain text only, no emojis unless one fits naturally. No hashtags."""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def post_reply(access_token, comment_id, reply_text, platform):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.post(
            f"{BASE_URL}/posts/comments/{comment_id}/reply",
            headers=headers,
            json={"content": reply_text},
            timeout=30,
        )
        if r.status_code == 404:
            print(f"[INFO] Reply endpoint not available for {platform} — logged only")
            return False
        r.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"[WARN] Could not post reply on {platform}: {e}")
        return False


def main():
    print("\n=== Enhanced Engagement Agent (APU-37) ===\n")

    try:
        access_token = refresh_token()
        print("[OK] Authentication successful")
    except Exception as e:
        log_run("EngagementAgentEnhanced", "error", f"Auth failed: {e}")
        print(f"[FAIL] Auth: {e}")
        return

    # Enhanced comment fetching with status reporting
    result = fetch_comments_enhanced(access_token)
    health = result["health"]

    print(f"[API] Status: {result['status']}")
    print(f"[API] Response time: {health['response_time_ms']}ms")
    print(f"[API] Detail: {result['status_detail']}")

    # Log detailed status for monitoring
    if result["status"] == "api_unavailable":
        log_run("EngagementAgentEnhanced", "warning", f"API unavailable: {result['status_detail']}")
        print("[WARN] Comments API is unavailable - cannot process comments")

        # Save API health status for monitoring dashboard
        health_log = load_json("research/api_health_log.json") if load_json("research/api_health_log.json") else {}
        today = today_str()
        if today not in health_log:
            health_log[today] = []
        health_log[today].append({
            "timestamp": health["timestamp"],
            "service": "comments_api",
            "available": health["available"],
            "status_code": health.get("status_code"),
            "response_time_ms": health["response_time_ms"],
            "error": health.get("error")
        })
        save_json("research/api_health_log.json", health_log)
        return

    elif result["status"] == "fetch_error":
        log_run("EngagementAgentEnhanced", "error", f"Fetch error: {result['status_detail']}")
        print(f"[ERROR] Failed to fetch comments: {result['status_detail']}")
        return

    # API is working, process comments
    comments = result["comments"]
    if not comments:
        log_run("EngagementAgentEnhanced", "ok", "API healthy, no comments to process")
        print("[OK] API is healthy, no comments to process")
        return

    print(f"[OK] Found {len(comments)} comments to process")

    log = load_json(ENGAGEMENT_LOG)
    if "replied_ids" not in log:
        log["replied_ids"] = []
    if "history" not in log:
        log["history"] = []

    client = get_anthropic_client()
    reply_count = 0

    for comment in comments:
        if reply_count >= MAX_REPLIES_PER_RUN:
            print(f"[INFO] Rate limit reached ({MAX_REPLIES_PER_RUN} replies)")
            break

        cid = comment.get("id", "")
        text = comment.get("text", "")
        platform = comment.get("platform", "unknown")
        caption = comment.get("post_caption", "")

        if not text or is_spam(text) or already_replied(cid, log):
            continue

        print(f"[{platform}] Comment: {text[:60]}...")
        reply = generate_reply(client, text, caption)
        print(f"  Reply: {reply[:60]}...")

        posted = post_reply(access_token, cid, reply, platform)

        log["replied_ids"].append(cid)
        log["history"].append({
            "date": datetime.now().isoformat(),
            "platform": platform,
            "comment": text[:200],
            "reply": reply,
            "posted": posted,
        })
        reply_count += 1

    # Keep log manageable — only last 500 replied IDs
    log["replied_ids"] = log["replied_ids"][-500:]
    log["history"] = log["history"][-200:]
    log["last_updated"] = datetime.now().isoformat()
    log["api_health"] = health
    save_json(ENGAGEMENT_LOG, log)

    # Enhanced logging with API health status
    status_msg = f"{reply_count} replies generated, API response: {health['response_time_ms']}ms"
    log_run("EngagementAgentEnhanced", "ok", status_msg)
    print(f"\n[OK] {status_msg}")


if __name__ == "__main__":
    main()