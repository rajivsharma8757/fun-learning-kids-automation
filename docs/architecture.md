# System Architecture

## Fun Learning Kids — Automated YouTube Content Generation & Publishing System

This document provides a detailed architectural specification of the **Fun Learning Kids** automation platform. The platform is designed as an autonomous, dual-track content production pipeline capable of generating, rendering, and publishing educational and cartoon media to YouTube daily without human intervention.

---

## 1. High-Level Architecture

```mermaid
graph TD
    subgraph Scheduler & Orchestration
        SCHED[Windows Task Scheduler / OnLogon Trigger] --> RUNNER[run.py / run_automation.bat]
        RUNNER --> NET_CHK{Internet Available?}
        NET_CHK -- No --> NOTIF_WARN[Desktop Notification / Abort]
        NET_CHK -- Yes --> DM[daily_manager.py]
    end

    subgraph Dual-Track Production Orchestration
        DM --> CHECK_STATE{Check Completed Slots Today}
        CHECK_STATE -->|Slot 1: Morning| NORMAL_PIPE_1[Normal Video Pipeline]
        CHECK_STATE -->|Slot 2: Evening| NORMAL_PIPE_2[Normal Video Pipeline]
        CHECK_STATE -->|Slot 3: Cartoon| CARTOON_PIPE[Cartoon Animation Pipeline]
    end

    subgraph Normal Video Pipeline
        NORMAL_PIPE_1 & NORMAL_PIPE_2 --> CM[content_manager.py]
        CM --> SCRIPT[scripts_bank.json Deduplication]
        CM --> TTS_NORM[voice_generator.py Edge-TTS hi-IN-SwaraNeural]
        CM --> IMG_MGR[image_generator.py Asset Reuse & Generation]
        TTS_NORM & IMG_MGR --> VM[video_maker.py FFmpeg Compositor]
        VM --> TM[thumbnail_maker.py High-CTR Devanagari Thumbnail]
        TM --> UPLOADER_1[uploader.py Headless OAuth 2.0]
    end

    subgraph Cartoon Animation Pipeline
        CARTOON_PIPE --> SE[cartoon/story_engine.py]
        SE --> VMGR[cartoon/variety_manager.py]
        VMGR --> STYLE_SEL{1:1 Alternation Engine}
        STYLE_SEL -->|V1 Engine| RIG_V1[character_rig.py 2D Kinematic Vector Rig]
        STYLE_SEL -->|V4 Engine| RIG_V4[character_rig_v4.py 1080p Parallax Rig]
        RIG_V1 --> SR_V1[scene_renderer.py Multi-Background Renderer]
        RIG_V4 --> SR_V4[scene_renderer_v4.py Multi-Plane Parallax Renderer]
        SR_V1 & SR_V4 --> AUDIO_MIX[cartoon_daily_runner.py Multi-Track TTS & Audio Mix]
        AUDIO_MIX --> QA_GATE[quality_gate_v4.py Technical & Visual QA Inspection]
        QA_GATE --> UPLOADER_2[uploader.py Headless OAuth 2.0]
    end

    subgraph YouTube Publishing & Persistence
        UPLOADER_1 & UPLOADER_2 --> AUTH{token.json Valid?}
        AUTH -- Refresh Needed --> REFRESH[Google OAuth 2.0 Token Refresh]
        AUTH -- Valid --> YT_API[YouTube Data API v3]
        YT_API --> REC_UPL[history/uploads.json & cartoon_history.json]
        REC_UPL --> NOTIF_OK[notifier.py Windows Toast Notification]
    end
```

---

## 2. Dual-Track Architecture

The platform operates two isolated production tracks:

| Characteristic | Track A: Normal Educational Videos | Track B: Original Cartoon Episodes |
| :--- | :--- | :--- |
| **Daily Target** | 2 Videos (Morning Slot at 09:00, Evening Slot at 21:30) | 1 Video (Independent Cartoon Slot) |
| **Content Type** | Educational Stories (Moral stories, Animal facts, Good habits, ABCs, Numbers) | 6-Scene Narrative Character Cartoons |
| **Voice Engine** | Edge-TTS (`hi-IN-SwaraNeural`), Single narration stream | Multi-scene character & narrator dialogue, micro-fades, peak normalization (-1.0 dBFS) |
| **Visual Style** | Ken-Burns motion across curated high-res illustrations | Vector Kinematics (V1) or 1080p Multi-Plane Parallax with Contact Shadows (V4) |
| **Subtitle System** | Hardburned yellow subtitles with black border via FFmpeg filter | Synchronized English & Hindi subtitles with safe bottom-margin positioning |
| **Failure Isolation** | Isolated in `daily_manager.py` | Wrapped in self-contained `try/except` blocks; cartoon errors never halt educational videos |

