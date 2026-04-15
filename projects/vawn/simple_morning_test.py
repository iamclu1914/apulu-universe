#!/usr/bin/env python3
"""
APU-156 Morning Pipeline Simple Test
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import post_vawn
post_vawn.EXPORTS_DIR = post_vawn.EXPORTS_BASE

from post_vawn import *
from datetime import date

def main():
    print("=" * 60)
    print("APU-156 MORNING PIPELINE VALIDATION")
    print("=" * 60)
    print(f"Date: {date.today()}")
    print()

    # Test configuration
    config = CRON_CONFIG['morning']
    print("[CONFIG] Morning configuration loaded")
    print(f"Energy: {config['energy'][:60]}...")
    print(f"Hook strategy: {config['hook']}")
    print(f"Keywords: {len(config['keywords'])} defined")
    print()

    # Test content context
    content_ctx = load_content_context('morning')
    if content_ctx:
        print("[CONTEXT] Content context loaded")
        print(f"Pillar: {content_ctx.get('pillar', 'None')}")
        print(f"Anchor line: {content_ctx.get('anchor_line', 'None')[:50]}...")
        if content_ctx.get('image_keyword'):
            print(f"Image override keywords: {content_ctx['image_keyword']}")
    else:
        print("[CONTEXT] No content context found")
    print()

    # Test image selection
    log = load_json(LOG_FILE)
    today = str(date.today())

    keywords = content_ctx.get('image_keyword') or config.get('keywords', [])
    chosen = pick_image(log, today, keywords=keywords, strategy=config.get('image_strategy', 'random'))

    img_path = EXPORTS_DIR / chosen
    print(f"[IMAGE] Selected: {chosen}")
    print(f"[IMAGE] Exists: {img_path.exists()}")
    print()

    # Test caption generation
    captions = generate_captions(chosen, config['energy'], config['hook'], content_context=content_ctx)
    print(f"[CAPTIONS] Generated for {len(captions)} platforms")

    # Test each platform
    platforms = ['tiktok', 'instagram', 'threads', 'x', 'bluesky']
    for platform in platforms:
        if platform in captions:
            caption = captions[platform]
            char_count = len(caption)
            lines = len(caption.split('\n'))

            # Basic validation
            validation_notes = []

            if platform == 'tiktok' and lines > 2:
                validation_notes.append("Too many lines")
            elif platform == 'instagram':
                hashtag_count = caption.count('#')
                if hashtag_count < 5 or hashtag_count > 15:
                    validation_notes.append(f"Hashtag count: {hashtag_count}")
            elif platform == 'threads' and '#' in caption:
                validation_notes.append("Contains hashtags (should use Topics)")
            elif platform in ['x', 'bluesky'] and char_count > (300 if platform == 'bluesky' else 280):
                validation_notes.append("Exceeds character limit")

            status = "[WARN]" if validation_notes else "[OK]"
            notes = f" ({', '.join(validation_notes)})" if validation_notes else ""
            print(f"{status} {platform.upper()}: {char_count} chars, {lines} lines{notes}")

    print()

    # Test accessibility
    alt_text = generate_alt_text(chosen)
    print(f"[ACCESS] Alt text: {alt_text}")
    print()

    # Test morning energy alignment
    all_content = ' '.join(captions.values()).lower()
    morning_indicators = ['sharp', 'intentional', 'quiet', 'confidence', 'authority', 'focus', 'already']
    found = [word for word in morning_indicators if word in all_content]

    print("[ENERGY] Morning energy check")
    if found:
        print(f"[OK] Found indicators: {found}")
    else:
        print("[WARN] No explicit morning energy words detected")

    # Check for anti-patterns
    anti_patterns = ['lets go', 'crushing', 'grinding', 'beast mode', 'motivation']
    anti_found = [pattern for pattern in anti_patterns if pattern in all_content]

    if not anti_found:
        print("[OK] No hype anti-patterns detected")
    else:
        print(f"[WARN] Anti-patterns found: {anti_found}")
    print()

    # Show sample content
    print("[PREVIEW] Sample content")
    print("-" * 40)
    for platform in ['instagram', 'tiktok', 'threads']:
        if platform in captions:
            caption = captions[platform]
            preview = caption[:150] + "..." if len(caption) > 150 else caption
            print(f"{platform.upper()}:")
            print(preview)
            print("-" * 40)

    print()
    print("VALIDATION COMPLETE")
    print()

    # Test scheduling validation
    print("[SCHEDULE] Testing 9:00 AM scheduling alignment")

    # Check if it's currently morning
    from datetime import datetime
    current_hour = datetime.now().hour
    if 8 <= current_hour <= 10:
        print("[OK] Current time aligns with morning slot")
    else:
        print(f"[INFO] Current time ({current_hour}:xx) - morning is 9:00 AM")

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("[SUCCESS] All validation tests completed")
    else:
        print("[FAIL] Validation failed")