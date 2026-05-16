'use strict';

// Compatibility shim for older tests/imports. The current implementation was
// renamed to Higgsfield Director, but the public contract is still a video
// director agent with systemPrompt + buildUserMessage exports.
const higgsfieldDirector = require('./higgsfield-director');

const systemPrompt = `${higgsfieldDirector.systemPrompt}

Legacy transition vocabulary retained for compatibility:
- Camera movement: Dolly, Steadicam, Speed Ramp
- Transition types: Smash Cut, Match Cut`;

module.exports = {
  ...higgsfieldDirector,
  systemPrompt,
};
