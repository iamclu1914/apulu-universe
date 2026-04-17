---
title: "Seedance 2.0 Integration Roadmap — Apulu Prompt Generator Enhancement"
date: 2026-04-10
tags: [integration-roadmap, seedance, apulu-prompt-generator, implementation, apu-12]
source: APU-12
author: Pixel (AI Prompt Researcher)
status: ready-for-implementation
---

# Seedance 2.0 Integration Roadmap — Apulu Prompt Generator Enhancement

> [!info] APU-12 Deliverable
> Comprehensive roadmap for integrating Seedance 2.0 capabilities into the existing Apulu Prompt Generator, enhancing the tool with ByteDance's multimodal AI video generation platform.

## Executive Summary

**Objective**: Seamlessly integrate Seedance 2.0 functionality into the existing Apulu Prompt Generator web application, providing Vawn's production team with a unified interface for generating AI video content using multiple platforms (Kling, Higgsfield, and Seedance 2.0).

**Strategy**: Additive integration that preserves existing Higgsfield/Kling workflows while introducing Seedance 2.0-specific features and prompt engineering capabilities.

---

## Current System Architecture Analysis

### Existing Capabilities
- **Frontend**: HTML5 web interface with multi-platform support (Nano Banana 2, Kling 3.0, Higgsfield)
- **Backend**: Node.js/Express server with agent-based pipeline processing
- **Prompt Engineering**: Sophisticated prompt templates for cinematic video generation
- **Character Consistency**: Visual lock system for maintaining character across shots
- **Workflow Types**: Text-to-video, image-to-video, start/end frame workflows

### Current Platform Support Matrix
| Platform | Type | Current Support | Strengths |
|----------|------|----------------|-----------|
| **Nano Banana 2** | Image Generation | ✅ Full | High-quality character images |
| **Kling 3.0** | Video Generation | ✅ Full | Cinematic quality, 15-30s clips |
| **Higgsfield Cinema** | Video + Character | ✅ Full | Character consistency, SoulCast |
| **Seedance 2.0** | Video + Audio | ❌ None | Audio-visual sync, 15s clips |

---

## Seedance 2.0 Integration Strategy

### Integration Approach: Platform Parity
**Philosophy**: Seedance 2.0 becomes a first-class citizen alongside Kling and Higgsfield, with specialized features that leverage its unique audio-visual synchronization capabilities.

### Key Differentiators for Seedance 2.0 Integration
1. **Native Audio Sync**: Upload mastered tracks from Vawn pipeline (Freq/Slate output)
2. **6-Step Prompt Formula**: Implement structured prompt input (Subject → Action → Environment → Camera → Style → Constraints)
3. **Timeline Prompting**: Multi-shot sequence planning with timestamp coordination
4. **Reference Image System**: @image1, @image2 tagging for character consistency
5. **Phoneme-Level Lip Sync**: Enhanced for hip-hop/rap content
6. **Beat Synchronization**: Precise rhythm matching with uploaded tracks

---

## Technical Architecture Enhancement

### Frontend UI Enhancements

#### 1. Platform Selection Enhancement
**Current**: Toggle between Kling and Higgsfield
**Enhanced**: Three-platform selection with Seedance 2.0 option

```html
<!-- Enhanced Platform Toggle -->
<div class="platform-toggle" id="platformToggle">
  <button class="active" id="ptKling" onclick="setVideoPlatform('kling')">Kling</button>
  <button id="ptHf" onclick="setVideoPlatform('higgsfield')">Higgsfield</button>
  <button id="ptSeedance" onclick="setVideoPlatform('seedance')">Seedance 2.0</button>
</div>

<!-- Platform-Specific Badges -->
<div class="h-badge seedance" id="badgeSeedance" style="display:none">
  <div class="h-badge-dot"></div>Seedance 2.0
</div>
```

#### 2. Seedance-Specific Input Panels

