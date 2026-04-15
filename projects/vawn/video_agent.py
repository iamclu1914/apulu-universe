"""
video_agent.py — Generates video content for TikTok/Reels.
Daily: Ken Burns effect on Vawn photo (Level 1).
Weekly (--cinematic): Triggers Higgsfield via Apulu backend (Level 2).
Schedule: Windows Task Scheduler, 6:45am daily / Sunday 7am weekly.
"""

import argparse
import os
import random
import subprocess
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from vawn_config import (
    load_json, CONTENT_CALENDAR, VAWN_DIR, VAWN_PICS, EXPORTS_DIR,
    log_run, today_str,
)


def get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def pick_photo(keywords=None):
    images = [
        f for f in os.listdir(VAWN_PICS)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
        and f.startswith("vawn-")
    ]
    if not images:
        raise RuntimeError("No vawn- prefixed images found in Vawn Pics")
    if keywords:
        kw = [k.lower() for k in keywords]
        matched = [f for f in images if any(k in f.lower() for k in kw)]
        if matched:
            images = matched
    return VAWN_PICS / random.choice(images)


def prepare_input_image(img_path, target_w=1080, target_h=1920):
    """Fit image to exact target size."""
    img = Image.open(img_path).convert("RGB")
    scale = max(target_w / img.width, target_h / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - target_w) // 2
    top = (nh - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    return img


AUDIO_DIR = VAWN_DIR / "audio_clips"


def pick_audio_clip():
    """Pick a random audio clip from audio_clips folder. Returns path or None."""
    if not AUDIO_DIR.exists():
        return None
    clips = [
        f for f in os.listdir(AUDIO_DIR)
        if f.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".ogg"))
    ]
    if not clips:
        return None
    return AUDIO_DIR / random.choice(clips)


def overlay_audio_on_video(video_path, output_path, audio_path=None, duration=15):
    """Take a pre-made video, strip its audio, mux in a Vawn audio clip.

    Used for posts where we have a pre-rendered video (Higgsfield, etc.)
    but want the Vawn track as the audio instead of the original.
    """
    ffmpeg = get_ffmpeg_path()
    if audio_path is None:
        audio_path = pick_audio_clip()

    if audio_path is None or not Path(audio_path).exists():
        # No audio — just copy the video as-is
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path

    # Replace video's audio with the Vawn clip, trim to duration
    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration),
        "-shortest",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"[WARN] Audio overlay failed, using original: {result.stderr[:200]}")
        import shutil
        shutil.copy2(video_path, output_path)
    else:
        print(f"[OK] Overlaid Vawn audio: {Path(audio_path).name} onto {Path(video_path).name}")
    return output_path


def ken_burns_video(img_path, output_path, duration=15, audio_path=None):
    """Create Ken Burns video. If audio_path provided, mixes audio in."""
    ffmpeg = get_ffmpeg_path()

    prepared = prepare_input_image(img_path, 1080, 1920)
    temp_input = VAWN_DIR / "temp" / "kb_input.png"
    temp_input.parent.mkdir(exist_ok=True)
    prepared.save(temp_input, quality=95)

    fps = 25
    total_frames = duration * fps

    # Step 1: Generate silent video from static image
    temp_video = VAWN_DIR / "temp" / "kb_silent.mp4"
    cmd_video = [
        ffmpeg,
        "-y",
        "-loop", "1",
        "-i", str(temp_input),
        "-t", str(duration),
        "-r", str(fps),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        str(temp_video),
    ]

    result = subprocess.run(cmd_video, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg video failed: {result.stderr[:500]}")

    # Step 2: Mux audio if available
    if audio_path and Path(audio_path).exists():
        print(f"[OK] Audio: {Path(audio_path).name}")
        # Copy video stream + copy audio stream as-is (no re-encode)
        # Audio clips already have fades baked in from the cut step
        cmd_mux = [
            ffmpeg,
            "-y",
            "-i", str(temp_video),
            "-i", str(audio_path),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "copy",
            "-t", str(duration),
            str(output_path),
        ]
        result = subprocess.run(cmd_mux, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"[WARN] Audio mux failed, using silent video: {result.stderr[:200]}")
            import shutil
            shutil.copy2(temp_video, output_path)
        temp_video.unlink(missing_ok=True)
    else:
        # No audio — just rename silent video to output
        import shutil
        shutil.move(str(temp_video), str(output_path))

    temp_input.unlink(missing_ok=True)
    return output_path


def make_tiktok_video(image_path, duration=15):
    """
    Create a TikTok-ready Ken Burns video from an image, with audio if available.
    Called by post_vawn.py before uploading to TikTok.
    Returns path to the video file.
    """
    audio = pick_audio_clip()
    temp_dir = VAWN_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)
    stem = Path(image_path).stem
    out_path = temp_dir / f"tiktok-{stem}.mp4"

    ken_burns_video(image_path, out_path, duration=duration, audio_path=audio)
    has_audio = "with audio" if audio else "silent"
    print(f"[OK] TikTok video ready ({has_audio}): {out_path.name}")
    return out_path


