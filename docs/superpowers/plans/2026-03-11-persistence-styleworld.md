# Artist Name Persistence + Style World Memory Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist the artist name field across sessions, and track which of the 8 NB2 style worlds the LLM has used so it never repeats them across generation runs.

**Architecture:** All changes are in `index.html` only. Artist name persistence follows the same localStorage read/write pattern already used for wardrobe memory. Style world memory follows the exact same LLM self-report → localStorage store → prompt injection → system prompt rule pattern as wardrobe memory — just with a different field name and an auto-reset at 8 (the total number of style worlds). No backend changes.

**Tech Stack:** Plain HTML/JS — edit `index.html` directly. No build step.

---

## Chunk 1: Helper Functions

### Task 1: Add artist name persistence helpers + wire resetAll

**Files:**
- Modify: `index.html` (just after `// ── END WARDROBE MEMORY` comment, ~line 1676)
- Modify: `index.html` (`resetAll` function, line 2320)

**Context:** The wardrobe helpers live in a block between `// ── WARDROBE MEMORY` and `// ── END WARDROBE MEMORY` comments (lines 1612–1676). New helpers go immediately after line 1676. `resetAll` at line 2312 explicitly clears `#artistName` at line 2320 — that line must be removed.

- [ ] **Step 1: Locate the insertion point**

Search for this exact text in `index.html`:
```
// ── END WARDROBE MEMORY ──────────────────────────────────────────────────────
```

- [ ] **Step 2: Insert artist persistence helpers immediately after it**

Insert this block on the line directly after:

```javascript
// ── ARTIST PERSISTENCE ───────────────────────────────────────────────────────
function loadArtistFields(){
  const a=localStorage.getItem('apulu_artist');
  if(a)document.getElementById('artistName').value=a;
}
function saveArtistFields(artist){
  if(artist)localStorage.setItem('apulu_artist',artist);
}
// ── END ARTIST PERSISTENCE ───────────────────────────────────────────────────
```

- [ ] **Step 3: Remove artistName clear from resetAll**

Search for this exact text (inside `resetAll`):
```
  document.getElementById('artistName').value='';
  document.getElementById('trackName').value='';
```

Replace with:
```
  document.getElementById('trackName').value='';
```

(Remove the `artistName` line; keep `trackName` intact.)

- [ ] **Step 4: Verify**

1. `loadArtistFields` and `saveArtistFields` appear after `// ── END WARDROBE MEMORY`
2. `document.getElementById('artistName').value=''` no longer exists anywhere in `resetAll`
3. `document.getElementById('trackName').value=''` still exists in `resetAll`

- [ ] **Step 5: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add artist name persistence helpers, remove artistName clear from resetAll"
```

---

### Task 2: Add style world memory helpers

**Files:**
- Modify: `index.html` (just after artist persistence block, after `// ── END ARTIST PERSISTENCE`)

- [ ] **Step 1: Locate the insertion point**

Search for:
```
// ── END ARTIST PERSISTENCE ───────────────────────────────────────────────────
```

- [ ] **Step 2: Insert style world helpers immediately after it**

```javascript
// ── STYLE WORLD MEMORY ───────────────────────────────────────────────────────
function loadStyleWorlds(){
  try{
    const raw=localStorage.getItem('apulu_styleworlds');
    const parsed=raw?JSON.parse(raw):{};
    return{worlds:Array.isArray(parsed.worlds)?parsed.worlds:[]};
  }catch(e){return{worlds:[]};}
}

function styleWorldCount(){
  const sw=loadStyleWorlds();
  return Array.isArray(sw.worlds)?sw.worlds.length:0;
}

function updateStyleWorldLabel(){
  const el=document.getElementById('styleWorldLabel');
  if(!el)return;
  el.textContent=`Worlds: ${styleWorldCount()}/8 used`;
}

function clearStyleWorlds(){
  localStorage.removeItem('apulu_styleworlds');
  updateStyleWorldLabel();
}

function saveStyleWorlds(scenes){
  if(!Array.isArray(scenes))return;
  const sw=loadStyleWorlds();
  scenes.forEach(s=>{
    const val=((s&&s.style_world)||'').trim();
    if(!val||val.toLowerCase()==='none')return;
    if(!sw.worlds.some(x=>x.toLowerCase()===val.toLowerCase())){
      sw.worlds.push(val);
    }
  });
  if(sw.worlds.length>8)sw.worlds=sw.worlds.slice(-8);
  if(sw.worlds.length===8){
    localStorage.setItem('apulu_styleworlds',JSON.stringify(sw));
    sw.worlds=[];
  }
  localStorage.setItem('apulu_styleworlds',JSON.stringify(sw));
  updateStyleWorldLabel();
}

function buildStyleWorldPromptBlock(sw){
  if(!Array.isArray(sw.worlds)||!sw.worlds.length)return'';
  return`STYLE WORLD MEMORY — these style worlds have already been used in previous generations. Do NOT use any world on this list. Every scene in this generation must use a style world not on this list.\nWorlds used: ${sw.worlds.join(', ')}\n\n`;
}
// ── END STYLE WORLD MEMORY ───────────────────────────────────────────────────
```