**A. Audio Upload Panel**
```html
<div class="exp-panel" id="panelAudioSync" style="max-width:860px;margin:0 auto;">
  <div class="exp-panel-title">Audio Synchronization</div>
  <div class="exp-panel-hint">Upload mastered track for beat-synchronized video generation</div>
  <div class="audio-upload-zone">
    <input type="file" id="audioFile" accept=".wav,.mp3,.m4a" style="display:none">
    <div class="audio-drop" id="audioZone" onclick="document.getElementById('audioFile').click()">
      <span class="audio-waveform" id="audioWaveform" style="display:none"></span>
      <span class="audio-drop-ph">+ Upload Audio Track</span>
    </div>
    <div class="audio-controls" id="audioControls" style="display:none">
      <button class="play-pause" id="playPause">▶</button>
      <div class="audio-timeline" id="audioTimeline"></div>
      <span class="audio-duration" id="audioDuration">0:00</span>
    </div>
  </div>
</div>
```

**B. 6-Step Prompt Builder**
```html
<div class="exp-panel" id="panelSeedancePrompt" style="max-width:860px;margin:0 auto;">
  <div class="exp-panel-title">6-Step Prompt Formula</div>
  <div class="prompt-steps">
    <div class="prompt-step">
      <label>1. Subject</label>
      <input type="text" id="promptSubject" placeholder="Who/what (one primary subject)">
    </div>
    <div class="prompt-step">
      <label>2. Action</label>
      <input type="text" id="promptAction" placeholder="Movement, behavior">
    </div>
    <div class="prompt-step">
      <label>3. Environment</label>
      <input type="text" id="promptEnvironment" placeholder="Setting, atmosphere">
    </div>
    <div class="prompt-step">
      <label>4. Camera</label>
      <select id="promptCamera">
        <option>Orbit</option>
        <option>Aerial/Crane</option>
        <option>Zoom</option>
        <option>Pan</option>
        <option>Tilt</option>
        <option>Follow/Track</option>
        <option>Handheld</option>
        <option>Gimbal</option>
      </select>
    </div>
    <div class="prompt-step">
      <label>5. Style</label>
      <input type="text" id="promptStyle" placeholder="Lighting, mood, film look">
    </div>
    <div class="prompt-step">
      <label>6. Constraints</label>
      <input type="text" id="promptConstraints" placeholder="What to preserve/avoid">
    </div>
  </div>
</div>
```

**C. Timeline Prompting Interface**
```html
<div class="exp-panel" id="panelTimeline" style="max-width:860px;margin:0 auto;">
  <div class="exp-panel-title">Timeline Prompting (Multi-Shot)</div>
  <div class="timeline-builder">
    <div class="timeline-segment" data-start="0" data-end="4">
      <div class="segment-time">[0:00-0:04]</div>
      <textarea class="segment-prompt" placeholder="Camera position + action + atmospheric detail"></textarea>
    </div>
    <div class="timeline-segment" data-start="4" data-end="8">
      <div class="segment-time">[0:04-0:08]</div>
      <textarea class="segment-prompt" placeholder="Camera position + action + atmospheric detail"></textarea>
    </div>
    <button class="add-segment" onclick="addTimelineSegment()">+ Add Segment</button>
  </div>
</div>
```

**D. Reference Image Management**
```html
<div class="exp-panel" id="panelReferences" style="max-width:860px;margin:0 auto;">
  <div class="exp-panel-title">Reference Images (@tag system)</div>
  <div class="reference-grid">
    <div class="ref-slot" data-tag="image1">
      <div class="ref-label">@image1</div>
      <div class="ref-drop" onclick="uploadReference('image1')">
        <img id="refPreview1" src="" alt="" style="display:none">
        <span class="ref-drop-ph">+ Character Face</span>
      </div>
    </div>
    <div class="ref-slot" data-tag="image2">
      <div class="ref-label">@image2</div>
      <div class="ref-drop" onclick="uploadReference('image2')">
        <img id="refPreview2" src="" alt="" style="display:none">
        <span class="ref-drop-ph">+ Wardrobe</span>
      </div>
    </div>
    <div class="ref-slot" data-tag="image3">
      <div class="ref-label">@image3</div>
      <div class="ref-drop" onclick="uploadReference('image3')">
        <img id="refPreview3" src="" alt="" style="display:none">
        <span class="ref-drop-ph">+ Environment</span>
      </div>
    </div>
  </div>
</div>
```

