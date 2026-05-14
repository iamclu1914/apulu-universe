/**
 * Apulu HQ — Phaser 3 isometric scene.
 *
 * 2.5D top-down-angled map of the label HQ. Renders rooms as diamond floor
 * tiles with raised platform edges (left + back walls), places every agent
 * as a procedural sprite at their desk, drives a per-agent state machine
 * (idle / walking / working / chatting / error / success) from the existing
 * WebSocket event stream.
 *
 * No build step. No external assets. Phaser 3 from CDN.
 */

import {
  TILE_W, TILE_H, GRID_W, GRID_H, WORLD_W, WORLD_H,
  ROOMS, PALETTE, DEPT_TO_ROOM, DEPT_COLORS, AGENT_GLYPHS,
  tileToIso, tileToIsoCenter, deskToWorld, randomTileInRoom, diamondPoints,
} from "./mapdata.js";

const SPRITE_KEY_PREFIX = "sprite_dept_";

const WALK_SPEED_PX_PER_S = 90;
const IDLE_DWELL_MS_MIN = 6000;
const IDLE_DWELL_MS_MAX = 14000;
const SUCCESS_HOLD_MS = 3000;
const ERROR_HOLD_MS = 6000;


export class HQScene extends Phaser.Scene {

  constructor() {
    super({ key: "HQScene" });
    this.agents = [];
    this.agentById = new Map();
    this.onSelectAgent = null;
  }

  init(data) {
    this.agents = (data?.agents || []).slice();
    this.onSelectAgent = data?.onSelectAgent || (() => {});
  }

  preload() {
    // One sprite texture per department tint so we can swap by dept cheaply.
    for (const [dept, color] of Object.entries(DEPT_COLORS)) {
      this._genSprite(`${SPRITE_KEY_PREFIX}${dept}`, color);
    }
    // Fallback / state tints
    this._genSprite(`${SPRITE_KEY_PREFIX}__walking`, 0xf4ecdf);
    this._genSprite(`${SPRITE_KEY_PREFIX}__working`, 0x8bc28b);
    this._genSprite(`${SPRITE_KEY_PREFIX}__error`,   0xd96565);
  }

  _genSprite(key, fill) {
    // 26×38 figure with iso-style shadow.
    const g = this.make.graphics({ x: 0, y: 0, add: false });
    // iso shadow ellipse beneath the feet
    g.fillStyle(0x000000, 0.45);
    g.fillEllipse(13, 36, 18, 5);
    // legs
    g.fillStyle(0x140d09, 1);
    g.fillRect(9, 26, 3, 8);
    g.fillRect(14, 26, 3, 8);
    // body (dept tint)
    g.fillStyle(fill, 1);
    g.fillRoundedRect(6, 13, 14, 14, 3);
    // body highlight
    g.fillStyle(0xffffff, 0.12);
    g.fillRoundedRect(6, 13, 14, 5, { tl: 3, tr: 3, bl: 0, br: 0 });
    // head
    g.fillStyle(0xeed7b5, 1);
    g.fillCircle(13, 7, 5);
    // hair / cap rim
    g.fillStyle(0xc8a35b, 1);
    g.fillRect(8, 2, 10, 2);
    g.generateTexture(key, 26, 38);
    g.destroy();
  }

  create() {
    this.cameras.main.setBackgroundColor(0x140d09);
    this.cameras.main.setBounds(0, 0, WORLD_W, WORLD_H);
    this.cameras.main.setSize(this.scale.width, this.scale.height);

    // Render order: floor → room platforms → desks → agents.
    this._drawFloor();
    this._drawRoomPlatforms();
    this._drawDesks();

    this.agents.forEach(a => this._spawnAgent(a));

    // Idle wander loop
    this.time.addEvent({
      delay: 2500,
      loop: true,
      callback: () => this._tickWander(),
    });

    this._setupPan();

    // Center camera roughly on the building.
    this.cameras.main.centerOn(WORLD_W / 2, WORLD_H / 2);

    this.scale.on("resize", (size) => {
      this.cameras.main.setSize(size.width, size.height);
    });
  }

  _drawFloor() {
    // Solid hall background
    const bg = this.add.graphics();
    bg.fillStyle(PALETTE.hall, 1);
    bg.fillRect(0, 0, WORLD_W, WORLD_H);
    bg.setDepth(-1000);

    // Faint base diamond grid (every tile, very low alpha)
    const g = this.add.graphics();
    g.setDepth(-900);
    for (let y = 0; y < GRID_H; y++) {
      for (let x = 0; x < GRID_W; x++) {
        const pts = diamondPoints(x, y);
        g.lineStyle(1, 0x000000, 0.25);
        g.beginPath();
        g.moveTo(pts[0], pts[1]);
        g.lineTo(pts[2], pts[3]);
        g.lineTo(pts[4], pts[5]);
        g.lineTo(pts[6], pts[7]);
        g.closePath();
        g.strokePath();
      }
    }
  }

