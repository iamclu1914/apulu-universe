# GitHub + Render + Vercel Deployment Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy Apulu Prompt Generator with backend on Render, frontend on Vercel, connected via GitHub, using Vercel proxy rewrites so the frontend never exposes the backend URL.

**Architecture:** GitHub repo is the single source of truth — Render auto-deploys `server.js` (Express/Gemini proxy) from it, and Vercel auto-deploys `index.html` (static) from it. Vercel rewrites `/api/*` to the Render backend URL so the browser always calls same-origin and no CORS config is needed.

**Tech Stack:** Node 22, Express 4, GitHub CLI (`gh`), Vercel CLI (optional), Render (dashboard), Vercel (dashboard)

---

## Chunk 1: Repo scaffolding — files that need to exist before GitHub

### Task 1: Add .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Create `.gitignore`**

```
node_modules/
.env
.env.local
.DS_Store
```

- [ ] **Step 2: Verify node_modules and .env are excluded**

Run: `git check-ignore -v node_modules .env`
Expected: both lines printed (they are ignored)

> Skip step 2 until after git init in Task 3 — come back to verify.

---

### Task 2: Create `vercel.json`

**Files:**
- Create: `vercel.json`

This tells Vercel two things: (1) the project is a static site rooted at `.`, and (2) any request to `/api/*` should be transparently proxied to the Render backend.

- [ ] **Step 1: Create `vercel.json`**

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://RENDER_APP_NAME.onrender.com/api/:path*"
    }
  ]
}
```

> `RENDER_APP_NAME` is a placeholder — it gets replaced with the real Render service name in Task 6 after the Render service is created.

- [ ] **Step 2: Confirm `index.html` still uses `/api/messages` (no change needed)**

Search for the fetch call:
```bash
grep -n "fetch.*api/messages\|/api/messages" index.html
```
Expected: at least one match confirming the relative URL is already correct.

---

### Task 3: Create `render.yaml`

**Files:**
- Create: `render.yaml`

Render uses this file to auto-configure the service on first connect.

- [ ] **Step 1: Create `render.yaml`**

```yaml
services:
  - type: web
    name: apulu-backend
    runtime: node
    buildCommand: npm install
    startCommand: node server.js
    envVars:
      - key: GEMINI_API_KEY
        sync: false
```

> `sync: false` means the value is NOT stored in the YAML (stays secret) — you set it manually in the Render dashboard.

---

## Chunk 2: Git repo + GitHub

### Task 4: Authenticate GitHub CLI

- [ ] **Step 1: Log in to GitHub via browser**

Run:
```bash
gh auth login
```
Choose: GitHub.com → HTTPS → Login with a web browser → follow prompts.

- [ ] **Step 2: Verify auth**

Run:
```bash
gh auth status
```
Expected: `Logged in to github.com as <your-username>`

---

### Task 5: Initialize git and make first commit

**Files:** all project files (excluding node_modules, .env)

- [ ] **Step 1: Initialize repo**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git init
git branch -M main
```

- [ ] **Step 2: Stage all files**

```bash
git add index.html server.js package.json vercel.json render.yaml .gitignore workflow.md
```

- [ ] **Step 3: Verify staging (no node_modules, no .env)**

```bash
git status
```
Expected: only the 7 files above listed under "Changes to be committed". `node_modules/` must NOT appear.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: initial commit — Apulu prompt generator"
```

---

### Task 6: Create GitHub repo and push

- [ ] **Step 1: Create private GitHub repo and push**

```bash
gh repo create apulu-prompt-generator --private --source=. --remote=origin --push
```

Expected output: repo URL printed, e.g. `https://github.com/<username>/apulu-prompt-generator`

- [ ] **Step 2: Verify push**

```bash
gh repo view --web
```
Expected: browser opens the repo with all files visible.

---

## Chunk 3: Render setup (backend)

### Task 7: Connect GitHub repo to Render

> This is done in the Render dashboard — no CLI steps.

- [ ] **Step 1: Go to [https://render.com](https://render.com) → New → Web Service**

- [ ] **Step 2: Connect your GitHub account if not already connected**

- [ ] **Step 3: Select the `apulu-prompt-generator` repo**

- [ ] **Step 4: Render will auto-detect `render.yaml` — confirm these settings:**
  - Name: `apulu-backend`
  - Runtime: Node
  - Build Command: `npm install`
  - Start Command: `node server.js`
  - Instance Type: Free

- [ ] **Step 5: Set the `GEMINI_API_KEY` environment variable**
  - In the Render dashboard, go to Environment → Add Environment Variable
  - Key: `GEMINI_API_KEY`
  - Value: your actual Gemini API key

- [ ] **Step 6: Click "Create Web Service" — wait for first deploy to succeed**

- [ ] **Step 7: Copy the Render service URL**
  - Format: `https://apulu-backend.onrender.com` (or similar)
  - Save this — needed for next chunk.

---

## Chunk 4: Vercel setup + wire up the proxy

### Task 8: Update `vercel.json` with real Render URL

- [ ] **Step 1: Replace the placeholder in `vercel.json`**

Edit `vercel.json` — replace `RENDER_APP_NAME` with the actual name from Task 7 Step 7:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://apulu-backend.onrender.com/api/:path*"
    }
  ]
}
```

- [ ] **Step 2: Commit and push**

```bash
git add vercel.json
git commit -m "chore: set Render backend URL in Vercel proxy config"
git push
```

---

### Task 9: Connect GitHub repo to Vercel

> Done in the Vercel dashboard.

- [ ] **Step 1: Go to [https://vercel.com](https://vercel.com) → Add New → Project**

- [ ] **Step 2: Import the `apulu-prompt-generator` GitHub repo**

- [ ] **Step 3: Configure project settings:**
  - Framework Preset: **Other** (it's a plain static HTML file)
  - Root Directory: `.` (leave as default)
  - Build Command: *(leave empty)*
  - Output Directory: `.` (or leave empty — Vercel auto-detects `index.html`)

- [ ] **Step 4: Click "Deploy" — wait for deploy to finish**

- [ ] **Step 5: Copy the Vercel deployment URL**
  - Format: `https://apulu-prompt-generator.vercel.app`

---

## Chunk 5: Verification

### Task 10: End-to-end smoke test

- [ ] **Step 1: Open the Vercel URL in the browser**

Expected: Apulu Generation UI loads correctly with all fonts and styles.

- [ ] **Step 2: Enter artist name, track name, and lyrics — hit Generate**

Expected: loading spinner appears → scene cards render with image/video prompts.

- [ ] **Step 3: Open browser DevTools → Network tab — inspect the `/api/messages` request**

Expected:
- Request URL: `https://apulu-prompt-generator.vercel.app/api/messages`
- Response: 200 with JSON `{ content: [{ type: "text", text: "..." }] }`
- No CORS errors in the console

- [ ] **Step 4: Push a test change and verify auto-deploy**

```bash
# Add a harmless comment to server.js
echo "" >> server.js
git add server.js
git commit -m "chore: trigger auto-deploy test"
git push
```

Expected: Render re-deploys automatically within ~2 minutes.

---

## Post-deployment notes

- **Render free tier** spins down after 15 min of inactivity — first request after sleep takes ~30s. Upgrade to a paid plan to avoid cold starts.
- **Auto-deploys**: every `git push` to `main` triggers both Render and Vercel redeploys.
- **Secrets**: `GEMINI_API_KEY` lives only in Render's environment — never in the repo.
- **Future env vars on Vercel**: if the frontend ever needs build-time variables, add them in Vercel dashboard → Settings → Environment Variables.
