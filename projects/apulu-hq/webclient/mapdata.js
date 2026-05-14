/**
 * Apulu HQ — floor plan data.
 *
 * The map is a 30-column × 18-row grid. Each tile is 32 px → world is 960×576.
 * Department regions are listed as inclusive rectangles {x1,y1,x2,y2}.
 *
 * Agent desks come from the SQLite `agents` table (desk_x, desk_y) at runtime.
 * The seeded coordinates from importer.py are intentionally spread out across
 * 4×4 to 18×12 — see AGENT_SEEDS in apulu_hq/importer.py for the layout intent.
 * We translate those coords into pixel positions inside this grid in hq-map.js.
 */

export const TILE_SIZE = 32;
export const GRID_W = 30;
export const GRID_H = 18;
export const WORLD_W = TILE_SIZE * GRID_W;   // 960
export const WORLD_H = TILE_SIZE * GRID_H;   // 576

// Colors from the dark editorial palette (matches webclient/index.html CSS vars)
export const PALETTE = {
  floor:       0x2a1f18,  // --surface
  floorAlt:    0x382a20,  // --surface-2
  wall:        0x100b08,
  accent:      0xc8a35b,  // --gold
  text:        0xf4ecdf,  // --text
  muted:       0x9a8a78,
  ok:          0x8bc28b,
  error:       0xd96565,
  warn:        0xe2b463,
  hall:        0x231a14,
};

/** Rooms — each has a label and an inclusive tile rect. */
export const ROOMS = [
  // Top row
  { id: "ceo",        label: "CEO Office",        x1: 1,  y1: 1,  x2: 6,  y2: 4,  tone: 0x33251c },
  { id: "cos",        label: "CoS Corner",        x1: 8,  y1: 1,  x2: 13, y2: 4,  tone: 0x2e2218 },
  { id: "marketing",  label: "Marketing Bullpen", x1: 15, y1: 1,  x2: 28, y2: 7,  tone: 0x2a1f18 },
  // Middle row
  { id: "research",   label: "Research Lab",      x1: 1,  y1: 6,  x2: 13, y2: 13, tone: 0x261c14 },
  // Lower right
  { id: "production", label: "Production Booth",  x1: 15, y1: 9,  x2: 22, y2: 13, tone: 0x2a1f18 },
  { id: "postprod",   label: "Post-prod",         x1: 24, y1: 9,  x2: 28, y2: 13, tone: 0x2e2018 },
  // Hallway / common (decorative — drawn last)
  { id: "common",     label: "Common",            x1: 1,  y1: 15, x2: 28, y2: 17, tone: 0x231a14 },
];

/** Department → room mapping (used to constrain idle wandering). */
export const DEPT_TO_ROOM = {
  board:      "ceo",
  cos:        "cos",
  marketing:  "marketing",
  research:   "research",
  operations: "research",   // operations team sits in research lab area
  production: "production",
  "post-prod": "postprod",
};

/**
 * Map a (desk_x, desk_y) from the agent registry into a world pixel position.
 * Seed coords roughly span x∈[2..18], y∈[2..12]; scale to our 30×18 grid.
 */
export function deskToWorld(deskX, deskY) {
  // Pad inside the room with a 1-tile margin; clamp into grid bounds.
  const tileX = Math.max(1, Math.min(GRID_W - 2, Math.round(deskX * 1.5)));
  const tileY = Math.max(1, Math.min(GRID_H - 2, Math.round(deskY * 1.3)));
  return {
    tileX,
    tileY,
    px: tileX * TILE_SIZE + TILE_SIZE / 2,
    py: tileY * TILE_SIZE + TILE_SIZE / 2,
  };
}

/** Pick a random idle wander target inside the agent's home room. */
export function randomTileInRoom(roomId, rng = Math.random) {
  const room = ROOMS.find(r => r.id === roomId) || ROOMS[0];
  const x = room.x1 + Math.floor(rng() * (room.x2 - room.x1 + 1));
  const y = room.y1 + Math.floor(rng() * (room.y2 - room.y1 + 1));
  return {
    tileX: x,
    tileY: y,
    px: x * TILE_SIZE + TILE_SIZE / 2,
    py: y * TILE_SIZE + TILE_SIZE / 2,
  };
}
