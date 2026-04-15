---
title: "Note Taking & Research Assistant Powered by AI"
source: "https://notebooklm.google.com/notebook/d029cbc8-9bfe-43f2-90a2-a24d5bf3f28c?authuser=1"
author:
published:
created: 2026-04-12
description: "Use the power of AI for quick summarization and note taking, NotebookLM is your powerful virtual research assistant rooted in information you can trust."
tags:
  - "clippings"
---
[![NotebookLM Logo](https://notebooklm.google.com/_/static/branding/v5/light_mode/icon.svg)](https://notebooklm.google.com/?authuser=1)

                                    

## Chat

🎬

## Higgsfield AI: Mastering Cinematic Storytelling and Community Creation

36 sources

These sources highlight the capabilities and technical workflows of **Higgsfield AI**, a platform designed for creating cinematic and hyper-realistic digital content. The text provides **extensive prompt engineering guides** that explain how to use structured language and "negative prompts" to eliminate visual glitches while maintaining anatomical accuracy. Various technical tutorials illustrate the "production chain" method, where users combine tools like **Higgsfield Popcorn** for storyboarding and **Seedance** for adding motion to static images. The collection also showcases a **searchable database of Nano Banana prompts**, offering pre-made templates for diverse categories such as product photography, 3D miniatures, and character design. Detailed examples emphasize the importance of **identity preservation** and authentic imperfections, such as skin pores and natural lighting, to achieve high-resolution realism. Collectively, these documents serve as a comprehensive manual for creators looking to master **next-generation AI video and image generation**.

How do I build a cinematic sequence using Higgsfield's workflow?

What are the best tips for mastering Higgsfield prompt engineering?

How do negative prompts help fix anatomy and realism issues?

Today • 5:42 PM

For highly controlled, professional generations in the 3.0 ecosystem (which utilizes the Nano Banana Pro architecture for precise visual reasoning), using a JSON structure forces the model to treat every token as a strict instruction with zero data loss.

Here is a representative JSON prompt structure based on the platform's advanced templates, which categorizes instructions into distinct hierarchical keys:

```
{
  "generation_request": {
    "reference_settings": {
      "identity_lock": true,
      "face_preservation": "100% identical to reference — same facial structure, proportions, skin texture, expression, and details"
    },
    "subject": {
      "demographics": "female, young adult",
      "expression": "confident, calm, focused",
      "pose_action": {
        "action": "hands raised mid-clap",
        "body_orientation": "three-quarter side profile",
        "gaze": "Looking toward the camera"
      }
    },
    "wardrobe": {
      "top": "yellow and navy sleeveless volleyball jersey",
      "bottom": {
        "type": "full-length black athletic pants",
        "fit": "sporty, fitted, opaque fabric"
      },
      "accessories": [
        "Small gold hoop earrings"
      ]
    },
    "scene": {
      "location": "indoor sports arena",
      "background_elements": [
        "blurred volleyball court with pink and white wall panels",
        "teammates visible in soft background blur"
      ]
    },
    "lighting": {
      "type": "bright indoor sports lighting",
      "quality": "Bright, even",
      "shadows": "soft",
      "effects": "Clean highlights on skin and clothing"
    },
    "camera": {
      "shot_type": "medium shot",
      "angle": "eye-level",
      "focus": "sharp focus on subject face and upper body",
      "depth_of_field": "shallow background blur"
    },
    "quality": {
      "realism": "photorealistic",
      "resolution": "8K ultra sharp",
      "detail_level": "high"
    },
    "constraints": {
      "no_face_modification": true,
      "legs_must_be_covered": "black pants required",
      "negative_prompt": [
        "extra people",
        "face blending",
        "beautify filter",
        "plastic skin",
        "cartoon",
        "cgi look",
        "blurry faces"
      ]
    }
  }
}
```

**Key Components of the 3.0 JSON Structure:**

- **reference\_settings** **(Identity Lock):** This is critical for character consistency. By setting variables like `"identity_lock": true` and defining exact accuracy, you instruct the reasoning engine to prioritize the uploaded reference image's facial geometry and skin texture above all else, ensuring zero deviation or "morphing".- **subject** **&** **pose\_action****:** Instead of writing a messy paragraph about what the character is doing, you explicitly define demographic details, posture, gaze, and specific hand actions into nested keys.- **scene** **&** **lighting****:** You establish the environment and define specific optical behaviors, such as "bright indoor sports lighting" and "clean highlights," which the engine applies mathematically to the generated 3D space.- **camera** **&** **quality****:** This block controls the virtual optical stack. By specifying the shot type, angle, focal depth, and requesting "8K ultra sharp" resolution, you bypass the default AI aesthetic and force cinematic realism.- **constraints** **/** **negative\_prompt****:** Positioned at the end, these define the exact boundaries of failure. By passing strict Boolean rules (e.g., `"no_face_modification": true`) alongside an array of negative keywords, you actively filter out unwanted artifacts, extra limbs, and stylistic clichés.

What are some visual style tags for a music video?

Show me a JSON structure for a gritty 16mm scene

How do I use @mentions to keep characters consistent?

A hierarchical JSON prompt structure leverages Nano Banana Pro's reasoning core to parse complex instructions as strict parameters rather than loose suggestions. By categorizing variables into distinct keys, the model can simultaneously manage character identities, dynamic poses, environmental cohesion, and virtual camera optics without data loss.

Here is a professional-grade example of a hierarchical JSON prompt structure for a cinematic shot:

```
{
  "type": "image_generation_prompt",
  "style": "hyper-realistic, cinematic motorsport photography",
  "identity_preservation": {
    "use_reference_image": true,
    "strict_identity_lock": true,
    "alter_face": false,
    "notes": "Use the uploaded photo as a strict reference. Preserve 100% of the woman's facial features, proportions, skin texture, hairstyle, and expression with no alterations."
  },
  "subject": {
    "gender": "female",
    "pose": {
      "stance": "standing confidently on the race grid",
      "posture": "upright, professional, composed",
      "hands": "holding a Ferrari F1 helmet in one hand"
    },
    "expression": "focused, confident, calm",
    "appearance": {
      "wardrobe": {
        "outfit": "official Ferrari Formula 1 driver racing suit (female fit), red with sponsor details"
      },
      "accessories": [
        "Ferrari F1 helmet held at the side"
      ]
    }
  },
  "environment": {
    "location": "Formula 1 race grid",
    "elements": [
      "Ferrari Formula 1 car positioned beside the subject",
      "asphalt track markings",
      "pit lane and grid details",
      "subtle background crew and equipment (softly blurred)"
    ]
  },
  "lighting": {
    "type": "natural daylight",
    "quality": "bright and cinematic",
    "effects": [
      "realistic highlights on racing suit and helmet",
      "natural shadows on the ground",
      "reflections on the Ferrari car body"
    ]
  },
  "camera": {
    "framing": "full-body shot",
    "angle": "eye-level to slightly low angle",
    "lens_look": "85mm motorsport editorial style",
    "depth_of_field": "moderate, subject in sharp focus with softly blurred background"
  },
  "color_grading": {
    "palette": [
      "Ferrari red",
      "black",
      "white",
      "metallic highlights"
    ],
    "contrast": "balanced and dynamic"
  },
  "constraints": [
    "Do not alter the face in any way",
    "No distortion of body proportions",
    "No logos misspellings or unrealistic sponsor details",
    "No cartoon or illustration style"
  ]
}
```

**Key Hierarchical Components:**

- **identity\_preservation** **/** **reference\_settings****:** This block instructs the engine to strictly lock onto an uploaded reference image, ensuring the character's facial structure and proportions remain 100% identical without any unwanted beautification or morphing.- **subject****:** Instead of writing a messy paragraph, you nest specific demographics, physical postures, expressions, and wardrobe details. This ensures the model perfectly styles the character before placing them in the scene.- **environment** **&** **lighting****:** These keys explicitly define the 3D space. You map out the background elements, architectural details, and light source behaviors (like "natural daylight" and "reflections on the Ferrari car body") to establish physical realism.- **camera****:** This acts as your virtual optical stack. By defining the framing, camera angle, specific focal length (e.g., "85mm"), and depth of field, you force the AI to adhere to professional photography rules.- **constraints** **/** **negative\_prompt****:** Positioned at the end, these arrays define your "boundaries of failure." By explicitly listing what the model must avoid (such as "cartoon," "distortion," or "misspellings"), you filter out typical AI artifacts and unwanted styles.

What are the specific subject and action keys for JSON?

Can you give me a JSON prompt for a product?

How do I add lighting constraints into a JSON prompt?

Google apps

Google Account

Ricardo Dyall

r.dyall1914@gmail.com

<iframe src="chrome-extension://cnjifjpddelmedmihgijeibhnjfabmlf/side-panel.html?context=iframe"></iframe>