### Backend API Enhancements

#### 1. Seedance 2.0 Integration Module
```javascript
// agents/seedance-integration.js
const SEEDANCE_SYSTEM_PROMPT = `You are a Seedance 2.0 prompt engineering specialist. 
Convert user inputs into optimized Seedance 2.0 prompts using the 6-step formula:
Subject → Action → Environment → Camera → Style → Constraints

Key Requirements:
- 60-100 words total
- One camera instruction per shot
- Include lighting descriptions (highest impact on quality)
- Support reference image tagging (@image1, @image2, etc.)
- Timeline prompting for multi-shot sequences
- Audio synchronization considerations

Output valid JSON following the Seedance 2.0 API specification.`;

async function generateSeedancePrompt(userInput, audioFile, referenceImages) {
  const promptData = {
    sixStepFormula: userInput.sixStep,
    timelineSegments: userInput.timeline,
    referenceImages: referenceImages,
    audioFile: audioFile,
    aspectRatio: userInput.aspectRatio || "9:16", // Default to social vertical
    duration: userInput.duration || 15
  };

  return await callGeminiAgent(SEEDANCE_SYSTEM_PROMPT, promptData);
}
```

#### 2. Audio Processing Pipeline
```javascript
// agents/audio-processor.js
const ffmpeg = require('fluent-ffmpeg');

async function processAudioForSeedance(audioFile) {
  // Extract audio metadata
  const metadata = await extractAudioMetadata(audioFile);
  
  // Generate beat markers for synchronization
  const beatMap = await detectBeats(audioFile);
  
  // Prepare for Seedance 2.0 upload
  const processedAudio = await convertToSeedanceFormat(audioFile);
  
  return {
    metadata,
    beatMap,
    processedAudio,
    duration: metadata.duration,
    bpm: beatMap.averageBpm
  };
}
```

#### 3. Prompt Template Integration
```javascript
// agents/prompt-templates.js
const VAWN_SEEDANCE_TEMPLATES = {
  performanceCore: {
    16: `@VawnRef stands in an abandoned warehouse, wearing (@VawnOutfit1), 
         delivering bars with controlled intensity and precise hand gestures.
         He maintains steady eye contact with camera while rapping, 
         subtle head movement matching the rhythm.
         Industrial warehouse space with exposed brick walls, hanging tungsten work lights.
         Slow dolly push-in from medium shot to close-medium, camera height at eye level.
         Warm tungsten key light from camera left, cool blue rim light from behind.
         Smooth camera motion, preserve composition and colors, no jitter.`,
    
    9: `@VawnRef in tight medium shot, wearing (@VawnOutfit2), 
        delivering verse directly to camera with authentic energy.
        Natural hand gestures matching lyrical flow, maintaining connection with lens.
        Urban rooftop at golden hour, Atlanta skyline blurred in background.
        Static framing, locked off at shoulder height, no camera movement.
        Golden hour natural light as key, soft fill from reflector.
        Vertical composition, text-safe areas preserved, no motion blur.`
  }
};
```

---

## Feature Implementation Roadmap

### Phase 1: Core Integration (Weeks 1-2)

#### Week 1: Backend Foundation
- [ ] **API Integration**: Seedance 2.0 API client implementation
- [ ] **Audio Processing**: FFmpeg integration for audio upload/processing
- [ ] **Prompt Engineering**: 6-step formula backend logic
- [ ] **Reference Management**: Image upload and @tag system backend

#### Week 2: Frontend Core
- [ ] **UI Components**: Seedance-specific input panels
- [ ] **Platform Toggle**: Enhanced three-platform selection
- [ ] **Audio Interface**: Upload, playback, and timeline visualization
- [ ] **Prompt Builder**: 6-step structured input interface

### Phase 2: Advanced Features (Weeks 3-4)

