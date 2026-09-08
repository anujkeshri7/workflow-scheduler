---
name: "Instagram News Automation 2.0"
description: "Triggers the massive 15-point news workflow to research, score, generate JSON, render multi-template Instagram posts, convert to 9:16 Reels with music, and auto-publish/schedule via Meta Graph API."
---

# Instagram News Workflow Instructions

When the user says "run workflow" or asks for news on a specific topic, execute these steps exactly:

## 1. Research & Scoring
- Research the internet for 3 trending news stories (prioritize Criticism, Politics, Current Affairs, Film, Sports, Business).
- STRICT RULE: News must be extremely fresh (maximum 2-3 days old, preferably today's or yesterday's news).
- STRICT RULE: Check your memory and do NOT repeat any previous news stories that you have already covered.
- Verify sources (minimum 2 reliable sources).
- Score each story for Virality (1-10). Only pick stories scoring >= 7.

## 2. Visual & Collage Sourcing
- Look for REAL web images or generate custom high-quality AI images (`generate_image`).
- STRICT MULTI-LAYOUT / GRID RULE:
  - Generate context-specific layouts (e.g., 3-panel grid collage for political debates/controversy, 2-panel split for diplomacy/partnerships, full-bleed dramatic scenes for breaking legal/court news).
  - All AI-generated images must be in vertical 4:5 aspect ratio (`3:4`).
  - The main visual subjects must be placed strictly in the top 55-60% of the frame.
  - The bottom 40% must fade into a smooth dark gradient/solid dark background for clear typography overlay.
- STRICT QUOTA RULE: If `generate_image` hits quota limits (429 / RESOURCE_EXHAUSTED), immediately inform the user and stop.

## 3. Data Generation & Content Rules

### A. Post Image Rules (100% Self-Contained Context)
- **CRITICAL**: The post image alone MUST convey the full context and story to the viewer at first glance without needing to read the caption.
- **Headline**: 2 lines, UPPERCASE, strong, bold, punchy. (Use 'RS.' or '$' to ensure font compatibility).
- **Subheadline**: 2-3 lines of crystal-clear, informative facts covering Who, What, Why, and the primary outcome.
- **Highlighted Fact Box**: A crisp, high-impact key fact (e.g., date, amount, milestone, directive).
- **Template Selection**:
  - `controversy`: Grid 3-panel collage layout, yellow bold headline on dark panel, red pill.
  - `politics`: Split 2-panel layout, clean white headline on navy panel, gold accent bar.
  - `breaking`: Cinematic full-bleed scene, red/white dual-tone headline on dark gradient.
  - `film`: High-fashion / entertainment grid layout.
  - `sports`: Action split layout with energetic accents.

### B. Caption Strict Formatting Rules
Every caption MUST strictly follow this exact 4-part structure:

1. **Title (approx 100 characters)**:
   - Catchy, hook-driven with relevant emoji.
   - Example: `🤝 Global Diplomacy: New Delhi me India-Japan Maritime Security MoA hua sign! 🇮🇳🇯🇵`
2. **Detailed Description**:
   - Complete, in-depth breakdown of the news, including background, key quotes, numbers, and impact.
   - Includes a compelling Call to Action (CTA) / question at the end (e.g., `Is strategic move par aapki kya rai hai? Comment karein! 👇💬`).
3. **Source**:
   - Clickable HTML format link at the end: `Source: <a href="https://resolved-link.com">NDTV</a>`.
   - Always resolve via `python resolve_url.py <Grounding_Redirect_URL>`.
4. **Hashtags**:
   - **EXACTLY 5** best, highly relatable, trending lowercase hashtags.

### C. Language Preference
- If Hinglish is chosen:
  - Headline, subheadline, title, and description in conversational Hinglish (Latin script).
  - No Devanagari script (write "Dilli" or "Delhi", "aaj ki badi khabar").
  - Hashtags in English.
- If English is chosen:
  - Everything in clear, professional English.

## 4. JSON Export
- Overwrite `daily_news_data.json` matching this schema:
```json
{
  "posts": [
    {
      "template": "controversy",
      "category": "CATEGORY NAME",
      "image_path": "path_to_saved_image.jpg",
      "headline": "UPPERCASE TWO LINE\nSTRONG HEADLINE",
      "subheadline": "Self-contained 2-3 line summary giving 100% complete story context.",
      "highlighted_fact": "Aug 20, 2026 Milestone",
      "caption": "🔥 Political Row: CWC ke 2 Stanzas faisle par Amit Shah ne Congress ko anti-national kaha! 🇮🇳\n\nVande Mataram par naya bavaal shuru ho gaya hai. CWC ne 1937 precedent cite karte hue party functions me sirf pehle do stanzas gaane ka faisla kiya. Ispar Home Minister Amit Shah ne kadi aalochana karte hue ise appeasement politics karaar diya. Congress ne ise BJP ka political diversion bataya.\n\nKya aap puri Vande Mataram gaane ke paksh me hain? Comment karein! 👇💬\n\nSource: <a href=\"https://indiatoday.in/...\">India Today</a>\n\n#vandemataram #amitshah #congress #indianpolitics #breakingnews",
      "out_path": "C:\\Users\\anujk\\.gemini\\antigravity\\brain\\<conv-id>\\news1_final.png",
      "video_path": "C:\\Users\\anujk\\.gemini\\antigravity\\brain\\<conv-id>\\news1_reel.mp4"
    }
  ]
}
```

## 5. Rendering, Video Reel Generation & Delivery
1. **Render 1080x1350 Visuals**: Run `python overlay.py` to render the multi-template posts.
2. **Generate 9:16 Reels with Split Layout & Dual 100% Audio**:
   - Run `python video_generator.py` to produce 1080x1920 MP4 reels.
   - **Split Layout**:
     - Upper portion (0 to 1350 px): 1080x1350 crisp News Graphic Card (`news_final.png`).
     - Bottom portion (1350 to 1920 px): 1080x570 Reaction Video Clip (`clip.mp4`) trimmed starting from **1.0s** (`-ss 1.0`).
   - **Dual 100% Audio Mix**:
     - Reaction Clip Audio: **100% volume** (`volume=1.0`).
     - News Background Music: **100% volume** (`volume=1.0`) with smooth fade-in/out.
     - Mixed together via `amix=inputs=2:duration=first:dropout_transition=2`.
   - **Exclusive News Background Soundtracks**:
     - Exclusively rotate tracks from `/music/` folder: `Breaking News sound1.mp3`, `Breaking News sound2.mp3`, `Breaking News sound3.mp3`. Do not use any other background music.
3. **Telegram Delivery**: Run `python clear_batch_history.py; python telegram_sender.py` to deliver images, videos and formatted captions to Telegram.
4. **Queue for 9-Slot Cloud Scheduling**: Run `python queue_manager.py` to append the newly generated posts to `posts_queue.json` and sync with GitHub.
5. In chat, provide **Bollywood Music Recommendations** for each story.