- [ ] **Step 3: Verify**

1. All 6 style world functions are present (`loadStyleWorlds`, `styleWorldCount`, `updateStyleWorldLabel`, `clearStyleWorlds`, `saveStyleWorlds`, `buildStyleWorldPromptBlock`)
2. `saveStyleWorlds` saves to localStorage before clearing (two separate `localStorage.setItem` calls — one to record the full 8, then one after reset to `[]`)
3. `updateStyleWorldLabel()` is called once, at the very end of `saveStyleWorlds`

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add style world memory helper functions"
```

---

## Chunk 2: System Prompt Rule + JSON Schemas

### Task 3: Add style world memory rule to buildPromptSystem

**Files:**
- Modify: `index.html` (`buildPromptSystem` NB2 guidelines block)

**Context:** The wardrobe memory rule was inserted between the `- Include "4K ultra-HD"` line and the `- negative_prompt must include:` line. The style world rule goes immediately after the wardrobe memory rule.

- [ ] **Step 1: Locate the anchor**

Search for this exact text (the wardrobe rule + what follows):
```
- Wardrobe memory: if a WARDROBE MEMORY block appears in the user message, treat it as a hard constraint. No shirt, pant, jacket, or hat in any scene may match or closely resemble any item on the list — not the same garment type, not the same brand in the same colorway, not the same silhouette in the same color. Every generation must produce entirely fresh outfit choices across all scenes. Shoes are exempt from this constraint.
- negative_prompt must include:
```

- [ ] **Step 2: Insert style world rule between wardrobe rule and negative_prompt line**

Replace with:
```
- Wardrobe memory: if a WARDROBE MEMORY block appears in the user message, treat it as a hard constraint. No shirt, pant, jacket, or hat in any scene may match or closely resemble any item on the list — not the same garment type, not the same brand in the same colorway, not the same silhouette in the same color. Every generation must produce entirely fresh outfit choices across all scenes. Shoes are exempt from this constraint.
- Style world memory: if a STYLE WORLD MEMORY block appears in the user message, treat it as a hard constraint. No scene may use any style world listed — not the same world number, not the same brand universe, not the same aesthetic register. Every generation must use only worlds not on the list.
- negative_prompt must include:
```

- [ ] **Step 3: Verify**

1. `- Style world memory:` rule appears between the wardrobe rule and `- negative_prompt must include:`
2. The wardrobe memory rule is unchanged
3. Search confirms `Style world memory` appears exactly once in the file

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add style world memory system prompt rule to buildPromptSystem"
```

---

### Task 4: Add style_world field to all three JSON schemas

**Files:**
- Modify: `index.html` (3 locations — lyrics branch, description branch, generateGridStory schema)

**Context:** `wardrobe_used` was added to all 3 schemas in a previous feature. `style_world` goes immediately after `wardrobe_used` in each. The three locations are distinguished by:
- Lyrics branch: has `"archetype"` field above `wardrobe_used`
- Description branch: no `"archetype"` field; ends with `` }` `` + semicolon followed by `const content=`
- GridStory: ends with `` }` `` + semicolon followed by `const userPrompt=`

- [ ] **Step 1: Add to lyrics branch**

Search for this exact text (unique because of `"archetype"`):
```
      "wardrobe_used": {"shirt": "exact shirt description or 'none'", "pants": "exact pants description or 'none'", "jacket": "exact jacket description or 'none'", "hat": "exact hat description or 'none'"},
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`
:
```

Replace with:
```
      "wardrobe_used": {"shirt": "exact shirt description or 'none'", "pants": "exact pants description or 'none'", "jacket": "exact jacket description or 'none'", "hat": "exact hat description or 'none'"},
      "style_world": "WORLD N — FULL NAME (e.g. WORLD 3 — FRENCH LUXURY STREETWEAR), or 'none'",
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`
:
```

- [ ] **Step 2: Add to description branch**

Search for this exact text (unique: ends with `` }` `` + `;` followed shortly by `const content=`):
```
      "wardrobe_used": {"shirt": "exact shirt description or 'none'", "pants": "exact pants description or 'none'", "jacket": "exact jacket description or 'none'", "hat": "exact hat description or 'none'"},
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`;
```

