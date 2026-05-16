# Wardrobe Memory Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Track shirt/pant/jacket/hat pieces in localStorage across generation runs so the LLM never repeats them, with a Reset Wardrobe button that shows a live piece count.

**Architecture:** Six targeted changes to `index.html` only — helper functions, system prompt rule, JSON schema additions (3 places), prompt injection + saveWardrobe calls (2 functions), and UI button + page-init call. No backend changes, no new files.

**Tech Stack:** Plain HTML/JS — edit `index.html` directly. No build step.

---

## Chunk 1: Helper Functions + System Prompt Rule

### Task 1: Add wardrobe helper functions

**Files:**
- Modify: `index.html` (just before `buildPromptSystem` function, ~line 1608)

- [ ] **Step 1: Locate the insertion point**

Search for this exact text in `index.html`:
```
function buildPromptSystem(anchorBlock, onlyOutput){
```

- [ ] **Step 2: Insert helper functions immediately before it**

Insert the following block on the line directly before `function buildPromptSystem`:

```javascript
// ── WARDROBE MEMORY ─────────────────────────────────────────────────────────
function loadWardrobe(){
  try{
    const raw=localStorage.getItem('apulu_wardrobe');
    const parsed=raw?JSON.parse(raw):{};
    return{
      shirts:Array.isArray(parsed.shirts)?parsed.shirts:[],
      pants:Array.isArray(parsed.pants)?parsed.pants:[],
      jackets:Array.isArray(parsed.jackets)?parsed.jackets:[],
      hats:Array.isArray(parsed.hats)?parsed.hats:[]
    };
  }catch(e){return{shirts:[],pants:[],jackets:[],hats:[]};}
}

function wardrobeCount(){
  const w=loadWardrobe();
  return(Array.isArray(w.shirts)?w.shirts.length:0)
       +(Array.isArray(w.pants)?w.pants.length:0)
       +(Array.isArray(w.jackets)?w.jackets.length:0)
       +(Array.isArray(w.hats)?w.hats.length:0);
}

function updateWardrobeCountLabel(){
  const el=document.getElementById('wardrobeCountLabel');
  if(!el)return;
  const n=wardrobeCount();
  el.textContent=n===0?'Wardrobe: empty':`Wardrobe: ${n} pieces`;
}

function clearWardrobe(){
  localStorage.removeItem('apulu_wardrobe');
  updateWardrobeCountLabel();
}

function saveWardrobe(scenes){
  if(!Array.isArray(scenes))return;
  const w=loadWardrobe();
  const MAP={shirt:'shirts',pants:'pants',jacket:'jackets',hat:'hats'};
  scenes.forEach(s=>{
    const u=s&&s.wardrobe_used;
    if(!u||typeof u!=='object')return;
    Object.entries(MAP).forEach(([key,arr])=>{
      const val=(u[key]||'').trim();
      if(!val||val.toLowerCase()==='none')return;
      if(!w[arr].some(x=>x.toLowerCase()===val.toLowerCase())){
        w[arr].push(val);
      }
    });
  });
  // cap at 200 per category
  Object.keys(MAP).forEach(k=>{const a=MAP[k];if(w[a].length>200)w[a]=w[a].slice(-200);});
  localStorage.setItem('apulu_wardrobe',JSON.stringify(w));
  updateWardrobeCountLabel();
}

function buildWardrobePromptBlock(w){
  const lines=[];
  if(w.shirts.length)lines.push(`Shirts used: ${w.shirts.join(', ')}`);
  if(w.pants.length)lines.push(`Pants used: ${w.pants.join(', ')}`);
  if(w.jackets.length)lines.push(`Jackets used: ${w.jackets.join(', ')}`);
  if(w.hats.length)lines.push(`Hats used: ${w.hats.join(', ')}`);
  if(!lines.length)return'';
  return`WARDROBE MEMORY — these garment pieces have already been used in previous generations. Do NOT repeat or closely resemble any item on this list. Every scene in this generation must use entirely new garment choices not on this list.\n${lines.join('\n')}\n\n`;
}
// ── END WARDROBE MEMORY ──────────────────────────────────────────────────────

```

- [ ] **Step 3: Verify the edit**