#### Week 3: Timeline & Templates
- [ ] **Timeline Prompting**: Multi-shot sequence interface
- [ ] **Template Library**: Vawn-specific prompt templates integration
- [ ] **Character Integration**: SoulCast character asset compatibility
- [ ] **Quality Controls**: Validation and preview systems

#### Week 4: Integration & Testing
- [ ] **Workflow Integration**: End-to-end generation testing
- [ ] **Access Strategy**: Authorized cloud platform integration
- [ ] **Performance Optimization**: Batch generation and caching
- [ ] **User Experience**: Polish and refinement

### Phase 3: Production Ready (Weeks 5-6)

#### Week 5: Production Features
- [ ] **Asset Management**: Generated content organization
- [ ] **Export Systems**: Multiple format output support
- [ ] **Quality Assurance**: Automated validation and checks
- [ ] **Documentation**: User guides and workflows

#### Week 6: Launch & Optimization
- [ ] **Team Training**: Production team onboarding
- [ ] **Performance Monitoring**: Usage analytics and optimization
- [ ] **Feedback Integration**: User feedback and iteration
- [ ] **Workflow Documentation**: Complete integration guides

---

## Access Strategy Implementation

### Authorized Cloud Platform Integration

#### Option 1: Third-Party Platform Integration
```javascript
// config/seedance-access.js
const SEEDANCE_CONFIG = {
  // Based on research findings
  platforms: {
    topviewAI: {
      baseUrl: "https://api.topview.ai/v1/seedance",
      features: ["unlimited_generations", "agent_workflow"],
      costModel: "subscription" // Annual business plan
    },
    chatcutIO: {
      baseUrl: "https://api.chatcut.io/seedance",
      features: ["discord_invite", "community_access"],
      costModel: "credits"
    }
  },
  fallbacks: ["topviewAI", "chatcutIO"]
};
```

#### Option 2: Direct API Integration (when available)
```javascript
// Future-ready for direct ByteDance API access
const SEEDANCE_DIRECT = {
  baseUrl: "https://api.volcengine.com/seedance/v2",
  authentication: "business_verification",
  costModel: "$0.10_per_minute",
  regions: ["hong_kong", "singapore"] // US availability pending
};
```

---

## Data Flow Architecture

### Enhanced Generation Pipeline

#### 1. Input Processing Flow
```
User Input → Audio Upload → Reference Images → 6-Step Formula → 
Timeline Segments → Template Selection → Prompt Generation → 
Platform Routing → Generation Request → Result Processing
```

#### 2. Platform Decision Logic
```javascript
function determineOptimalPlatform(userInput, audioRequirements, characterNeeds) {
  if (audioRequirements.lipSync || audioRequirements.beatSync) {
    return 'seedance'; // Audio-visual sync required
  }
  
  if (characterNeeds.consistency && characterNeeds.soulcast) {
    return 'higgsfield'; // Character consistency priority
  }
  
  if (userInput.duration > 15) {
    return 'kling'; // Longer duration support
  }
  
  return 'seedance'; // Default for Vawn content (audio focus)
}
```

#### 3. Multi-Platform Workflow
```javascript
async function generateMultiPlatform(prompt, audio, references) {
  const platforms = ['seedance', 'kling', 'higgsfield'];
  const results = {};
  
  for (const platform of platforms) {
    try {
      const optimizedPrompt = optimizeForPlatform(prompt, platform);
      results[platform] = await generateVideo(optimizedPrompt, platform);
    } catch (error) {
      console.log(`${platform} generation failed, continuing...`);
    }
  }
  
  return results;
}
```

---

## Quality Assurance Framework

### Seedance 2.0 Specific Validations

#### 1. Audio Sync Validation
```javascript
function validateAudioSync(generatedVideo, originalAudio) {
  const syncCheck = {
    lipSyncAccuracy: measureLipSyncAccuracy(generatedVideo, originalAudio),
    beatAlignment: measureBeatAlignment(generatedVideo, originalAudio),
    audioQuality: analyzeAudioQuality(generatedVideo),
    durationMatch: compareDurations(generatedVideo, originalAudio)
  };
  
  return syncCheck.lipSyncAccuracy > 0.85 && syncCheck.beatAlignment > 0.90;
}
```

