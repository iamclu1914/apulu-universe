"""
dm_welcome.py — Automated DM welcome messages.

STATUS: NOT AUTOMATED — API limitations prevent this.

The LATE API (used for Instagram, TikTok, Threads, X) does not support sending DMs.
The Bluesky AT Protocol has limited DM support but it's not stable.

MANUAL ALTERNATIVES (set these up once in each app):
1. Instagram: Settings > Business > Saved Replies > Create an auto-reply
   - Or use Meta Business Suite > Inbox > Automated Responses > Instant Reply
   - Message: "appreciate you being here. album dropping soon — you'll hear it first."

2. TikTok: No auto-DM feature available.

3. X: Settings > Direct Messages > Quick Reply
   - Set up a greeting message for new followers.

4. Threads: No DM feature at all.

5. Bluesky: No auto-DM feature.

FUTURE: When LATE or platform APIs add DM support, this script can be extended.
"""

def main():
    print("\n=== DM Welcome Agent — Status ===\n")
    print("Auto-DMs are NOT available through current APIs.")
    print()
    print("Set these up MANUALLY (one-time, 5 minutes):")
    print()
    print("  Instagram:")
    print("    Meta Business Suite > Inbox > Automated Responses > Instant Reply")
    print("    Message: \"appreciate you being here. album dropping soon.\"")
    print()
    print("  X/Twitter:")
    print("    Settings > Direct Messages > set a greeting message")
    print()
    print("  TikTok / Threads / Bluesky:")
    print("    No auto-DM available on these platforms.")
    print()


if __name__ == "__main__":
    main()
