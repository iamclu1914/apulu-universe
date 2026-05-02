# Projects Folder Instructions

This folder may contain project workspaces, links, junctions, or symlinked external projects.

Do not replace symlinks, junctions, or linked project folders with real directories unless explicitly requested.

Before editing anything under `projects/`, verify whether the target is:
- a real tracked folder
- a symlink
- a junction
- an external workspace reference

If a project path is symlinked or external, do not create files inside it as part of this repo unless explicitly approved.

## Apulu Prompt Generator

For Apulu Prompt Generator work, treat it as an AI-powered creative-direction tool for music video production.

The app is not a generic AI prompt tool.
It is a focused production instrument for Vawn and the Apulu creative circle.

Preferred tech constraints:
- Plain HTML
- CSS
- Vanilla JavaScript
- Express Node server if present

Do not introduce:
- React
- Next.js
- Build tools
- New UI frameworks
- Random component libraries

unless explicitly asked.

Preserve the existing design direction:
- dark editorial cinematic interface
- warm espresso/chocolate surfaces
- gold primary accent
- warm off-white text
- Instrument Serif for display/logo
- Raleway for UI
- JetBrains Mono for prompt/code output
- no pure black/pure white
- no generic cyan/purple AI SaaS look

When editing UI, verify:
- empty state
- loading/progress state
- generated results
- Studio view
- mobile layout
- copy buttons
