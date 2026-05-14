/**
 * Apulu HQ — Phaser 3 scene.
 *
 * Top-down 2D map of the label HQ. Renders rooms as colored floor tiles,
 * draws every agent as a procedural sprite at their desk, drives a per-agent
 * state machine (idle / walking / working / chatting / error / success)
 * from the existing WebSocket event stream.
 *
 * No build step. No external sprite assets. Uses Phaser 3 from CDN, but the
 * scene is fully self-contained and can be torn down without leaking.
 */

import {
  TILE_SIZE, GRID_W, GRID_H, WORLD_W, WORLD_H,
  ROOMS, PALETTE, DEPT_TO_ROOM, deskToWorld, randomTileInRoom,
} from "./mapdata.js";

// Per-agent sprite cache so we can swap textures by state.
const SPRITE_KEYS = {
  idle:    "sprite_idle",
  walking: "sprite_walking",
  working: "sprite_working",
  error:   "sprite_error",
};

const STATE_TINTS = {
  idle:     0xc8a35b,
  walking:  0xf4ecdf,
  working:  0x8bc28b,
  chatting: 0xc8a35b,
  error:    0xd96565,
  success:  0x8bc28b,
};

const WALK_SPEED_PX_PER_S = 70;
const IDLE_DWELL_MS_MIN = 6000;
const IDLE_DWELL_MS_MAX = 14000;
const SUCCESS_HOLD_MS = 3000;
const ERROR_HOLD_MS = 6000;


export class HQScene extends Phaser.Scene {

  constructor() {
    super({ key: "HQScene" });
    this.agents = [];                 // [{id, displayName, dept, roomId, sprite, statusText, state, target, dwellUntil}]
    this.agentById = new Map();
    this.onSelectAgent = null;        // callback set from index.html
  }

  init(data) {
    this.agents = (data?.agents || []).slice();
    this.onSelectAgent = data?.onSelectAgent || (() => {});
  }

  preload() {
    // Generate all sprites procedurally so the scene ships with no assets.
    this._genSprite(SPRITE_KEYS.idle,    0xc8a35b);
    this._genSprite(SPRITE_KEYS.walking, 0xe9d4a3);
    this._genSprite(SPRITE_KEYS.working, 0x8bc28b);
    this._genSprite(SPRITE_KEYS.error,   0xd96565);
  }

  _genSprite(key, fill) {
    // 24×28 px figure: head + body + legs, with a tiny shadow ellipse below.
    const g = this.make.graphics({ x: 0, y: 0, add: false });
    // shadow
    g.fillStyle(0x000000, 0.35);
    g.fillEllipse(12, 26, 14, 4);
    // legs
    g.fillStyle(0x100b08, 1);
    g.fillRect(8, 18, 3, 6);
    g.fillRect(13, 18, 3, 6);
    // body
    g.fillStyle(fill, 1);
    g.fillRoundedRect(6, 9, 12, 11, 2);
    // head
    g.fillStyle(0xeed7b5, 1);
    g.fillCircle(12, 5, 4);
    // hair / cap accent (gold rim)
    g.fillStyle(0xc8a35b, 1);
    g.fillRect(8, 1, 8, 2);
    g.generateTexture(key, 24, 28);
    g.destroy();
  }

  create() {
    this.cameras.main.setBackgroundColor(0x1a1410);
    this.cameras.main.setBounds(0, 0, WORLD_W, WORLD_H);
    this.cameras.main.setSize(this.scale.width, this.scale.height);

    // --- Floor + rooms ---
    this._drawFloor();
    this._drawRooms();
    this._drawDesks();

    // --- Agents ---
    this.agents.forEach(a => this._spawnAgent(a));

    // --- Wander loop ---
    this.time.addEvent({
      delay: 2500,
      loop: true,
      callback: () => this._tickWander(),
    });

    // --- Click-and-drag camera pan ---
    this._setupPan();

    // Resize handler so the canvas adapts to its container.
    this.scale.on("resize", (size) => {
      this.cameras.main.setSize(size.width, size.height);
    });
  }