Confirm:
1. The six functions (`loadWardrobe`, `wardrobeCount`, `updateWardrobeCountLabel`, `clearWardrobe`, `saveWardrobe`, `buildWardrobePromptBlock`) are present and each is `function` keyword style
2. `function buildPromptSystem` immediately follows the closing comment `// ── END WARDROBE MEMORY`
3. No existing code was disturbed

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add wardrobe memory helper functions"
```

---

### Task 2: Add wardrobe memory rule to buildPromptSystem

**Files:**
- Modify: `index.html` (`buildPromptSystem` NB2 guidelines block, ~line 1662)

- [ ] **Step 1: Locate the anchor**

Search for this exact two-line sequence (using both lines ensures you match the `buildPromptSystem` occurrence, not the one inside `generateGridStory`):
```
- Include "4K ultra-HD" naturally within the scene description
- negative_prompt must include:
```

- [ ] **Step 2: Insert the wardrobe rule between those two lines**

Replace with:
```
- Include "4K ultra-HD" naturally within the scene description
- Wardrobe memory: if a WARDROBE MEMORY block appears in the user message, treat it as a hard constraint. No shirt, pant, jacket, or hat in any scene may match or closely resemble any item on the list — not the same garment type, not the same brand in the same colorway, not the same silhouette in the same color. Every generation must produce entirely fresh outfit choices across all scenes. Shoes are exempt from this constraint.
- negative_prompt must include:
```

(both existing lines are preserved unchanged; the new rule is inserted between them)

- [ ] **Step 3: Verify the edit**

Confirm:
1. `- Include "4K ultra-HD"` line is unchanged
2. The new `- Wardrobe memory:` rule appears immediately after it
3. `- negative_prompt must include:` follows immediately after the new rule
4. The `- Style anchor and photographer reference:` line (before `- Include "4K ultra-HD"`) is unchanged

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add wardrobe memory system prompt rule to buildPromptSystem"
```

---

## Chunk 2: JSON Schema + Prompt Injection + saveWardrobe

### Task 3: Add wardrobe_used to lyrics-mode JSON schema

**Files:**
- Modify: `index.html` (`generateMV` lyrics branch user prompt, ~line 1707)

- [ ] **Step 1: Locate the anchor in the lyrics branch**

Search for this exact text:
```
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`
:
```

The lyrics branch ends with that backtick followed by a newline and a colon (the ternary separator before the description branch). Confirm by checking the line before it — it should be `"negative_prompt": "smiling..."` and the line immediately after the closing `\`` should be `:` starting the description branch.

- [ ] **Step 2: Add wardrobe_used field before negative_prompt**

In the lyrics branch JSON schema, use this uniquely-lyrics anchor (the `"archetype"` field only exists in the lyrics branch, not the description branch):
```
      "archetype": "EMOTIONAL_ARC | TRANSFORMATION | etc",
      "director_note": "Brief director note",
      ${outputMode!=='kling'?'"image_prompt": "Full NB2 prompt...",':""}
      ${outputMode!=='nb2'?'"video_prompt": "Full Kling prompt with timestamps...",':""}
      "negative_prompt": "smiling, laughing, cartoonish..."
```

Replace with:
```
      "archetype": "EMOTIONAL_ARC | TRANSFORMATION | etc",
      "director_note": "Brief director note",
      ${outputMode!=='kling'?'"image_prompt": "Full NB2 prompt...",':""}
      ${outputMode!=='nb2'?'"video_prompt": "Full Kling prompt with timestamps...",':""}
      "wardrobe_used": {"shirt": "exact shirt description or 'none'", "pants": "exact pants description or 'none'", "jacket": "exact jacket description or 'none'", "hat": "exact hat description or 'none'"},
      "negative_prompt": "smiling, laughing, cartoonish..."
```

- [ ] **Step 3: Verify the edit**

Confirm:
1. `"wardrobe_used"` field appears between the video_prompt conditional and `"negative_prompt"` in the lyrics branch
2. The description branch (the else arm of the ternary, starting after the `:` separator) is unchanged

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add wardrobe_used field to lyrics-mode JSON schema"
```

---

### Task 4: Add wardrobe_used to description-mode JSON schema

**Files:**
- Modify: `index.html` (`generateMV` description branch user prompt, ~line 1727)

- [ ] **Step 1: Locate the anchor in the description branch**

The description branch user prompt ends with:
```
      ${outputMode!=='nb2'?'"video_prompt": "Full Kling prompt with timestamps...",':""}
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`;
```

Note: the description branch ends with `` }` ``  followed by a semicolon (`;`), unlike the lyrics branch which ends with `` }` `` followed by a colon.

- [ ] **Step 2: Add wardrobe_used field**