  _drawRoomPlatforms() {
    ROOMS.forEach(room => {
      // Each room is rendered as filled diamonds + back-left walls so it
      // looks like a raised platform with a back-left corner.
      this._drawRoomFloor(room);
      this._drawRoomWalls(room);
      this._drawRoomLabel(room);
    });
  }

  _drawRoomFloor(room) {
    const g = this.add.graphics();
    g.setDepth(-800);
    for (let y = room.y1; y <= room.y2; y++) {
      for (let x = room.x1; x <= room.x2; x++) {
        const pts = diamondPoints(x, y);
        // Alternate tint per tile for a parquet feel
        const alt = ((x + y) % 2 === 0) ? room.tone : this._shade(room.tone, 0.92);
        g.fillStyle(alt, 1);
        g.beginPath();
        g.moveTo(pts[0], pts[1]);
        g.lineTo(pts[2], pts[3]);
        g.lineTo(pts[4], pts[5]);
        g.lineTo(pts[6], pts[7]);
        g.closePath();
        g.fillPath();
      }
    }
    // Gold accent outline around the room perimeter (corner-to-corner)
    const top    = tileToIso(room.x1, room.y1);
    const right  = tileToIso(room.x2 + 1, room.y1);
    const bottom = tileToIso(room.x2 + 1, room.y2 + 1);
    const left   = tileToIso(room.x1, room.y2 + 1);
    g.lineStyle(1.5, PALETTE.accent, 0.55);
    g.beginPath();
    g.moveTo(top.x + TILE_W / 2, top.y);
    g.lineTo(right.x + TILE_W / 2, right.y);
    g.lineTo(bottom.x + TILE_W / 2, bottom.y);
    g.lineTo(left.x + TILE_W / 2, left.y);
    g.closePath();
    g.strokePath();
  }

  _drawRoomWalls(room) {
    // Back wall: along y = room.y1, from x=room.x1 to x=room.x2+1
    // Left wall: along x = room.x1, from y=room.y1 to y=room.y2+1
    const wallHeight = 28;  // pixels lifted in -y direction

    const back = this.add.graphics();
    back.setDepth(-700);
    back.fillStyle(PALETTE.wallBack, 1);
    const a = tileToIso(room.x1, room.y1);
    const b = tileToIso(room.x2 + 1, room.y1);
    back.beginPath();
    back.moveTo(a.x + TILE_W / 2, a.y);
    back.lineTo(b.x + TILE_W / 2, b.y);
    back.lineTo(b.x + TILE_W / 2, b.y - wallHeight);
    back.lineTo(a.x + TILE_W / 2, a.y - wallHeight);
    back.closePath();
    back.fillPath();
    back.lineStyle(1, PALETTE.accent, 0.25);
    back.strokePath();

    const left = this.add.graphics();
    left.setDepth(-700);
    left.fillStyle(PALETTE.wallLeft, 1);
    const c = tileToIso(room.x1, room.y1);
    const d = tileToIso(room.x1, room.y2 + 1);
    left.beginPath();
    left.moveTo(c.x + TILE_W / 2, c.y);
    left.lineTo(d.x + TILE_W / 2, d.y);
    left.lineTo(d.x + TILE_W / 2, d.y - wallHeight);
    left.lineTo(c.x + TILE_W / 2, c.y - wallHeight);
    left.closePath();
    left.fillPath();
    left.lineStyle(1, PALETTE.accent, 0.25);
    left.strokePath();
  }

  _drawRoomLabel(room) {
    // Place label above the back wall, near the back-left corner.
    const anchor = tileToIso(room.x1, room.y1);
    const label = this.add.text(
      anchor.x + TILE_W / 2 + 6,
      anchor.y - 24,
      room.label.toUpperCase(),
      {
        fontFamily: "Raleway, system-ui, sans-serif",
        fontSize: "10px",
        color: "#c8a35b",
        fontStyle: "bold",
      },
    );
    label.setLetterSpacing(2);
    label.setAlpha(0.85);
    label.setDepth(-600);
  }