Replace with:
```
      "wardrobe_used": {"shirt": "exact shirt description or 'none'", "pants": "exact pants description or 'none'", "jacket": "exact jacket description or 'none'", "hat": "exact hat description or 'none'"},
      "style_world": "WORLD N — FULL NAME (e.g. WORLD 3 — FRENCH LUXURY STREETWEAR), or 'none'",
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`;
```

Note: the description branch ending is `` }` `` + `;` — confirm the semicolon is still there after the edit.

- [ ] **Step 3: Add to generateGridStory schema**

Search for this exact text (unique: `` }` `` + `;` followed by `const userPrompt=`):
```
      "wardrobe_used": {"shirt": "exact shirt description or 'none'", "pants": "exact pants description or 'none'", "jacket": "exact jacket description or 'none'", "hat": "exact hat description or 'none'"},
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`;

  const userPrompt=`Artist: ${artist}
```

Replace with:
```
      "wardrobe_used": {"shirt": "exact shirt description or 'none'", "pants": "exact pants description or 'none'", "jacket": "exact jacket description or 'none'", "hat": "exact hat description or 'none'"},
      "style_world": "WORLD N — FULL NAME (e.g. WORLD 3 — FRENCH LUXURY STREETWEAR), or 'none'",
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`;

  const userPrompt=`Artist: ${artist}
```

- [ ] **Step 4: Verify**

Run:
```bash
grep -c "style_world" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 4 matches (1 in saveStyleWorlds reading `s.style_world`, plus 3 schema injections).

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat: add style_world field to all three JSON schemas"
```

---

## Chunk 3: Wiring — Generate Functions + Page Init

### Task 5: Wire artist save + style world injection into generateMV and generateGridStory

**Files:**
- Modify: `index.html` (`generateMV` and `generateGridStory` functions)

**Context:**
- `generateMV` starts at line ~1749 with `const artist=document.getElementById('artistName').value.trim()||'Artist';`
- `generateGridStory` starts at line ~1834 with the same pattern
- The wardrobe block injection is at `const wardrobeBlock=buildWardrobePromptBlock(loadWardrobe());` followed by `const content=[{type:'text',text:wardrobeBlock+userPrompt}];`
- After generation: `allScenes=parsed.scenes||[];` then `saveWardrobe(allScenes);`

**Edit 1 — artist save in generateMV:**

Search for this exact text (unique to generateMV — has `||'Artist'` and is followed by `const track=`):
```
  const artist=document.getElementById('artistName').value.trim()||'Artist';
  const track=document.getElementById('trackName').value.trim()||'Track';
```

Replace with:
```
  const artist=document.getElementById('artistName').value.trim()||'Artist';
  saveArtistFields(artist);
  const track=document.getElementById('trackName').value.trim()||'Track';
