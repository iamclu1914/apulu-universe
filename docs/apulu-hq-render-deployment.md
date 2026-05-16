# Apulu HQ Render Deployment

Apulu HQ is the main website and business dashboard. Render serves the FastAPI
app, the `/ui/` dashboard, and the bundled Prompt Generator UI at
`/ui/prompt-generator/`.

## Render

Use the repository root blueprint:

```text
render.yaml
```

The web service deploys from:

```text
projects/apulu-hq
```

Runtime behavior:

- `/` redirects to `/ui/`
- `/ui/` serves the Apulu HQ Command Center
- `/ui/prompt-generator/` serves the Prompt Generator UI
- `/api/prompt-generator/*` proxies to `https://apulu-backend.onrender.com/api/*`

Required environment:

```text
APULU_PROMPT_GENERATOR_BACKEND_URL=https://apulu-backend.onrender.com
APULU_HQ_DATA_DIR=/var/data/apulu-hq
```

The blueprint also mounts a persistent Render disk at:

```text
/var/data/apulu-hq
```

## Vercel

Vercel is no longer required for the combined app.

During migration, keep the old Prompt Generator Vercel app live or redirect it
to the new Render URL:

```text
https://<apulu-hq-render-domain>/ui/prompt-generator/
```

After the Render app is verified, the Vercel project can be disabled.
