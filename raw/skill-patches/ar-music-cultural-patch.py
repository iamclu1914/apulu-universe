"""
Patch script: inject April 2026 cultural radar directives into ar-music SKILL.md
Run from any terminal: python ar-music-cultural-patch.py
"""
import pathlib, sys

SKILL_PATH = pathlib.Path.home() / ".claude" / "skills" / "ar-music" / "SKILL.md"

OLD = """### 1c. Build Your Cultural Radar Note

Whether sourced from the saved report or fresh research, synthesize into a **Cultural Radar Note** with these four anchors:

1. **Oversaturation** — What specific sounds or tropes are fatigued right now
2. **Emerging** — What's gaining traction that hasn't peaked yet
3. **Cultural mood** — What emotional/social atmosphere the audience is living in
4. **White space for Vawn** — The specific gap his sound can fill given the above

This note should directly drive every creative decision below — producer selection, lyric mode, track concept, and sequencing all flow from it."""

NEW = """### 1c. Build Your Cultural Radar Note

Whether sourced from the saved report or fresh research, synthesize into a **Cultural Radar Note** with these four anchors:

1. **Oversaturation** — What specific sounds or tropes are fatigued right now
2. **Emerging** — What's gaining traction that hasn't peaked yet
3. **Cultural mood** — What emotional/social atmosphere the audience is living in
4. **White space for Vawn** — The specific gap his sound can fill given the above

**When reading the April 2026 radar specifically, extract these signals:**
- *Vibecession as setting, not theme* — financial anxiety + housing instability are the LOCATION, not the concept. Every track should be grounded in a specific ATL material condition (the gentrifying block, the parking lot, the corner store at 2am, the new luxury building casting shadow on old houses). This is Camdyn's active Directive 2.
- *Bass-baritone cinematic lane* — structurally uncrowded in ATL right now. The dominant emerging ATL voices (Nine, Zukenee, SpookDaKiid) are all in the melodic/warbly/rage register. Vawn's identity is the opposite. Name this gap explicitly in the note.
- *Hollywood Toray competitive urgency* — the only named artist in adjacent territory. His positioning isn't locked yet. Speed is a factor. Include a one-line note on this whenever running Project Mode — the first single needs to establish the identity before he does.
- *Lean project mandate* — 10-12 tracks, one conceptual through-line that resolves by the final track. Critical consensus is unambiguous. Never recommend bloat.
- *What's fatigued* — generic trap maximalism, Auto-tune melodic rap as differentiator, 20+ track album formats, high-gloss luxury aesthetics. Don't recommend creative directions that pull toward any of these.

**Active Camdyn Directives (April 2026):**
> **DIRECTIVE 1** — Lock "earned authority" positioning before Hollywood Toray does. Vawn needs a public-facing artifact that establishes the bass-baritone, Atlanta-specific, cinematic identity clearly and first.
> **DIRECTIVE 2** — Write directly into the vibecession with hyper-specific ATL material conditions as SETTING. Every track answers: what specific thing happened, to whom, where.
> **DIRECTIVE 3** — Keep the project 10-12 tracks with a single conceptual through-line. Design around one question or tension Vawn resolves by the final track.

This note should directly drive every creative decision below — producer selection, lyric mode, track concept, and sequencing all flow from it."""

# --- music-composition-skill patch ---
COMP_SKILL_PATH = pathlib.Path.home() / ".claude" / "skills" / "music-composition-skill" / "SKILL.md"

COMP_OLD = """- Gentrification, specifically in Brooklyn and Atlanta
- The immigrant experience as a lived thing, not a talking point
- Race and class observed through specific scenes, not essays"""

COMP_NEW = """- Gentrification, specifically in Brooklyn and Atlanta
- The immigrant experience as a lived thing, not a talking point
- Race and class observed through specific scenes, not essays
- **Vibecession material conditions (April 2026 active):** the gentrifying block (half storefronts shuttered, half boutiques), the parking lot where a new Benz sits next to a car on blocks, the corner store at 2am under fluorescent lights, the new luxury building casting shadow on old houses, the highway overpass at golden hour, the empty barbershop after close. These are SETTINGS, not themes — grounded specificity, not economic anxiety as an abstraction."""

COMP_OLD2 = """### T.I.-mode diagnostic
- [ ] Is there a refrain landing every 2-4 bars?
- [ ] Does bar 1 open with image, not commentary?
- [ ] Does the middle 8 accelerate into the close?
- [ ] Are there at least 2 operational specifics (places, objects, roles)?
- [ ] Is there one counterpunch folded inside a couplet?"""

COMP_NEW2 = """### T.I.-mode diagnostic
- [ ] Is there a refrain landing every 2-4 bars?
- [ ] Does bar 1 open with image, not commentary?
- [ ] Does the middle 8 accelerate into the close?
- [ ] Are there at least 2 operational specifics (places, objects, roles)?
- [ ] Is there one counterpunch folded inside a couplet?

**Vibecession specificity check (April 2026):** At least one operational specific in T.I.-mode verses should be grounded in a material condition — a real ATL or Brooklyn place, object, or situation that names what the audience is living through. "The rent on Bankhead" > "the grind." "The barbershop that's closing next month" > "the block." Vague is the enemy. Specific is the flex."""


def patch_file(path, old_str, new_str, label):
    if not path.exists():
        print(f"ERROR: {label} not found at {path}")
        return False
    content = path.read_text(encoding="utf-8")
    if old_str not in content:
        print(f"SKIP: {label} — target string not found (already patched or changed?)")
        return False
    patched = content.replace(old_str, new_str, 1)
    path.write_text(patched, encoding="utf-8")
    print(f"OK: {label} patched successfully.")
    return True


if __name__ == "__main__":
    ok1 = patch_file(SKILL_PATH, OLD, NEW, "ar-music SKILL.md — Cultural Radar Note")
    ok2 = patch_file(COMP_SKILL_PATH, COMP_OLD, COMP_NEW, "music-composition-skill — Social/Cultural Observation")
    ok3 = patch_file(COMP_SKILL_PATH, COMP_OLD2, COMP_NEW2, "music-composition-skill — T.I.-mode diagnostic")

    if ok1 and ok2 and ok3:
        print("\nAll patches applied. Restart any active Claude session to pick up changes.")
    else:
        print("\nSome patches skipped or failed — see messages above.")