  _drawDesks() {
    this.agents.forEach(a => {
      const p = deskToWorld(a.deskX, a.deskY);
      a._desk = p;
      // Iso desk: small dark diamond patch at the back of the tile
      const { x, y } = tileToIso(p.tileX, p.tileY);
      const g = this.add.graphics();
      g.setDepth(p.py - 1);  // just behind the agent
      g.fillStyle(0x100b08, 0.92);
      g.beginPath();
      g.moveTo(x + TILE_W / 2,          y + 6);
      g.lineTo(x + TILE_W - 8,          y + TILE_H / 2);
      g.lineTo(x + TILE_W / 2,          y + TILE_H - 6);
      g.lineTo(x + 8,                   y + TILE_H / 2);
      g.closePath();
      g.fillPath();
      g.lineStyle(1, PALETTE.accent, 0.45);
      g.strokePath();
    });
  }

  _spawnAgent(a) {
    const p = a._desk;
    const dept = a.department || "operations";
    const baseKey = `${SPRITE_KEY_PREFIX}${dept}`;
    a._baseTextureKey = baseKey;

    const sprite = this.add.sprite(p.px, p.py - 14, baseKey);
    sprite.setOrigin(0.5, 1);
    sprite.setInteractive({ useHandCursor: true });
    sprite.on("pointerdown", () => this.onSelectAgent(a.id));

    // Role glyph above head — always visible
    const glyph = AGENT_GLYPHS[a.displayName] || "•";
    const glyphText = this.add.text(p.px, p.py - 48, glyph, {
      fontSize: "14px",
      color: "#f4ecdf",
    }).setOrigin(0.5, 0.5);

    // Name tag — hover-only
    const nameTag = this.add.text(p.px, p.py - 60, a.displayName, {
      fontFamily: "Raleway, system-ui, sans-serif",
      fontSize: "10px",
      color: "#f4ecdf",
      backgroundColor: "#100b08",
      padding: { x: 4, y: 2 },
    }).setOrigin(0.5, 1);
    nameTag.setAlpha(0);

    sprite.on("pointerover", () => nameTag.setAlpha(0.95));
    sprite.on("pointerout",  () => nameTag.setAlpha(0));

    // Status floater (state changes)
    const statusText = this.add.text(p.px, p.py - 70, "", {
      fontSize: "16px",
    }).setOrigin(0.5, 0.5);

    a.sprite = sprite;
    a.glyphText = glyphText;
    a.nameTag = nameTag;
    a.statusText = statusText;
    a.state = "idle";
    a.target = null;
    a.dwellUntil = this.time.now + this._randomDwell();
    a._statusHoldUntil = 0;
    a.roomId = DEPT_TO_ROOM[a.department] || "ops";

    this._restyleSprite(a);
    this._updateDepth(a);
    this.agentById.set(a.id, a);
  }

  _updateDepth(a) {
    const d = a.sprite.y;
    a.sprite.setDepth(d);
    a.glyphText.setDepth(d + 1);
    a.nameTag.setDepth(d + 2);
    a.statusText.setDepth(d + 3);
  }

  _randomDwell() {
    return IDLE_DWELL_MS_MIN + Math.random() * (IDLE_DWELL_MS_MAX - IDLE_DWELL_MS_MIN);
  }

  _shade(color, factor) {
    const r = Math.min(255, Math.floor(((color >> 16) & 0xff) * factor));
    const g = Math.min(255, Math.floor(((color >> 8) & 0xff) * factor));
    const b = Math.min(255, Math.floor((color & 0xff) * factor));
    return (r << 16) | (g << 8) | b;
  }

  _tickWander() {
    const now = this.time.now;
    this.agents.forEach(a => {
      if (a.state === "working" || a.state === "chatting" || a.state === "error") return;
      if (a.target) return;
      if (now < a.dwellUntil) return;

      const goHome = Math.random() < 0.4;
      const dest = goHome ? a._desk : randomTileInRoom(a.roomId);
      a.target = dest;
      this._setState(a, "walking");
    });
  }

  update(_time, deltaMs) {
    const dt = deltaMs / 1000;
    const now = this.time.now;

    this.agents.forEach(a => {
      if (a._statusHoldUntil && now > a._statusHoldUntil) {
        a.statusText.setText("");
        a._statusHoldUntil = 0;
        if (a.state === "success" || a.state === "error") {
          this._setState(a, "idle");
        }
      }

      if (a.target && a.state === "walking") {
        const targetY = a.target.py - 14;  // sprite origin is bottom-center, offset to stand on tile
        const dx = a.target.px - a.sprite.x;
        const dy = targetY - a.sprite.y;
        const dist = Math.hypot(dx, dy);
        if (dist < 1.5) {
          a.sprite.setPosition(a.target.px, targetY);
          a.target = null;
          a.dwellUntil = now + this._randomDwell();
          this._setState(a, "idle");
        } else {
          const step = Math.min(dist, WALK_SPEED_PX_PER_S * dt);
          a.sprite.x += (dx / dist) * step;
          a.sprite.y += (dy / dist) * step;
          // Walk-cycle bob
          a.sprite.y += Math.sin(now / 90) * 0.18;
        }
        a.glyphText.setPosition(a.sprite.x, a.sprite.y - 34);
        a.nameTag.setPosition(a.sprite.x, a.sprite.y - 46);
        a.statusText.setPosition(a.sprite.x, a.sprite.y - 56);
        this._updateDepth(a);
      }
    });
  }