#### 2. Character Consistency Validation
```javascript
function validateCharacterConsistency(videoFrames, referenceImages) {
  const consistencyScore = computeFacialSimilarity(videoFrames, referenceImages);
  const outfitConsistency = validateOutfitConsistency(videoFrames);
  
  return {
    faceConsistency: consistencyScore > 0.95,
    outfitConsistency: outfitConsistency > 0.90,
    overallScore: (consistencyScore + outfitConsistency) / 2
  };
}
```

#### 3. Prompt Quality Metrics
```javascript
function validatePromptQuality(prompt) {
  const checks = {
    wordCount: prompt.split(' ').length >= 60 && prompt.split(' ').length <= 100,
    hasLighting: /\b(light|lighting|glow|shadow|illuminat)\b/i.test(prompt),
    hasCameraMovement: /\b(orbit|dolly|pan|tilt|track|zoom|crane)\b/i.test(prompt),
    hasConstraints: prompt.includes('smooth') || prompt.includes('no jitter'),
    hasSubjectDetail: !prompt.includes('the man') && !prompt.includes('the figure')
  };
  
  return Object.values(checks).filter(Boolean).length >= 4;
}
```

---

## Performance & Scalability

### Optimization Strategies

#### 1. Generation Optimization
- **Batch Processing**: Multiple shots generated simultaneously
- **Template Caching**: Pre-generated prompt templates for common scenarios
- **Preview Generation**: Low-resolution previews before full generation
- **Failed Generation Recovery**: Automatic retry with prompt variations

#### 2. Asset Management
- **Generated Content Storage**: Organized by project, date, and platform
- **Reference Image Library**: Vawn character assets readily available
- **Template Versioning**: Track and update prompt templates
- **Usage Analytics**: Monitor platform performance and user preferences

#### 3. Cost Management
- **Credit Monitoring**: Track usage across platforms
- **Platform Optimization**: Route requests to most cost-effective platform
- **Batch Discounts**: Leverage volume pricing when available
- **Quality vs. Cost**: Balance generation quality with budget constraints

---

## Integration Testing Strategy

### Testing Phases

#### 1. Unit Testing
- [ ] Audio processing pipeline
- [ ] 6-step prompt formula validation
- [ ] Reference image tagging system
- [ ] Timeline prompting logic

#### 2. Integration Testing
- [ ] Platform routing and failover
- [ ] Multi-platform generation comparison
- [ ] Character consistency across platforms
- [ ] Audio sync accuracy validation

#### 3. User Acceptance Testing
- [ ] Complete workflow with Vawn content
- [ ] Production team usability testing
- [ ] Performance benchmarking
- [ ] Quality validation with creative director

#### 4. Production Testing
- [ ] Load testing with multiple simultaneous generations
- [ ] Error handling and recovery
- [ ] Platform availability and failover
- [ ] Cost efficiency validation

---

## Success Metrics & KPIs

### Technical Performance
- **Generation Success Rate**: >85% usable outputs on first attempt
- **Audio Sync Accuracy**: >90% lip-sync and beat alignment
- **Character Consistency**: >95% visual consistency score
- **Platform Uptime**: >95% availability across integrated platforms

### User Experience
- **Workflow Completion Time**: <15 minutes from concept to generated content
- **User Adoption Rate**: >90% production team adoption within 30 days
- **Quality Approval Rate**: >80% generated content approved by creative director
- **Error Recovery Time**: <2 minutes for failed generation recovery

### Business Impact
- **Cost Reduction**: 70-80% reduction in video production costs vs. traditional methods
- **Production Velocity**: 5x increase in video content generation speed
- **Content Quality**: Maintain or exceed current video quality standards
- **Creative Flexibility**: Enable experimentation with multiple visual styles

---

## Risk Mitigation & Contingency Plans

### Technical Risks