---

## 3. Cartoon Animation Engines

The cartoon subsystem incorporates two distinct animation engines governed by a persistent **Strict 1:1 Alternation** controller:

### 3.1 Version 1 Engine (Kinematic Vector Animation)
- **Character Rigging (`character_rig.py`)**: Hierarchical skeletal kinematics for animal characters (*Chintu Bunny*, *Golu Bear*, *Koko Squirrel*, *Bholu Puppy*, *Leo Lion Cub*). Dynamic ear sways, limb rotation, and facial visemes.
- **Scene Renderer (`scene_renderer.py`)**: Dynamic viewport panning and zooming across vector backgrounds (`forest_meadow`, `sunny_farm`, `treehouse_canopy`, `pond_park`).
- **Compositing**: Direct rawvideo pipe into FFmpeg for rapid rendering at 25-30 FPS.

### 3.2 Version 4 Engine (1080p Multi-Plane Parallax)
- **Production Polish Rigging (`character_rig_v4.py`)**:
  - **Dynamic Gaze Tracking**: Active pupil look-at coordinates tracking interactive props and camera.
  - **Physical Contact Shadows**: Radial gradient Gaussian-blurred contact shadows dynamically scaling with character ground distance.
  - **Acting Sequences**: Anticipation crouching, squash & stretch volume preservation, and natural trotting deceleration.
- **Scene Renderer (`scene_renderer_v4.py`)**: Multi-plane parallax camera moving through Far, Midground, and Foreground layers (`cozy_playroom`, `science_lab`, `starry_space`).
- **Quality Gate (`quality_gate_v4.py`)**: Dual automated QA inspecting 22 technical checkpoints (resolution, audio rate, bitrates, duration) and 7 visual composition checkpoints.

---

## 4. Variety Manager & Anti-Repetition Engine

To prevent character, location, or thematic monotony, [`cartoon/variety_manager.py`](../cartoon/variety_manager.py) enforces 6 deterministic rules:

1. **Strict 1:1 Alternation**: Day 1 = V1, Day 2 = V4, Day 3 = V1, Day 4 = V4, maintaining 50/50 equal priority.
2. **Persistence Grounding**: Style rotation is determined strictly by the last confirmed YouTube upload record (`status == "uploaded"` with valid `video_id`). Rebooting or running in `--dry-run` mode never corrupts rotation state.
3. **No Consecutive Characters**: Yesterday's main character cannot be selected today.
4. **Mimi Cooldown**: Characters with heavy historical presence (e.g. Mimi) must observe a mandatory **3-4 episode gap** before reappearing.
5. **No Consecutive Backgrounds or Locations**: Environments alternate continuously (e.g., Treehouse $\to$ Lab $\to$ Farm $\to$ Space).
6. **Unique SHA-256 Video Hashes**: Every generated video is cryptographically hashed to verify uniqueness against historical outputs before upload.

---

## 5. Headless Authentication & Upload Security

```mermaid
sequenceDiagram
    participant App as uploader.py
    participant Disk as token.json
    participant Google as Google OAuth 2.0
    participant YouTube as YouTube Data API v3

    App->>Disk: Read token.json
    alt Token Valid
        Disk-->>App: Return valid Credentials
    else Token Expired with Refresh Token
        App->>Google: POST /token (grant_type=refresh_token)
        Google-->>App: New Access Token
        App->>Disk: Write updated token.json
    else No Token Found
        Note over App,Google: Initial setup only: python auth_setup.py (Interactive Browser)
    end
    App->>YouTube: videos().insert(part="snippet,status", uploadType="resumable")
    YouTube-->>App: 200 OK (video_id)
    App->>YouTube: thumbnails().set(videoId, media_body)
    YouTube-->>App: 200 OK (thumbnail updated)
```

- **Headless Execution**: The system runs unattended under Windows Task Scheduler using a persistent refresh token stored in `token.json`. No browser popups or user interactions occur during production runs.
- **COPPA Compliance**: All uploads programmatically specify `selfDeclaredMadeForKids=True` in YouTube metadata.
- **Category Enforcement**: Automatically categorizes videos under Category `27` (Education).