  _restyleSprite(a) {
    // Choose texture per state, but fall back to the dept-colored idle texture.
    let key = a._baseTextureKey;
    if (a.state === "walking") key = `${SPRITE_KEY_PREFIX}__walking`;
    else if (a.state === "working") key = `${SPRITE_KEY_PREFIX}__working`;
    else if (a.state === "error")   key = `${SPRITE_KEY_PREFIX}__error`;
    a.sprite.setTexture(key);
    a.sprite.clearTint();
  }

  _setState(a, newState, opts = {}) {
    if (a.state === newState && !opts.force) return;
    a.state = newState;
    this._restyleSprite(a);

    if (opts.floater) {
      a.statusText.setText(opts.floater);
      a._statusHoldUntil = this.time.now + (opts.holdMs || 3000);
    }
  }

  // --- Public event handlers (called from index.html WS dispatcher) ---

  handleRoutineStarted(agentId, _payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    a.target = a._desk;
    this._setState(a, "walking");
    this.time.delayedCall(800, () => {
      if (!a) return;
      a.sprite.setPosition(a._desk.px, a._desk.py - 14);
      a.target = null;
      this._setState(a, "working", { floater: "⚙", holdMs: 4000, force: true });
    });
  }

  handleRoutineSucceeded(agentId, _payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    this._setState(a, "success", { floater: "✅", holdMs: SUCCESS_HOLD_MS, force: true });
    a.dwellUntil = this.time.now + 1500;
  }

  handleRoutineFailed(agentId, _payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    this._setState(a, "error", { floater: "⚠", holdMs: ERROR_HOLD_MS, force: true });
    a.dwellUntil = this.time.now + 2000;
    this.cameras.main.shake(120, 0.003);
  }

  handleRetry(agentId, _payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    this.tweens.add({
      targets: a.sprite,
      alpha: { from: 0.4, to: 1 },
      duration: 250,
      yoyo: true,
      repeat: 1,
    });
    a.statusText.setText("↻");
    a._statusHoldUntil = this.time.now + 1500;
  }

  handleDlqAppended(agentId, _payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    this._setState(a, "error", { floater: "📥", holdMs: 9000, force: true });
  }

  setChatting(agentId) {
    this.agents.forEach(other => {
      if (other.state === "chatting") this._setState(other, "idle", { force: true });
    });
    if (!agentId) return;
    const a = this.agentById.get(agentId); if (!a) return;
    a.target = null;
    a.sprite.setPosition(a._desk.px, a._desk.py - 14);
    this._setState(a, "chatting", { floater: "💬", holdMs: 999999, force: true });
    this.cameras.main.pan(a._desk.px, a._desk.py, 500, "Sine.easeInOut");
  }

  _setupPan() {
    let dragging = false;
    let last = { x: 0, y: 0 };
    this.input.on("pointerdown", (p) => {
      if (p.event && p.event.target && p.event.target.tagName === "CANVAS") {
        dragging = true;
        last = { x: p.x, y: p.y };
      }
    });
    this.input.on("pointermove", (p) => {
      if (!dragging) return;
      this.cameras.main.scrollX -= (p.x - last.x);
      this.cameras.main.scrollY -= (p.y - last.y);
      last = { x: p.x, y: p.y };
    });
    this.input.on("pointerup", () => { dragging = false; });
    this.input.on("pointerupoutside", () => { dragging = false; });
  }
}


export function bootHQMap({ parent, agents, onSelectAgent }) {
  const config = {
    type: Phaser.AUTO,
    parent: parent,
    backgroundColor: "#140d09",
    width: parent.clientWidth || WORLD_W,
    height: parent.clientHeight || WORLD_H,
    scale: {
      mode: Phaser.Scale.RESIZE,
      autoCenter: Phaser.Scale.CENTER_BOTH,
    },
    physics: { default: "arcade" },
    pixelArt: true,
    scene: [HQScene],
  };
  const game = new Phaser.Game(config);
  const sceneData = { agents, onSelectAgent };
  game.scene.start("HQScene", sceneData);
  return new Promise((resolve) => {
    game.events.once("step", () => {
      const scene = game.scene.getScene("HQScene");
      resolve({ game, scene });
    });
  });
}