#### 1. Platform Access Issues
- **Risk**: Seedance 2.0 access restrictions or API changes
- **Mitigation**: Multi-platform fallback system, multiple access providers
- **Contingency**: Prioritize Higgsfield/Kling for immediate production needs

#### 2. Audio Sync Quality Issues
- **Risk**: Poor lip-sync or beat alignment affecting usability
- **Mitigation**: Quality validation gates, manual adjustment tools
- **Contingency**: Fallback to Higgsfield with manual audio overlay

#### 3. Character Consistency Degradation
- **Risk**: Character drift across multi-shot sequences
- **Mitigation**: Reference image anchoring, validation checkpoints
- **Contingency**: Manual character correction tools, template refinement

### Business Risks

#### 1. Cost Escalation
- **Risk**: Credit usage exceeding budget projections
- **Mitigation**: Usage monitoring, platform cost optimization
- **Contingency**: Implement generation quotas, prioritize high-value content

#### 2. Creative Quality Issues
- **Risk**: AI-generated content not meeting creative standards
- **Mitigation**: Quality gates, creative director approval process
- **Contingency**: Hybrid workflow with manual enhancement

---

## Documentation & Training Plan

### Technical Documentation
- [ ] **API Integration Guide**: Seedance 2.0 API implementation details
- [ ] **Prompt Engineering Manual**: 6-step formula best practices
- [ ] **Character Consistency Guide**: SoulCast integration procedures
- [ ] **Quality Assurance Checklist**: Validation and testing protocols

### User Documentation
- [ ] **Workflow Guide**: Step-by-step usage instructions
- [ ] **Template Library**: Available prompt templates and usage
- [ ] **Troubleshooting Guide**: Common issues and solutions
- [ ] **Best Practices**: Tips for optimal results

### Training Materials
- [ ] **Production Team Onboarding**: Complete workflow training
- [ ] **Creative Director Briefing**: Quality standards and approval process
- [ ] **Technical Team Training**: Maintenance and troubleshooting
- [ ] **Video Tutorials**: Screen-recorded workflow demonstrations

---

## Next Steps for Implementation

### Immediate Actions (This Week)
1. **Access Strategy Execution**: Research and secure authorized Seedance 2.0 access
2. **Development Environment Setup**: Prepare development instance of Apulu Prompt Generator
3. **Team Coordination**: Brief Rex (CTO) and development team on integration plan
4. **Requirements Validation**: Review integration requirements with Clu and Lens

### Implementation Timeline
- **Week 1-2**: Core integration and backend foundation
- **Week 3-4**: Advanced features and frontend development
- **Week 5-6**: Testing, polish, and production deployment
- **Week 7**: Team training and workflow documentation
- **Week 8**: Performance monitoring and optimization

### Success Dependencies
- Successful Seedance 2.0 access via authorized cloud platforms
- Development team availability and technical expertise
- Quality validation and approval from creative director
- Production team adoption and workflow integration

---

## Conclusion

This integration roadmap provides a comprehensive path for enhancing the Apulu Prompt Generator with Seedance 2.0 capabilities while maintaining the existing workflow quality and efficiency. The additive approach ensures that current Higgsfield and Kling workflows continue to function while providing new capabilities specifically optimized for Vawn's music video production needs.

The focus on audio-visual synchronization, structured prompt engineering, and character consistency aligns perfectly with Vawn's content requirements and will significantly enhance the creative team's ability to produce high-quality, AI-generated music video content.

---

## Sources & Research Foundation

Built upon:
- [[Research Pipeline — Seedance 2.0 availability API access]] (access strategy research)
- [[Seedance 2.0 — Prompt Engineering Guide]] (APU-10 technical foundation)
- [[Vawn Multi-Shot Prompt Templates]] (implementation templates)
- [[Vawn SoulCast 3.0 Character Strategy]] (character consistency strategy)
- Current Apulu Prompt Generator architecture analysis

---

## Core Rules — In Order of Impact

### Structure

