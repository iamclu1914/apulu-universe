---
name: daily-image-processor
description: Daily scan of Vawn folder for new images — auto-rename by content, watermark check, and export to Social_Media_Exports at 1080×1920 (9:16).
---

You are running a daily automated image processing task for the Vawn artist folder. Follow every step below in order.

---

## OBJECTIVE
Scan the source folder for newly added images that have not yet been exported. For each new image: check for watermarks, rename it descriptively based on its visual content, then export it to the single Social_Media_Exports folder at 1080×1920 (9:16).

---

## PATHS

- **Source folder:** `/sessions/peaceful-loving-franklin/mnt/Vawn`
- **Export folder:** `/sessions/peaceful-loving-franklin/mnt/Vawn/Social_Media_Exports`
- **Single output format:** 1080×1920 (9:16 vertical) — all platforms use this size

---

## STEP 1 — FIND NEW IMAGES

Collect all image files in the source folder root only (not subfolders). Supported extensions: `.jpg`, `.jpeg`, `.png`, `.webp`.

An image is considered **new / unprocessed** if its base name (stem) does NOT already exist in the `Social_Media_Exports` folder. Build a list of only these new files.

If there are no new images, print "No new images found. Nothing to do." and stop.

---

## STEP 2 — WATERMARK CHECK

For each new image, scan for Google Gemini or Nana Banana watermarks using this approach:

```python
from PIL import Image, ImageEnhance
import pytesseract
import numpy as np

KEYWORDS = ['nana', 'banana', 'gemini', 'google', 'imagen']

def has_text_watermark(img):
    w, h = img.size
    strip = img.crop((0, int(h * 0.85), w, h))
    strip = strip.resize((min(w, 800), max(50, int(strip.height * 800 / w))), Image.LANCZOS)
    strip = strip.convert('L')
    strip = ImageEnhance.Contrast(strip).enhance(2.5)
    text = pytesseract.image_to_string(strip, config='--psm 11 --oem 3').lower()
    inverted = strip.point(lambda p: 255 - p)
    text += pytesseract.image_to_string(inverted, config='--psm 11 --oem 3').lower()
    return any(kw in text for kw in KEYWORDS)

def has_gemini_colors(img):
    arr = np.array(img.convert('RGB'), dtype=np.float32)
    h, w = arr.shape[:2]
    ch, cw = max(h // 10, 40), max(w // 10, 40)
    corners = [arr[:ch, :cw], arr[:ch, -cw:], arr[-ch:, :cw], arr[-ch:, -cw:]]
    for c in corners:
        cr, cg, cb = c[:,:,0], c[:,:,1], c[:,:,2]
        hits = ((cr < 120) & (cg > 100) & (cb > 180)).sum()
        hits += ((cr > 80) & (cr < 200) & (cg < 80) & (cb > 180)).sum()
        hits += ((cr < 80) & (cg > 160) & (cb > 180)).sum()
        if hits > 30:
            return True
    return False
```

**If watermark detected:** Delete the image from the source folder and skip it. Log which file was removed and why. Do NOT process it further.

---

## STEP 3 — RENAME BY CONTENT

For each image that passed the watermark check, determine if it needs renaming. An image needs renaming if its filename matches any of these patterns:
- Generic camera names: `IMG_`, `DSC_`, `DCIM`, `PHOTO_`, `image_`, `photo_`
- Date-only names (e.g. `20240315_123456`)
- Screenshot names: `Screenshot`, `screen_`
- Very short names under 8 characters (excluding extension)
- Names with only numbers
- Names starting with `hf_` followed by a date/UUID pattern

For images that need renaming:
1. Use your vision capability to look at the image
2. Generate a descriptive kebab-case filename that captures: subject, setting, mood/action (e.g. `vawn-studio-headphones-focused`, `artist-recording-booth-closeup`, `backstage-mirror-reflection`)
3. Keep names under 50 characters, all lowercase, hyphens only
4. Rename the file in the source folder
5. Update your working list to use the new filename

---

## STEP 4 — EXPORT TO SOCIAL_MEDIA_EXPORTS

For each valid image, export it to `Social_Media_Exports` at **1080×1920 (9:16)** using face-aware crop + resize. No blurred backgrounds — pure crop only.

### Method — Face-Aware Crop + Resize (9:16, no blur)

Detects the largest face in the image and anchors the crop around it so the subject's head is never cut off. Falls back to center crop if no face is detected.

```python
import cv2
import numpy as np
from PIL import Image

_face_cascade = None

def _get_cascade():
    global _face_cascade
    if _face_cascade is None:
        _face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    return _face_cascade

def smart_crop_resize(img, tw=1080, th=1920):
    sw, sh = img.size
    tr = tw / th  # 0.5625 for 9:16

    arr = np.array(img.convert('RGB'))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    faces = _get_cascade().detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40)
    )

    if len(faces) > 0:
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
        cx = x + fw // 2
        cy = y + fh // 2 - int(fh * 0.2)  # slight upward anchor for headroom
    else:
        cx, cy = sw // 2, sh // 2  # center crop fallback

    sr = sw / sh
    if sr > tr:  # source wider — crop sides
        nw = int(sh * tr)
        left = max(0, min(cx - nw // 2, sw - nw))
        img = img.crop((left, 0, left + nw, sh))
    else:  # source taller — crop top/bottom
        nh = int(sw / tr)
        top = max(0, min(cy - nh // 2, sh - nh))
        img = img.crop((0, top, sw, top + nh))

    return img.resize((tw, th), Image.LANCZOS)
```

### Output filename
Use the (renamed) source filename stem + `.jpg`. Save as JPEG quality=95.
Convert mode to RGB before saving.

---

## STEP 5 — REPORT

Print a clear summary:
- How many new images were found
- How many were deleted (watermark)
- How many were renamed and what the old → new names were
- How many were successfully exported to Social_Media_Exports
- Any errors encountered

---

## DEPENDENCIES

Install if not already available:
```
pip install Pillow pytesseract numpy opencv-python --break-system-packages -q
apt-get install -y tesseract-ocr -q
```

`opencv-python` ships with the Haar cascade files needed for face detection — no external model download required.
