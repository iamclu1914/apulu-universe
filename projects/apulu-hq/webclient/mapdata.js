/**
 * Apulu HQ — top-down floor plan data.
 *
 * Compact 20×14 tile grid (36 px tiles → 720×504 world). Rooms tile
 * edge-to-edge with NO gaps — the building reads as one contiguous floor
 * with interior partition walls between departments.
 *
 * Every agent's raw `desk_x` / `desk_y` from importer.py lands directly on
 * a tile inside its home room (no scaling, verified below).
 *
 *   marketing: Oaklyn(10,4) S&K(12,4) Dex(14,4) Nova(16,4) Echo(18,4)
 *   cos:       Nelly(4,2)  Sable(6,2)
 *   board:     Clu(2,2)
 *   ops:       Rex(4,8)  Aspyn(10,8) Cipher(12,8) Vibe(14,8)
 *   research:  Rhythm(4,12)
 *   production: Camdyn(12,12) Cole(14,12)
 *   post-prod: Onyx(16,12)
 */

export const TILE_SIZE = 36;
export const GRID_W = 20;
export const GRID_H = 14;
export const WORLD_W = TILE_SIZE * GRID_W;   // 720
export const WORLD_H = TILE_SIZE * GRID_H;   // 504

// Dark-editorial palette (matches webclient/index.html CSS vars).
export const PALETTE = {
  hall:       0x140d09,
  wall:       0x0a0705,
  accent:     0xc8a35b,
  accentDim:  0x8a7140,
  text:       0xf4ecdf,
  muted:      0x9a8a78,
  ok:         0x8bc28b,
  error:      0xd96565,
  warn:       0xe2b463,
};

/**
 * Rooms tile edge-to-edge across the floor. Coords are inclusive tile
 * rectangles. Each room's `tone` is its parquet base color.
 *
 *   y= 1..4   : CEO | CoS | Marketing      (top strip)
 *   y= 5..10  : Operations Floor           (full width)
 *   y=11..13  : Research | Production | Post-prod  (bottom strip)
 */
export const ROOMS = [
  { id: "ceo",        label: "CEO Office",        x1: 1,  y1: 1,  x2: 3,  y2: 4,  tone: 0x3a2a1d },
  { id: "cos",        label: "CoS Corner",        x1: 4,  y1: 1,  x2: 8,  y2: 4,  tone: 0x322419 },
  { id: "marketing",  label: "Marketing Bullpen", x1: 9,  y1: 1,  x2: 18, y2: 4,  tone: 0x2c2018 },
  { id: "ops",        label: "Operations Floor",  x1: 1,  y1: 5,  x2: 18, y2: 10, tone: 0x28201a },
  { id: "research",   label: "Research Lab",      x1: 1,  y1: 11, x2: 7,  y2: 13, tone: 0x2a1f18 },
  { id: "production", label: "Production Booth",  x1: 8,  y1: 11, x2: 14, y2: 13, tone: 0x2e2018 },
  { id: "postprod",   label: "Post-prod",         x1: 15, y1: 11, x2: 18, y2: 13, tone: 0x33221d },
];

/** Department → home room (used to constrain idle wandering). */
export const DEPT_TO_ROOM = {
  board:       "ceo",
  cos:         "cos",
  marketing:   "marketing",
  operations:  "ops",
  research:    "research",
  production:  "production",
  "post-prod": "postprod",
};

/** Per-department sprite tint — body color so agents read at a glance. */
export const DEPT_COLORS = {
  board:       0xc8a35b,  // gold
  cos:         0xe9d4a3,  // cream
  marketing:   0xe8a76c,  // peach
  operations:  0x7fb0a6,  // teal
  research:    0xa3c88b,  // sage
  production:  0xd9728e,  // rose
  "post-prod": 0xb086c8,  // violet
};

/** Per-agent role glyph (always visible above the sprite). */
export const AGENT_GLYPHS = {
  "Clu":          "♔",
  "Nelly":        "✦",
  "Sable":        "🎤",
  "Oaklyn":       "📈",
  "Sage & Khari": "🎨",
  "Dex":          "💬",
  "Nova":         "📊",
  "Echo":         "📣",
  "Aspyn":        "🧭",
  "Cipher":       "🔮",
  "Vibe":         "✨",
  "Rex":          "⚙",
  "Rhythm":       "🔍",
  "Camdyn":       "🎬",
  "Cole":         "🎚",
  "Onyx":         "💎",
};

/** Tile coord → world pixel center. */
export function tileCenter(tileX, tileY) {
  return {
    px: tileX * TILE_SIZE + TILE_SIZE / 2,
    py: tileY * TILE_SIZE + TILE_SIZE / 2,
  };
}

/** Map a raw desk_x, desk_y (from the DB) to world coords. */
export function deskToWorld(deskX, deskY) {
  const tileX = Math.max(0, Math.min(GRID_W - 1, deskX));
  const tileY = Math.max(0, Math.min(GRID_H - 1, deskY));
  const { px, py } = tileCenter(tileX, tileY);
  return { tileX, tileY, px, py };
}

/** Pick a random idle wander target inside the agent's home room. */
export function randomTileInRoom(roomId, rng = Math.random) {
  const room = ROOMS.find(r => r.id === roomId) || ROOMS[0];
  const x = room.x1 + Math.floor(rng() * (room.x2 - room.x1 + 1));
  const y = room.y1 + Math.floor(rng() * (room.y2 - room.y1 + 1));
  const { px, py } = tileCenter(x, y);
  return { tileX: x, tileY: y, px, py };
}