def make_slideshow_reel(image_paths, duration=15):
    """
    Create a slideshow Reel from multiple images with audio.
    Each image gets equal time with a crossfade transition.
    Returns path to the video file.
    """
    ffmpeg = get_ffmpeg_path()
    audio = pick_audio_clip()
    temp_dir = VAWN_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)

    n_images = len(image_paths)
    seconds_per_image = duration / n_images
    fps = 25

    # Prepare each image to 1080x1920 — fit-to-fill, no extra zoom
    prepared_paths = []
    for i, img_path in enumerate(image_paths):
        img = Image.open(img_path).convert("RGB")
        # Scale to cover 1080x1920 exactly (no 1.4x headroom — no zoom needed)
        scale = max(1080 / img.width, 1920 / img.height)
        nw, nh = int(img.width * scale), int(img.height * scale)
        img = img.resize((nw, nh), Image.LANCZOS)
        left = (nw - 1080) // 2
        top = (nh - 1920) // 2
        img = img.crop((left, top, left + 1080, top + 1920))
        p = temp_dir / f"slide_{i}.png"
        img.save(p, quality=95)
        prepared_paths.append(p)

    # Build FFmpeg filter: concat images with crossfade transitions
    inputs = []
    filter_parts = []
    for i, p in enumerate(prepared_paths):
        inputs.extend(["-loop", "1", "-t", str(seconds_per_image + 0.5), "-i", str(p)])
        filter_parts.append(f"[{i}:v]fps={fps},scale=1080:1920,setsar=1[v{i}]")

    # Chain crossfades between slides (0.5s each)
    fade_dur = 0.5
    if n_images == 1:
        filter_chain = f"{';'.join(filter_parts)};[v0]trim=0:{duration}[outv]"
    else:
        filter_chain = ";".join(filter_parts)
        prev = "v0"
        for i in range(1, n_images):
            offset = seconds_per_image * i - fade_dur * i
            out_label = f"xf{i}" if i < n_images - 1 else "outv"
            filter_chain += f";[{prev}][v{i}]xfade=transition=fade:duration={fade_dur}:offset={offset:.2f}[{out_label}]"
            prev = out_label

    # Generate silent video
    silent_path = temp_dir / "slideshow_silent.mp4"
    cmd = [ffmpeg, "-y"] + inputs + [
        "-filter_complex", filter_chain,
        "-map", "[outv]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "23",
        "-t", str(duration),
        silent_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(f"Slideshow FFmpeg failed: {result.stderr[:500]}")

    # Mux audio
    out_path = temp_dir / "slideshow_reel.mp4"
    if audio and Path(audio).exists():
        print(f"[OK] Slideshow audio: {Path(audio).name}")
        cmd_mux = [
            ffmpeg, "-y",
            "-i", str(silent_path),
            "-i", str(audio),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "copy",
            "-t", str(duration),
            str(out_path),
        ]
        r = subprocess.run(cmd_mux, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print(f"[WARN] Audio mux failed: {r.stderr[:200]}")
            import shutil
            shutil.copy2(silent_path, out_path)
    else:
        import shutil
        shutil.copy2(silent_path, out_path)

    # Cleanup temp slides
    for p in prepared_paths:
        p.unlink(missing_ok=True)
    silent_path.unlink(missing_ok=True)

    has_audio = "with audio" if audio else "silent"
    print(f"[OK] Slideshow Reel ready ({has_audio}, {n_images} images): {out_path.name}")
    return out_path


def daily_video():
    print("\n=== Video Agent (Daily — Ken Burns) ===\n")

    calendar = load_json(CONTENT_CALENDAR)
    today = today_str()

    keywords = []
    for day in calendar.get("calendar", []):
        if day.get("date") == today:
            slot = day.get("slots", {}).get("morning", {})
            keywords = slot.get("image_keyword", [])
            break

    photo = pick_photo(keywords)
    print(f"[OK] Photo: {photo.name}")

    audio = pick_audio_clip()
    if audio:
        print(f"[OK] Audio clip: {audio.name}")
    else:
        print("[INFO] No audio clips in audio_clips/ — video will be silent")

    filename = f"vawn-kenburns-{today}.mp4"

    EXPORTS_DIR.mkdir(exist_ok=True)
    out_path = EXPORTS_DIR / filename
    ken_burns_video(photo, out_path, duration=15, audio_path=audio)
    print(f"[OK] Exported to Social_Media_Exports")

    log_run("VideoAgent", "ok", f"Ken Burns exported: {filename}")
    print(f"\n[OK] Video exported as '{filename}' to Social_Media_Exports")


def cinematic_video():
    print("\n=== Video Agent (Weekly — Cinematic) ===\n")

    import requests
    from vawn_config import CREDS_FILE, load_json as lj

    creds = lj(CREDS_FILE)
    base_url = "https://apulustudio.onrender.com/api"

    r = requests.post(f"{base_url}/auth/refresh", json={"refresh_token": creds["refresh_token"]})
    if r.status_code != 200:
        log_run("VideoAgent-Cinematic", "error", f"Token refresh failed: {r.status_code}")
        print("[FAIL] Token refresh failed")
        return

    tokens = r.json()
    access_token = tokens["access_token"]

    calendar = load_json(CONTENT_CALENDAR)
    today = today_str()
    anchor = "Still moving through the city that made me"
    for day in calendar.get("calendar", []):
        if day.get("date") == today:
            slot = day.get("slots", {}).get("morning", {})
            anchor = slot.get("anchor_line", anchor)
            break

    print(f"[OK] Theme: {anchor}")
    print("[INFO] Cinematic video generation via Apulu backend — this may take several minutes")

    payload = {
        "messages": [{"role": "user", "content": f"Create a Higgsfield Cinema music video scene for Vawn based on: {anchor}"}],
        "mode": "hf-story",
        "scenes": 4,
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(f"{base_url}/messages", headers=headers, json=payload, timeout=300)

    if r.status_code == 200:
        log_run("VideoAgent-Cinematic", "ok", f"Cinematic video triggered: {anchor[:50]}")
        print(f"[OK] Cinematic video generation triggered")
    else:
        log_run("VideoAgent-Cinematic", "error", f"API error: {r.status_code} {r.text[:200]}")
        print(f"[FAIL] Cinematic trigger failed: {r.status_code}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cinematic", action="store_true", help="Weekly Higgsfield cinematic video")
    args = parser.parse_args()

    if args.cinematic:
        cinematic_video()
    else:
        daily_video()


if __name__ == "__main__":
    main()
