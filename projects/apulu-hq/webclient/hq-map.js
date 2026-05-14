/**
 * Apulu HQ — Phaser 3 top-down scene.
 *
 * Compact top-down map of the label HQ. Rooms tile edge-to-edge with
 * interior partition walls. Every agent is a procedural sprite at their
 * desk, driven by a per-agent state machine (idle / walking / working /
 * chatting / error / success) from the WebSocket event stream.
 *
 * No build step. No external assets. Phaser 3 from CDN.
 */

import {
  TILE_SIZE, GRID_W, GRID_H, WORLD_W, WORLD_H,
  ROOMS, PALETTE, DEPT_TO_ROOM, DEPT_COLORS, AGENT_GLYPHS,
  tileCenter, deskToWorld, randomTileInRoom,
} from "./mapdata.js";

const SPRITE_KEY_PREFIX = "sprite_dept_";

const WALK_SPEED_PX_PER_S = 80;
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
    for (const [dept, color] of Object.entries(DEPT_COLORS)) {
      this._genSprite(`${SPRITE_KEY_PREFIX}${dept}`, color);
    }
    this._genSprite(`${SPRITE_KEY_PREFIX}__walking`, 0xf4ecdf);
    this._genSprite(`${SPRITE_KEY_PREFIX}__working`, 0x8bc28b);
    this._genSprite(`${SPRITE_KEY_PREFIX}__error`,   0xd96565);
  }

  _genSprite(key, fill) {
    // 24×28 top-down-ish figure with soft shadow.
    const g = this.make.graphics({ x: 0, y: 0, add: false });
    g.fillStyle(0x000000, 0.4);
    g.fillEllipse(12, 26, 16, 4);
    g.fillStyle(0x140d09, 1);
    g.fillRect(8, 18, 3, 6);
    g.fillRect(13, 18, 3, 6);
    g.fillStyle(fill, 1);
    g.fillRoundedRect(6, 9, 12, 11, 3);
    g.fillStyle(0xffffff, 0.14);
    g.fillRoundedRect(6, 9, 12, 4, { tl: 3, tr: 3, bl: 0, br: 0 });
    g.fillStyle(0xeed7b5, 1);
    g.fillCircle(12, 5, 4);
    g.fillStyle(0xc8a35b, 1);
    g.fillRect(8, 1, 8, 2);
    g.generateTexture(key, 24, 28);
    g.destroy();
  }

  create() {
    this.cameras.main.setBackgroundColor(PALETTE.hall);
    this.cameras.main.setBounds(0, 0, WORLD_W, WORLD_H);
    this.cameras.main.setSize(this.scale.width, this.scale.height);

    this._drawFloor();
    this._drawRooms();
    this._drawPartitions();
    this._drawOuterWall();
    this._drawDesks();

    this.agents.forEach(a => this._spawnAgent(a));

    this.time.addEvent({
      delay: 2500,
      loop: true,
      callback: () => this._tickWander(),
    });

    this._setupPan();

    // Center camera on the building.
    this.cameras.main.centerOn(WORLD_W / 2, WORLD_H / 2);

    this.scale.on("resize", (size) => {
      this.cameras.main.setSize(size.width, size.height);
    });
  }

  _drawFloor() {
    const g = this.add.graphics();
    g.setDepth(-1000);
    g.fillStyle(PALETTE.hall, 1);
    g.fillRect(0, 0, WORLD_W, WORLD_H);
  }

  _drawRooms() {
    ROOMS.forEach(room => {
      const x = room.x1 * TILE_SIZE;
      const y = room.y1 * TILE_SIZE;
      const w = (room.x2 - room.x1 + 1) * TILE_SIZE;
      const h = (room.y2 - room.y1 + 1) * TILE_SIZE;

      // Parquet floor — alternate tile shades for texture
      const g = this.add.graphics();
      g.setDepth(-900);
      for (let ty = room.y1; ty <= room.y2; ty++) {
        for (let tx = room.x1; tx <= room.x2; tx++) {
          const alt = ((tx + ty) % 2 === 0) ? room.tone : this._shade(room.tone, 0.92);
          g.fillStyle(alt, 1);
          g.fillRect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        }
      }

      // Room label — top-left corner, gold
      const label = this.add.text(x + 8, y + 6, room.label.toUpperCase(), {
        fontFamily: "Raleway, system-ui, sans-serif",
        fontSize: "10px",
        color: "#c8a35b",
        fontStyle: "bold",
      });
      label.setLetterSpacing(2);
      label.setAlpha(0.85);
      label.setDepth(-500);
    });
  }

  _drawPartitions() {
    // Draw interior partition walls between adjacent rooms.
    // Build a set of "occupied" tiles for fast lookup, then walk pairs.
    const tileRoom = new Map();
    for (const room of ROOMS) {
      for (let ty = room.y1; ty <= room.y2; ty++) {
        for (let tx = room.x1; tx <= room.x2; tx++) {
          tileRoom.set(`${tx},${ty}`, room.id);
        }
      }
    }
    const g = this.add.graphics();
    g.setDepth(-400);
    g.lineStyle(2, PALETTE.accentDim, 0.7);

    // Vertical edges (between tx,ty and tx+1,ty)
    for (let ty = 0; ty < GRID_H; ty++) {
      for (let tx = 0; tx < GRID_W - 1; tx++) {
        const a = tileRoom.get(`${tx},${ty}`);
        const b = tileRoom.get(`${tx + 1},${ty}`);
        if (a && b && a !== b) {
          const x = (tx + 1) * TILE_SIZE;
          g.lineBetween(x, ty * TILE_SIZE, x, (ty + 1) * TILE_SIZE);
        }
      }
    }
    // Horizontal edges
    for (let tx = 0; tx < GRID_W; tx++) {
      for (let ty = 0; ty < GRID_H - 1; ty++) {
        const a = tileRoom.get(`${tx},${ty}`);
        const b = tileRoom.get(`${tx},${ty + 1}`);
        if (a && b && a !== b) {
          const y = (ty + 1) * TILE_SIZE;
          g.lineBetween(tx * TILE_SIZE, y, (tx + 1) * TILE_SIZE, y);
        }
      }
    }
  }

  _drawOuterWall() {
    const g = this.add.graphics();
    g.setDepth(-300);
    g.lineStyle(3, PALETTE.accent, 0.9);
    // Outline the union of all rooms (which is the rect from min(x1,y1) to max(x2+1,y2+1))
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const r of ROOMS) {
      minX = Math.min(minX, r.x1);
      minY = Math.min(minY, r.y1);
      maxX = Math.max(maxX, r.x2 + 1);
      maxY = Math.max(maxY, r.y2 + 1);
    }
    g.strokeRect(
      minX * TILE_SIZE,
      minY * TILE_SIZE,
      (maxX - minX) * TILE_SIZE,
      (maxY - minY) * TILE_SIZE,
    );
  }

  _drawDesks() {
    this.agents.forEach(a => {
      const p = deskToWorld(a.deskX, a.deskY);
      a._desk = p;
      const g = this.add.graphics();
      g.setDepth(-200);
      g.fillStyle(0x100b08, 0.92);
      g.fillRoundedRect(p.px - 14, p.py + 8, 28, 7, 2);
      g.lineStyle(1, PALETTE.accent, 0.45);
      g.strokeRoundedRect(p.px - 14, p.py + 8, 28, 7, 2);
    });
  }

  _spawnAgent(a) {
    const p = a._desk;
    const dept = a.department || "operations";
    const baseKey = `${SPRITE_KEY_PREFIX}${dept}`;
    a._baseTextureKey = baseKey;

    const sprite = this.add.sprite(p.px, p.py, baseKey);
    sprite.setInteractive({ useHandCursor: true });
    sprite.on("pointerdown", () => this.onSelectAgent(a.id));

    const glyph = AGENT_GLYPHS[a.displayName] || "•";
    const glyphText = this.add.text(p.px, p.py - 22, glyph, {
      fontSize: "13px",
      color: "#f4ecdf",
    }).setOrigin(0.5, 0.5);

    const nameTag = this.add.text(p.px, p.py - 36, a.displayName, {
      fontFamily: "Raleway, system-ui, sans-serif",
      fontSize: "10px",
      color: "#f4ecdf",
      backgroundColor: "#100b08",
      padding: { x: 4, y: 2 },
    }).setOrigin(0.5, 1);
    nameTag.setAlpha(0);

    sprite.on("pointerover", () => nameTag.setAlpha(0.95));
    sprite.on("pointerout",  () => nameTag.setAlpha(0));

    const statusText = this.add.text(p.px, p.py - 24, "", {
      fontSize: "15px",
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
        const dx = a.target.px - a.sprite.x;
        const dy = a.target.py - a.sprite.y;
        const dist = Math.hypot(dx, dy);
        if (dist < 1.5) {
          a.sprite.setPosition(a.target.px, a.target.py);
          a.target = null;
          a.dwellUntil = now + this._randomDwell();
          this._setState(a, "idle");
        } else {
          const step = Math.min(dist, WALK_SPEED_PX_PER_S * dt);
          a.sprite.x += (dx / dist) * step;
          a.sprite.y += (dy / dist) * step;
          a.sprite.y += Math.sin(now / 90) * 0.18;
        }
        a.glyphText.setPosition(a.sprite.x, a.sprite.y - 22);
        a.nameTag.setPosition(a.sprite.x, a.sprite.y - 36);
        a.statusText.setPosition(a.sprite.x, a.sprite.y - 24);
        this._updateDepth(a);
      }
    });
  }

  _restyleSprite(a) {
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

  // --- Public event handlers ---

  handleRoutineStarted(agentId, _payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    a.target = a._desk;
    this._setState(a, "walking");
    this.time.delayedCall(800, () => {
      if (!a) return;
      a.sprite.setPosition(a._desk.px, a._desk.py);
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
    a.sprite.setPosition(a._desk.px, a._desk.py);
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