```

**Edit 2 — style world block injection in generateMV:**

Search for this exact text (in generateMV — has `outputMode!=='kling'` guard):
```
  const wardrobeBlock=buildWardrobePromptBlock(loadWardrobe());
  const content=[{type:'text',text:wardrobeBlock+userPrompt}];
  if(imgBase64&&outputMode!=='kling'){
```

Replace with:
```
  const wardrobeBlock=buildWardrobePromptBlock(loadWardrobe());
  const styleWorldBlock=buildStyleWorldPromptBlock(loadStyleWorlds());
  const content=[{type:'text',text:wardrobeBlock+styleWorldBlock+userPrompt}];
  if(imgBase64&&outputMode!=='kling'){
```

**Edit 3 — saveStyleWorlds after allScenes in generateMV:**

Search for this exact text (in generateMV — followed by `renderScenes(artist,track)`):
```
    allScenes=parsed.scenes||[];
    saveWardrobe(allScenes);
    renderScenes(artist,track);
```

Replace with:
```
    allScenes=parsed.scenes||[];
    saveWardrobe(allScenes);
    saveStyleWorlds(allScenes);
    renderScenes(artist,track);
```

**Edit 4 — artist save in generateGridStory:**

Search for this exact text (unique to generateGridStory — followed by `const inputText=document.getElementById('gridStoryInput')`):
```
  const artist=document.getElementById('artistName').value.trim()||'Artist';
  const inputText=document.getElementById('gridStoryInput').value.trim();
```

Replace with:
```
  const artist=document.getElementById('artistName').value.trim()||'Artist';
  saveArtistFields(artist);
  const inputText=document.getElementById('gridStoryInput').value.trim();
```

**Edit 5 — style world block injection in generateGridStory:**

Search for this exact text (in generateGridStory — has plain `if(imgBase64){` guard, no outputMode):
```
  const wardrobeBlock=buildWardrobePromptBlock(loadWardrobe());
  const content=[{type:'text',text:wardrobeBlock+userPrompt}];
  if(imgBase64){
```

Replace with:
```
  const wardrobeBlock=buildWardrobePromptBlock(loadWardrobe());
  const styleWorldBlock=buildStyleWorldPromptBlock(loadStyleWorlds());
  const content=[{type:'text',text:wardrobeBlock+styleWorldBlock+userPrompt}];
  if(imgBase64){
```

**Edit 6 — saveStyleWorlds after allScenes in generateGridStory:**

Search for this exact text (unique — followed by `renderScenes(artist,'9-Grid Story')`):
```
    allScenes=parsed.scenes||[];
    saveWardrobe(allScenes);
    renderScenes(artist,'9-Grid Story');
```

Replace with:
```
    allScenes=parsed.scenes||[];
    saveWardrobe(allScenes);
    saveStyleWorlds(allScenes);
    renderScenes(artist,'9-Grid Story');
```

- [ ] **Step 1: Apply all 6 edits above using the Edit tool**

- [ ] **Step 2: Verify**

```bash
grep -n "saveArtistFields\|styleWorldBlock\|saveStyleWorlds" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected:
- `saveArtistFields` appears in generateMV and generateGridStory (2 hits)
- `styleWorldBlock` appears 4 times (2 declarations + 2 uses in content array)
- `saveStyleWorlds` appears 3 times (definition + 2 call sites)

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: wire artist save and style world injection into generateMV and generateGridStory"
```

---

### Task 6: Wire artist save into generateFramePair

**Files:**
- Modify: `index.html` (`generateFramePair` function, ~line 1926)

**Context:** `generateFramePair` also reads `#artistName` (line 1927) but is a Kling-only path — it gets artist name persistence but NOT style world memory.

- [ ] **Step 1: Locate generateFramePair**

Search for this exact text:
```
async function generateFramePair(){
  const artist=document.getElementById('artistName').value.trim()||'Artist';
  const inputText=document.getElementById('framesInput').value.trim();
```

- [ ] **Step 2: Add saveArtistFields call**

Replace with:
```
async function generateFramePair(){
  const artist=document.getElementById('artistName').value.trim()||'Artist';
  saveArtistFields(artist);
  const inputText=document.getElementById('framesInput').value.trim();
```

- [ ] **Step 3: Verify**

```bash
grep -n "saveArtistFields" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 3 hits — generateMV, generateGridStory, generateFramePair.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: wire artist save into generateFramePair"
```

---

### Task 7: Add UI controls + page init

**Files:**
- Modify: `index.html` (controls bar HTML, ~line 1215; page init block, ~line 2344)

**Context:** Wardrobe controls are at lines 1214–1215, immediately before the History toggle at line 1217. Style world controls go after wardrobeCountLabel. The init block is at line 2344 and currently ends with `updateWardrobeCountLabel();`.

- [ ] **Step 1: Add style world UI after wardrobe controls**

Search for this exact text:
```
      <span id="wardrobeCountLabel" style="font-size:11px;opacity:.65;white-space:nowrap;align-self:center;">Wardrobe: empty</span>

      <!-- History toggle -->
```

Replace with:
```
      <span id="wardrobeCountLabel" style="font-size:11px;opacity:.65;white-space:nowrap;align-self:center;">Wardrobe: empty</span>

      <!-- Style world controls -->
      <button class="ctrl-btn" id="styleWorldResetBtn" onclick="clearStyleWorlds()">Reset Worlds</button>
      <span id="styleWorldLabel" style="font-size:11px;opacity:.65;white-space:nowrap;align-self:center;">Worlds: 0/8 used</span>

      <!-- History toggle -->
```

- [ ] **Step 2: Add init calls**

Search for this exact text:
```
// Initialize
updatePanels();
updateInputArea();
updateGenBtn();
updateWardrobeCountLabel();
```

Replace with:
```
// Initialize
updatePanels();
updateInputArea();
updateGenBtn();
updateWardrobeCountLabel();
updateStyleWorldLabel();
loadArtistFields();
```

- [ ] **Step 3: Verify**

1. `styleWorldResetBtn` and `styleWorldLabel` appear between `wardrobeCountLabel` and `histToggleBtn` in the HTML
2. `updateStyleWorldLabel()` and `loadArtistFields()` appear in the `// Initialize` block after `updateWardrobeCountLabel()`
3. No other init calls were disturbed

- [ ] **Step 4: Final smoke test**

Open the app in a browser. Verify:
- "Worlds: 0/8 used" and "Reset Worlds" button visible in controls bar
- Type an artist name, generate — artist name survives a page reload
- Click "Start Fresh" — artist name field still shows the saved name; track name is cleared
- Generate several times — "Worlds: X/8 used" count increments
- When count reaches 8, it resets to 0 automatically on the next generation
- Click "Reset Worlds" — label shows "Worlds: 0/8 used" immediately

- [ ] **Step 5: Commit and push**

```bash
git add index.html
git commit -m "feat: add style world UI controls and page init calls"
git push origin main
```