In the description branch JSON schema, find:
```
      ${outputMode!=='nb2'?'"video_prompt": "Full Kling prompt with timestamps...",':""}
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`;
```

Replace with:
```
      ${outputMode!=='nb2'?'"video_prompt": "Full Kling prompt with timestamps...",':""}
      "wardrobe_used": {"shirt": "exact shirt description or 'none'", "pants": "exact pants description or 'none'", "jacket": "exact jacket description or 'none'", "hat": "exact hat description or 'none'"},
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`;
```

- [ ] **Step 3: Verify the edit**

Confirm:
1. `"wardrobe_used"` appears in the description branch schema between video_prompt and negative_prompt
2. The `;` after the closing backtick is still there (unchanged)
3. The `const content=[{type:'text',text:userPrompt}];` line below is unchanged

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add wardrobe_used field to description-mode JSON schema"
```

---

### Task 5: Add wardrobe_used to generateGridStory JSON schema

**Files:**
- Modify: `index.html` (`generateGridStory` inline system prompt JSON schema, ~line 1809)

- [ ] **Step 1: Locate the anchor**

Search for this exact text (it is inside the gridStory inline system prompt):
```
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`;

  const userPrompt=`Artist: ${artist}
```

The `` }` `` followed by a semicolon and then `const userPrompt` tells you this is the right location.

- [ ] **Step 2: Add wardrobe_used field**

Replace the schema ending with:
```
      "wardrobe_used": {"shirt": "exact shirt description or 'none'", "pants": "exact pants description or 'none'", "jacket": "exact jacket description or 'none'", "hat": "exact hat description or 'none'"},
      "negative_prompt": "smiling, laughing, cartoonish..."
    }
  ]
}`;

  const userPrompt=`Artist: ${artist}
```

- [ ] **Step 3: Verify the edit**

Confirm:
1. `"wardrobe_used"` appears in the gridStory schema
2. The `const userPrompt` line that follows is unchanged
3. The inline system prompt's other rules (`- negative_prompt: smiling, laughing...` on ~line 1800) are unchanged — the schema at the end of the system prompt is the one being modified, not the rules block

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add wardrobe_used field to generateGridStory JSON schema"
```

---

### Task 6: Inject wardrobe block + call saveWardrobe in generateMV

**Files:**
- Modify: `index.html` (`generateMV` function, ~lines 1732 and 1749)

- [ ] **Step 1: Locate the content array construction in generateMV**

Search for this exact text:
```
  const content=[{type:'text',text:userPrompt}];
  if(imgBase64&&outputMode!=='kling'){
    content.unshift({type:'image',source:{type:'base64',media_type:'image/jpeg',data:imgBase64}});
  }
```

This appears in `generateMV` (not `generateGridStory` — the gridStory version uses `imgBase64` without the `outputMode` check).

- [ ] **Step 2: Replace with wardrobe-injected version**

Replace with:
```
  const wardrobeBlock=buildWardrobePromptBlock(loadWardrobe());
  const content=[{type:'text',text:wardrobeBlock+userPrompt}];
  if(imgBase64&&outputMode!=='kling'){
    content.unshift({type:'image',source:{type:'base64',media_type:'image/jpeg',data:imgBase64}});
  }
```

- [ ] **Step 3: Add saveWardrobe call after allScenes is assigned**

Search for this exact text (inside the try block of generateMV):
```
    allScenes=parsed.scenes||[];
    renderScenes(artist,track);
```

Replace with:
```
    allScenes=parsed.scenes||[];
    saveWardrobe(allScenes);
    renderScenes(artist,track);
```

- [ ] **Step 4: Verify the edit**

Confirm:
1. `buildWardrobePromptBlock(loadWardrobe())` is called in `generateMV` before `content` is built
2. `wardrobeBlock+userPrompt` is the text value in the content array
3. `saveWardrobe(allScenes)` appears on the line immediately after `allScenes=parsed.scenes||[];` in `generateMV`
4. `renderScenes(artist,track)` still follows on the next line

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat: inject wardrobe block into generateMV prompt and save wardrobe after parse"
```

---

### Task 7: Inject wardrobe block + call saveWardrobe in generateGridStory

**Files:**
- Modify: `index.html` (`generateGridStory` function, ~lines 1822 and 1839)

- [ ] **Step 1: Locate the content array construction in generateGridStory**

Search for this exact text (appears in generateGridStory):
```
  const content=[{type:'text',text:userPrompt}];
  if(imgBase64){
    content.unshift({type:'image',source:{type:'base64',media_type:'image/jpeg',data:imgBase64}});
  }
```

Note: this version checks only `imgBase64` with no `outputMode` guard — that distinguishes it from the `generateMV` version.

- [ ] **Step 2: Replace with wardrobe-injected version**