  _drawFloor() {
    const g = this.add.graphics();
    g.fillStyle(PALETTE.hall, 1);
    g.fillRect(0, 0, WORLD_W, WORLD_H);
    // subtle grid
    g.lineStyle(1, 0x000000, 0.15);
    for (let x = 0; x <= GRID_W; x++) {
      g.lineBetween(x * TILE_SIZE, 0, x * TILE_SIZE, WORLD_H);
    }
    for (let y = 0; y <= GRID_H; y++) {
      g.lineBetween(0, y * TILE_SIZE, WORLD_W, y * TILE_SIZE);
    }
  }

  _drawRooms() {
    ROOMS.forEach(room => {
      const x = room.x1 * TILE_SIZE;
      const y = room.y1 * TILE_SIZE;
      const w = (room.x2 - room.x1 + 1) * TILE_SIZE;
      const h = (room.y2 - room.y1 + 1) * TILE_SIZE;
      const g = this.add.graphics();
      g.fillStyle(room.tone, 1);
      g.fillRect(x, y, w, h);
      g.lineStyle(2, PALETTE.accent, 0.45);
      g.strokeRect(x + 1, y + 1, w - 2, h - 2);

      // Room label
      const label = this.add.text(x + 8, y + 6, room.label.toUpperCase(), {
        fontFamily: "Raleway, system-ui, sans-serif",
        fontSize: "10px",
        color: "#c8a35b",
        fontStyle: "bold",
      });
      label.setLetterSpacing(2);
      label.setAlpha(0.8);
    });
  }

  _drawDesks() {
    this.agents.forEach(a => {
      const p = deskToWorld(a.deskX, a.deskY);
      a._desk = p;
      const g = this.add.graphics();
      g.fillStyle(0x100b08, 0.9);
      g.fillRoundedRect(p.px - 12, p.py + 8, 24, 6, 1);
      g.lineStyle(1, PALETTE.accent, 0.4);
      g.strokeRoundedRect(p.px - 12, p.py + 8, 24, 6, 1);
    });
  }

  _spawnAgent(a) {
    const p = a._desk;
    const sprite = this.add.sprite(p.px, p.py, SPRITE_KEYS.idle);
    sprite.setInteractive({ useHandCursor: true });
    sprite.setTint(STATE_TINTS.idle);
    sprite.on("pointerdown", () => this.onSelectAgent(a.id));

    const nameTag = this.add.text(p.px, p.py + 18, a.displayName, {
      fontFamily: "Raleway, system-ui, sans-serif",
      fontSize: "9px",
      color: "#f4ecdf",
    }).setOrigin(0.5, 0);
    nameTag.setAlpha(0.85);

    const statusText = this.add.text(p.px, p.py - 24, "", {
      fontSize: "14px",
    }).setOrigin(0.5, 0.5);

    a.sprite = sprite;
    a.nameTag = nameTag;
    a.statusText = statusText;
    a.state = "idle";
    a.target = null;
    a.dwellUntil = this.time.now + this._randomDwell();
    a._statusHoldUntil = 0;
    a.roomId = DEPT_TO_ROOM[a.department] || "common";
    this.agentById.set(a.id, a);
  }

  _randomDwell() {
    return IDLE_DWELL_MS_MIN + Math.random() * (IDLE_DWELL_MS_MAX - IDLE_DWELL_MS_MIN);
  }

