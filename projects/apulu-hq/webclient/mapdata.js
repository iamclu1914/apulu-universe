/**
 * Apulu HQ — isometric floor plan data.
 *
 * Tile coordinate space is a 22-col × 16-row grid that maps 1:1 to the raw
 * `desk_x` / `desk_y` values seeded by importer.py. There is intentionally
 * NO scaling here — every agent's seeded desk coordinate lands directly on
 * a tile inside its home room (see ROOMS below).
 *
 * Rendering is 2.5D isometric: each tile is a 64×32 diamond. `tileToIso()`
 * projects a tile coord into world pixel space, with `ISO_OFFSET_X` chosen
 * so the leftmost diamond sits at world x = 0.
 */

export const TILE_W = 64;
export const TILE_H = 32;
export const GRID_W = 22;
export const GRID_H = 16;

// World extent of the iso projection.
//   minX = (0 - (GRID_H-1)) * TILE_W/2
//   maxX = (GRID_W-1) * TILE_W/2  +  TILE_W
export const ISO_OFFSET_X = (GRID_H - 1) * (TILE_W / 2);     // 480
export const WORLD_W      = (GRID_W + GRID_H - 1) * (TILE_W / 2) + TILE_W;   // 1248
export const WORLD_H      = (GRID_W + GRID_H - 1) * (TILE_H / 2) + TILE_H * 2;  // 624

// Dark-editorial palette (matches webclient/index.html CSS vars).
export const PALETTE = {
  hall:       0x1a1410,
  floorBase:  0x271c14,
  floorAlt:   0x2f221a,
  wallLeft:   0x140d09,
  wallBack:   0x1b1410,
  accent:     0xc8a35b,
  text:       0xf4ecdf,
  muted:      0x9a8a78,
  ok:         0x8bc28b,
  error:      0xd96565,
  warn:       0xe2b463,
};

/**
 * Rooms — every rectangle is inclusive and is sized so each agent's raw
 * `desk_x, desk_y` from importer.py falls inside its home room.
 *
 *   marketing: Oaklyn(10,4) S&K(12,4) Dex(14,4) Nova(16,4) Echo(18,4)
 *   cos:       Nelly(4,2)  Sable(6,2)
 *   board:     Clu(2,2)
 *   operations: Rex(4,8)   Aspyn(10,8) Cipher(12,8) Vibe(14,8)
 *   research:  Rhythm(4,12)
 *   production: Camdyn(12,12) Cole(14,12)
 *   post-prod: Onyx(16,12)
 */
export const ROOMS = [
  { id: "ceo",        label: "CEO Office",        x1: 1,  y1: 1,  x2: 3,  y2: 4,  tone: 0x33251c },
  { id: "cos",        label: "CoS Corner",        x1: 4,  y1: 1,  x2: 8,  y2: 4,  tone: 0x2e2218 },
  { id: "marketing",  label: "Marketing Bullpen", x1: 9,  y1: 1,  x2: 20, y2: 5,  tone: 0x2a1f18 },
  { id: "ops",        label: "Operations Floor",  x1: 1,  y1: 7,  x2: 16, y2: 10, tone: 0x261c14 },
  { id: "research",   label: "Research Lab",      x1: 1,  y1: 11, x2: 6,  y2: 14, tone: 0x2a1f18 },
  { id: "production", label: "Production Booth",  x1: 8,  y1: 11, x2: 14, y2: 14, tone: 0x2c1f18 },
  { id: "postprod",   label: "Post-prod",         x1: 15, y1: 11, x2: 20, y2: 14, tone: 0x2e2018 },
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

/** Per-department sprite tint. */
export const DEPT_COLORS = {
  board:       0xc8a35b,  // gold
  cos:         0xe9d4a3,  // cream
  marketing:   0xe8a76c,  // peach
  operations:  0x7fb0a6,  // teal
  research:    0xa3c88b,  // sage
  production:  0xd9728e,  // rose
  "post-prod": 0xb086c8,  // violet
};

/** Per-agent role glyph (displayed above the head). */
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

/** Project a (tileX, tileY) into iso world pixel space (top-center of diamond). */
export function tileToIso(tileX, tileY) {
  const x = (tileX - tileY) * (TILE_W / 2) + ISO_OFFSET_X;
  const y = (tileX + tileY) * (TILE_H / 2);
  return { x, y };
}

/** Center of the tile diamond, where a sprite should stand. */
export function tileToIsoCenter(tileX, tileY) {
  const { x, y } = tileToIso(tileX, tileY);
  return { x: x + TILE_W / 2, y: y + TILE_H / 2 };
}

/** Map a raw desk_x, desk_y (from the DB) to its iso anchor point. */
export function deskToWorld(deskX, deskY) {
  // Clamp into grid bounds so a malformed seed never escapes the floor.
  const tileX = Math.max(0, Math.min(GRID_W - 1, deskX));
  const tileY = Math.max(0, Math.min(GRID_H - 1, deskY));
  const { x: px, y: py } = tileToIsoCenter(tileX, tileY);
  return { tileX, tileY, px, py };
}

/** Pick a random idle wander target inside the agent's home room. */
export function randomTileInRoom(roomId, rng = Math.random) {
  const room = ROOMS.find(r => r.id === roomId) || ROOMS[0];
  const x = room.x1 + Math.floor(rng() * (room.x2 - room.x1 + 1));
  const y = room.y1 + Math.floor(rng() * (room.y2 - room.y1 + 1));
  const { x: px, y: py } = tileToIsoCenter(x, y);
  return { tileX: x, tileY: y, px, py };
}

/** Build the 4 vertices of a tile diamond in world pixel space. */
export function diamondPoints(tileX, tileY) {
  const { x, y } = tileToIso(tileX, tileY);
  const halfW = TILE_W / 2;
  const halfH = TILE_H / 2;
  return [
    x + halfW, y,              // top
    x + TILE_W, y + halfH,     // right
    x + halfW, y + TILE_H,     // bottom
    x, y + halfH,              // left
  ];
}
