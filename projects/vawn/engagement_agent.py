"""
engagement_agent.py — Monitors and responds to comments across all 5 platforms.
Generates replies in Vawn's voice. Runs every 2 hours via Windows Task Scheduler.
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


def fetch_comments(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(f"{BASE_URL}/posts/comments", headers=headers, timeout=30)
        if r.status_code == 404:
            print("[INFO] Comments endpoint not available yet — skipping")
            return []
        r.raise_for_status()
        return r.json().get("comments", [])
    except requests.exceptions.RequestException as e:
        print(f"[WARN] Could not fetch comments: {e}")
        return []


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
    print("\n=== Engagement Agent ===\n")

    try:
        access_token = refresh_token()
    except Exception as e:
        log_run("EngagementAgent", "error", f"Auth failed: {e}")
        print(f"[FAIL] Auth: {e}")
        return

    comments = fetch_comments(access_token)
    if not comments:
        log_run("EngagementAgent", "ok", "No comments to process")
        print("[OK] No comments to process")
        return

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
    save_json(ENGAGEMENT_LOG, log)

    log_run("EngagementAgent", "ok", f"{reply_count} replies generated")
    print(f"\n[OK] {reply_count} replies generated")


if __name__ == "__main__":
    main()