  _tickWander() {
    const now = this.time.now;
    this.agents.forEach(a => {
      if (a.state === "working" || a.state === "chatting" || a.state === "error") return;
      if (a.target) return;
      if (now < a.dwellUntil) return;

      // Pick a new random tile inside the home room (with a slight chance of
      // returning to the desk).
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
      // Clear transient floaters when their hold expires.
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
          // Walk-cycle bob
          a.sprite.y += Math.sin(now / 90) * 0.15;
        }
        a.nameTag.setPosition(a.sprite.x, a.sprite.y + 18);
        a.statusText.setPosition(a.sprite.x, a.sprite.y - 24);
      }
    });
  }

  _setState(a, newState, opts = {}) {
    if (a.state === newState) return;
    a.state = newState;

    const tint = STATE_TINTS[newState] || STATE_TINTS.idle;
    a.sprite.setTint(tint);

    const textureKey = newState === "walking" ? SPRITE_KEYS.walking
                     : newState === "working" ? SPRITE_KEYS.working
                     : newState === "error"   ? SPRITE_KEYS.error
                     : SPRITE_KEYS.idle;
    a.sprite.setTexture(textureKey);

    if (opts.floater) {
      a.statusText.setText(opts.floater);
      a._statusHoldUntil = this.time.now + (opts.holdMs || 3000);
    }
  }

  // --- Public event handlers (called from index.html WS dispatcher) ---

  handleRoutineStarted(agentId, payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    a.target = a._desk;
    this._setState(a, "walking");
    // After a brief moment, sit and "work"
    this.time.delayedCall(800, () => {
      if (!a) return;
      a.sprite.setPosition(a._desk.px, a._desk.py);
      a.target = null;
      this._setState(a, "working", { floater: "⚙", holdMs: 4000 });
    });
  }

  handleRoutineSucceeded(agentId, payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    this._setState(a, "success", { floater: "✅", holdMs: SUCCESS_HOLD_MS });
    a.dwellUntil = this.time.now + 1500;
  }

  handleRoutineFailed(agentId, payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    this._setState(a, "error", { floater: "⚠", holdMs: ERROR_HOLD_MS });
    a.dwellUntil = this.time.now + 2000;
    this.cameras.main.shake(120, 0.003);
  }

  handleRetry(agentId, payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    // Yellow pulse on the existing state — don't change state.
    a.sprite.setTint(STATE_TINTS.success);  // momentarily warm
    this.tweens.add({
      targets: a.sprite,
      alpha: { from: 0.4, to: 1 },
      duration: 250,
      yoyo: true,
      repeat: 1,
      onComplete: () => {
        a.sprite.setTint(STATE_TINTS[a.state] || STATE_TINTS.idle);
        a.sprite.setAlpha(1);
      },
    });
    a.statusText.setText("↻");
    a._statusHoldUntil = this.time.now + 1500;
  }

  handleDlqAppended(agentId, payload) {
    const a = this.agentById.get(agentId); if (!a) return;
    this._setState(a, "error", { floater: "📥", holdMs: 9000 });
  }

  setChatting(agentId) {
    // Reset all chatting → idle first
    this.agents.forEach(other => {
      if (other.state === "chatting") this._setState(other, "idle");
    });
    if (!agentId) return;
    const a = this.agentById.get(agentId); if (!a) return;
    a.target = a._desk;
    a.sprite.setPosition(a._desk.px, a._desk.py);
    this._setState(a, "chatting", { floater: "💬", holdMs: 999999 });
    // Pan camera to them
    this.cameras.main.pan(a._desk.px, a._desk.py, 500, "Sine.easeInOut");
  }

  _setupPan() {
    let dragging = false;
    let last = { x: 0, y: 0 };
    this.input.on("pointerdown", (p) => {
      // Only start panning if the click didn't hit an interactive sprite.
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


/** Boot a Phaser game into the given DOM element. Returns {game, scene}. */
export function bootHQMap({ parent, agents, onSelectAgent }) {
  const config = {
    type: Phaser.AUTO,
    parent: parent,
    backgroundColor: "#1a1410",
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
  // Phaser doesn't synchronously expose the scene after start(); wait one frame.
  return new Promise((resolve) => {
    game.events.once("step", () => {
      const scene = game.scene.getScene("HQScene");
      resolve({ game, scene });
    });
  });
}