- **Who, where, doing what, what changes, mood** — in that order.
- **≤4 story beats per generation.**
- **≤3 characters per shot, ≤5 named total.**
- **Duration must match complexity** — Seedance stretches the same content slower for longer clips, it doesn't add events.

### Language

- **Concrete visual description only** — what the camera sees.
- **No emotion labels** (`angry`, `afraid`) — describe the physical manifestation (`jaw clenches`, `hands press flat against the wall`).
- **No metaphors the lens can't render** (`the city breathes` → `steam rises from grates, traffic flows`).
- **No abstract quality words** (`breathtaking`, `haunting`) — ignored or produce generic output.

### Characters

- **Give each character a unique visual anchor on first mention** — wardrobe color, silhouette, accessory.
- **State positions and movement direction explicitly.**
- **Re-anchor positions after every cut** — Seedance has no memory between shots.

### Camera

- **One dominant camera move per shot** — compound instructions (`orbit while zooming while tilting`) confuse the engine.
- **No focal lengths above 75mm** — use shot size terms instead (choker, ECU).
- **No reflections** (mirrors, water, glass, blades) — duplicates characters unpredictably.
- **No U-turns or 180° vehicle spins** — split across two shots instead.

### What to Avoid Entirely

- `Strobing`, `step-printing`, `undercranking` — triggers global low shutter, unsalvageable.
- `Symmetrical` or `mirrored` — renders a literal mirror line down the frame.
- **Film titles** — trigger content filters. Use director names only.
- **Hidden objects** (`gun under the table`) — if the camera didn't see it, it doesn't exist.
- **Prismatic or Petzval effects** — produce artifacts, not the intended look.

### Audio

Sound is rendered. Include it — ambient, foley, dialogue delivery. **Music is post only.**

### Language of the Prompt

Always English, regardless of chat language. Dialogue defaults to English — other languages only on explicit request.

---

## Advanced Craft — Structure, Characters, Dialogue, Pacing, Presets

### Prompt Structure

- **Open with environment before character** — give Seedance a stage to place people onto.
- **End with sound** — audio cues at the end of the prompt anchor mood without competing with visual description.
- **Describe light direction and quality explicitly**, even when a preset is set — presets set the system, in-prompt description fine-tunes the shot.
- **Name what's NOT moving** as well as what is — `camera locked, only the smoke drifts` gives Seedance a contrast reference.

### Characters (Continuity & Contact)

- **Wardrobe is continuity glue** across clips — lock it on first appearance and never change it mid-sequence.
- **Physical state over emotional state** — `shirt torn at the collar, knuckles scraped` tells Seedance more than `he looks beaten`.
- If two characters are **interacting physically, describe the contact point explicitly** — `his hand grips her wrist, thumb over the pulse point`.

### Dialogue

- **Mark the power-shift line** — the moment one character gains or loses leverage. That's where Seedance needs to hold the tightest frame.
- **4–6 lines maximum at 15 seconds.**
- **Write delivery into the line** — `flat and quiet`, `through her teeth`, `almost to himself` — as physical vocal behavior, not emotion labels.

### Pacing

- **Front-load the action** — don't build to something if the duration is under 8 seconds. Start at the peak.
- **15-second clips = 3 beats minimum, 4 maximum.** Two beats at 15 seconds feels empty.
- **State what changes between the first and last frame** — if nothing changes, the clip has no arc.

### Multi-Clip Sequences

- **Last frame of clip N must be described at the top of clip N+1** — spatial re-anchor.
- **Emotional temperature moves in one direction per clip** — don't oscillate within a single generation.
- **Genre can shift between clips; visual identity (Session Lock) cannot.**

### Presets

- **DP Combo recipes are the safest starting point** — tested combinations with no internal conflicts.
- When building a custom combination, **check the conflict zones before generating** — incompatible axes waste a generation.
- **Null axes are valid** — if uncertain about a parameter, leave it null and let the engine decide rather than setting something that conflicts.

---

*Integration roadmap prepared by Pixel (AI Prompt Researcher) for APU-12. Ready for immediate development and implementation by Rex (CTO) and technical team.*