Replace with:
```
  const wardrobeBlock=buildWardrobePromptBlock(loadWardrobe());
  const content=[{type:'text',text:wardrobeBlock+userPrompt}];
  if(imgBase64){
    content.unshift({type:'image',source:{type:'base64',media_type:'image/jpeg',data:imgBase64}});
  }
```

- [ ] **Step 3: Add saveWardrobe call after allScenes is assigned**

Search for this exact text (inside the try block of generateGridStory):
```
    allScenes=parsed.scenes||[];
    renderScenes(artist,'9-Grid Story');
```

Replace with:
```
    allScenes=parsed.scenes||[];
    saveWardrobe(allScenes);
    renderScenes(artist,'9-Grid Story');
```

- [ ] **Step 4: Verify the edit**

Confirm:
1. `buildWardrobePromptBlock(loadWardrobe())` is called in `generateGridStory`
2. `saveWardrobe(allScenes)` appears immediately after `allScenes=parsed.scenes||[];` in `generateGridStory`
3. `renderScenes(artist,'9-Grid Story')` still follows on the next line

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat: inject wardrobe block into generateGridStory prompt and save wardrobe after parse"
```

---

## Chunk 3: UI + Page Init

### Task 8: Add Reset Wardrobe button and count label to controls bar

**Files:**
- Modify: `index.html` (controls bar HTML, ~line 1214)

- [ ] **Step 1: Locate the History toggle button**

Search for this exact text:
```
      <!-- History toggle -->
      <button class="hist-toggle" id="histToggleBtn" onclick="toggleHistory()">
```

- [ ] **Step 2: Insert wardrobe controls immediately before the History toggle**

Replace the entire history toggle block with the wardrobe controls prepended:

Find:
```
      <!-- History toggle -->
      <button class="hist-toggle" id="histToggleBtn" onclick="toggleHistory()">
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none" style="opacity:.7">
          <circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.4"/>
          <path d="M6 3.5V6.5L8 8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        </svg>
        History
      </button>
```

Replace with:
```
      <!-- Wardrobe controls -->
      <button class="ctrl-btn" id="wardrobeResetBtn" onclick="clearWardrobe()">Reset Wardrobe</button>
      <span id="wardrobeCountLabel" style="font-size:11px;opacity:.65;white-space:nowrap;align-self:center;">Wardrobe: empty</span>

      <!-- History toggle -->
      <button class="hist-toggle" id="histToggleBtn" onclick="toggleHistory()">
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none" style="opacity:.7">
          <circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.4"/>
          <path d="M6 3.5V6.5L8 8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        </svg>
        History
      </button>
```

- [ ] **Step 3: Verify the edit**

Confirm:
1. `wardrobeResetBtn` button and `wardrobeCountLabel` span appear in the HTML before `histToggleBtn`
2. The History button and its SVG are unchanged
3. Both elements have IDs that match what `updateWardrobeCountLabel()` and `clearWardrobe()` reference

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add Reset Wardrobe button and live count label to controls bar"
```

---

### Task 9: Call updateWardrobeCountLabel on page init

**Files:**
- Modify: `index.html` (page init block at end of script, ~line 2267)

- [ ] **Step 1: Locate the page init block**

Search for this exact text:
```
// Initialize
updatePanels();
updateInputArea();
updateGenBtn();
```

- [ ] **Step 2: Add updateWardrobeCountLabel call**

Replace with:
```
// Initialize
updatePanels();
updateInputArea();
updateGenBtn();
updateWardrobeCountLabel();
```

- [ ] **Step 3: Verify the edit**

Confirm:
1. `updateWardrobeCountLabel()` is called after `updateGenBtn()`
2. It is inside the `// Initialize` block (not inside any function)
3. No other lines were changed

- [ ] **Step 4: Final smoke test**

Open the app in a browser. Verify:
- "Wardrobe: empty" label appears in the controls bar next to "Reset Wardrobe" button
- Generate a scene (any mode). After generation completes, the count should update to reflect pieces stored (e.g., "Wardrobe: 6 pieces")
- Generate again — verify the WARDROBE MEMORY block appears in the network request (check browser devtools → Network → the /api/messages request body → look at the `messages[0].content[0].text` field for the WARDROBE MEMORY block)
- Click "Reset Wardrobe" — label should immediately show "Wardrobe: empty"
- Reload the page — label should show the correct count (or "empty" if reset) from localStorage

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat: call updateWardrobeCountLabel on page init"
```

- [ ] **Step 6: Push**

```bash
git push origin main
```
