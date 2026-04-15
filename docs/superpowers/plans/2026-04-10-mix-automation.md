# Mix Engine Volume Automation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add volume automation to the Vawn Mix Engine so faders move dynamically per song section (verse/chorus/bridge), not just sit at one static level.

**Architecture:** Structure detection via librosa energy analysis → section-aware gain targets → REAPER automation envelope writes via reapy RPR API.

**Tech Stack:** Python, librosa (energy/spectral analysis), reapy (REAPER automation via InsertEnvelopePoint), numpy

**Key Files:**
- `src/utils/structure_detector.py` — NEW: detect song sections from audio
- `src/automation_writer.py` — NEW: write volume automation envelopes to REAPER
- `src/decision_engine.py` — MODIFY: add section-aware gain offsets
- `src/stages/stage1_import.py` — MODIFY: call automation writer after track creation
- `src/stages/pipeline.py` — MODIFY: pass structure data through pipeline

---

## How reapy Automation Works

Confirmed available via RPR (ReaScript API):
```python
from reapy import reascript_api as RPR

# Get volume envelope for a track
envelope = RPR.GetTrackEnvelopeByName(track_id, "Volume")

# Insert a point: (envelope, time_seconds, value, shape, tension, selected)
# shape: 0=linear, 1=square, 2=slow start/end, 3=fast start, 4=fast end, 5=bezier
# value: 0.0-1.0 for volume (0.0=-inf, 1.0=+12dB, 0.716=0dB)
RPR.InsertEnvelopePoint(envelope, time, value, 0, 0.0, False)

# Sort points after adding
RPR.Envelope_SortPoints(envelope)
```

Volume envelope value mapping:
- 0.0 = -inf dB (silence)
- 0.716 = 0 dB (unity gain)
- 1.0 = +12 dB
- Formula: value = 10^(dB/20) * 0.716 (approximately)

---

## Task 1: Structure Detector

**Files:**
- Create: `src/utils/structure_detector.py`

Detect song sections from audio using energy analysis:
1. Load audio via librosa, compute frame-level RMS energy + spectral centroid
2. Smooth with 2-second window
3. Detect significant energy changes as section boundaries
4. Label sections: intro, verse, chorus, bridge, outro based on energy level + position
5. Merge sections shorter than 4 seconds
6. Return list of Section dataclasses (start, end, label, energy)

Also: `detect_structure_from_stems()` — picks the loudest stem for analysis (usually vocal or drum bus).

Test: `python -m src.main analyze sessions/her_place/stems` should show detected sections.

---

## Task 2: Section-Aware Gain Targets

**Files:**
- Modify: `src/decision_engine.py`

Add per-section gain offsets relative to the base gain:

```python
SECTION_OFFSETS = {
    # (stem_type, section_label) -> dB offset from base gain
    ("LEAD", "chorus"):  +1.0,   # vocal pushes forward in chorus
    ("LEAD", "verse"):    0.0,   # vocal at normal in verse
    ("LEAD", "bridge"):  -0.5,   # vocal slightly back in bridge
    ("LEAD", "intro"):   -2.0,   # vocal tucked in intro
    ("LEAD", "outro"):   -1.5,   # vocal fading in outro
    ("PERC", "chorus"):  +0.5,   # drums push in chorus
    ("PERC", "verse"):    0.0,
    ("PERC", "bridge"):  -1.0,   # drums pull back in bridge
    ("KEYS", "chorus"):  -1.0,   # support pulls back when vocal pushes
    ("KEYS", "verse"):   +0.5,   # support fills verse space
    ("SYN", "chorus"):   -1.0,
    ("SYN", "verse"):    +0.5,
    ("808", "chorus"):   +0.5,   # bass pushes with drums
    ("808", "bridge"):   -1.5,   # bass drops in bridge
    ("BASS", "chorus"):  +0.5,
    ("BASS", "bridge"):  -1.5,
}
```

New function: `compute_section_gains(analysis, sections, mix_context)` returns a list of `(time, gain_db)` pairs per stem.

---

## Task 3: Automation Writer

**Files:**
- Create: `src/automation_writer.py`

Write volume automation envelopes to REAPER tracks:

1. `write_volume_automation(reaper_client, track_index, gain_points, fade_time=0.5)`
   - gain_points: list of (time_seconds, gain_db) from decision engine
   - Convert dB to envelope value (0.0-1.0 scale)
   - Add fade_time ramp between sections (0.5s default — smooth transition)
   - Use RPR.InsertEnvelopePoint with linear shape (0)
   - Sort points after writing
   - Set track automation mode to "read" (plays back automation)

2. `db_to_envelope_value(db)` — convert dB offset to REAPER volume envelope value

3. `clear_automation(reaper_client, track_index)` — remove existing automation points

---

## Task 4: Pipeline Integration

**Files:**
- Modify: `src/stages/stage1_import.py` — after track creation and gain staging, call automation writer
- Modify: `src/stages/pipeline.py` — detect structure before Stage 1, pass sections through

Flow:
```
Pipeline starts
  → detect_structure_from_stems(stems_dir)
  → pass sections to Stage 1
    → Stage 1 creates tracks, applies static gain
    → For each track: compute_section_gains() → write_volume_automation()
  → Stage 2-4 run as normal (FX processing)
```

---

## Task 5: Dry-Run Support

**Files:**
- Modify: `src/main.py` — dry-run should show detected sections and planned automation

Dry-run output should show:
```
+== Sections Detected ==
|  [0.0 - 8.2]   intro    energy=0.25
|  [8.2 - 32.5]  verse    energy=0.65
|  [32.5 - 56.0] chorus   energy=0.92
|  [56.0 - 80.3] verse    energy=0.61
|  [80.3 - 104.0] chorus  energy=0.89
|  [104.0 - 120.0] outro  energy=0.30

+== Volume Automation ==
|  LEAD_main: verse=0dB, chorus=+1dB, bridge=-0.5dB
|  PERC_drumbus: verse=0dB, chorus=+0.5dB, bridge=-1dB
|  BASS_main: verse=0dB, chorus=+0.5dB, bridge=-1.5dB
```

---

## Verification

1. Dry-run shows detected sections for "Her Place"
2. Run on REAPER — volume envelopes visible on all tracks
3. Play back — faders move at section boundaries
4. Vocal pushes forward in chorus, instruments duck
5. Transitions are smooth (0.5s fades, no clicks)
6. Mix bus stays below -6 dBFS throughout
