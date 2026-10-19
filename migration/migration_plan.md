# Nanhe Seekho Club — Content Migration Strategy & Catalog Audit

## 1. Executive Summary

As part of the setup for **Nanhe Seekho Club (नन्हे सीखो क्लब)**, a complete audit of all local video assets on the laptop (`C:\kids_automation`) was conducted.

- **Total Local Videos Audited:** 151 video files (.mp4)
- **Already Uploaded to Fun Learning Kids:** 114 videos (Verified by YouTube Video ID, filename, and SHA-256 hash)
- **Local Unuploaded Renders:** 36 videos (26 Educational, 10 Cartoon)
- **Defective / Empty Videos:** 1 video (0 bytes / header failure)

Detailed catalog data is persisted in:
`C:\kids_automation\migration\local_video_catalog.json`

---

## 2. Core Migration Principles (Strict Compliance)

1. **Absolute Protection of Legacy Channel:**
   - The existing channel **Fun Learning Kids** (`UCcOA6heUaTbOUnx7ERF23Gw`) must remain completely undisturbed.
   - Code enforces a hard block (`ALLOW_LEGACY_CHANNEL_UPLOADS = False`) preventing any upload or modification targeting the legacy channel ID.

2. **No Bulk Uploads / Dump:**
   - Under no circumstances will videos be bulk-uploaded. YouTube algorithms penalize sudden batch uploads of backlog content as spam.
   - Content will follow the sustainable schedule:
     - **1 Short per day** (09:00 IST)
     - **2 Long videos per week** (Wednesday 17:00 IST & Sunday 17:00 IST)

3. **Rebranding Before Upload Requirement:**
   - **Cartoon Videos:** The 10 unuploaded cartoon renders contain hardcoded spoken outro audio mentioning *"फन लर्निंग किड्स"* in Scene 6. They **CANNOT** be uploaded directly. They must be re-rendered through `cartoon_daily_runner.py` with the updated outro:
     *"रोज कुछ नया सीखिए और नन्हे सीखो क्लब के साथ हमेशा मुस्कुराते रहिए!"*
   - **Educational Videos:** The 26 unuploaded educational videos have clean educational Hindi voice narration without any channel name spoken. However, metadata (title, description, tags, and thumbnail watermark) must carry the **Nanhe Seekho Club** branding.
   - **Duplicate Detection Safeguard:** `uploader.py` inspects SHA-256 hashes against both legacy and new upload histories to block raw re-uploads of old-channel videos.

---

## 3. Catalog Breakdown

### A. Uploaded to Legacy Channel (114 Videos)
- Status: `uploaded_to_fun_learning_kids`
- Policy: **Archived / Read-Only**. Kept locally on disk for backup and reference. Never re-uploaded.

### B. Unuploaded Educational Videos (26 Videos)
- Status: `local_unuploaded`
- Format: Mostly landscape 1280×720 (16:9), plus 5 vertical shorts (9:16).
- Policy: Can be scheduled on long-video days (Sundays) or converted to Shorts, provided they are packaged with Nanhe Seekho Club metadata and thumbnail.

### C. Unuploaded Cartoon Videos (10 Videos)
- Status: `local_unuploaded`
- Policy: Must be re-rendered with new outro audio. The story IDs will automatically alternate through `VarietyManager` and produce fresh, high-CTR episodes with the new watermark and outro.

### D. Corrupted Video (1 Video)
- `video/moral_story_2026-09-09_182046.mp4` (0 bytes).
- Policy: Quarantined / Ignored.

---

## 4. Cadence & Release Schedule

| Day | Time (IST) | Slot | Format | Content Pillar |
|---|---|---|---|---|
| **Everyday (Mon–Sun)** | 09:00 AM | `morning` / `shorts` | Vertical Shorts (1080×1920) | Fun Facts, Quick Habits, Animals, Alphabet |
| **Wednesday** | 05:00 PM | `cartoon` | Landscape 16:9 (1280×720) | Animated Cartoon Adventure (Alternating V1/V4) |
| **Sunday** | 05:00 PM | `evening` | Landscape 16:9 (1280×720) | Moral Story / Educational Deep Dive |
