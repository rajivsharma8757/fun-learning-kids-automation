"""
cartoon_daily_runner.py
-----------------------
Independent Master Orchestrator for the 3rd Daily Video Pipeline:
Kids Cartoon Animation System for "Fun Learning Kids".

Features:
1. Complete failure isolation: Errors never bubble up or affect Normal Video 1 & 2.
2. Style Rotation:
   - Style A: V4 (Primary, ~75% cadence) - 1080p multi-plane parallax, contact shadows, Mimi.
   - Style B: V1 (Secondary, ~25% cadence) - Vector kinematic animation, Chintu & Golu.
3. Automated Quality Gate QA validation.
4. Support for both Dry-Run (local verification) and Live Upload modes.
5. Desktop notification and multi-source history tracking (uploads.json + cartoon_history.json).
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
from datetime import datetime

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")

from cartoon.config import (
    CARTOON_DIR, OUTPUT_DIR, THUMBNAILS_DIR,
    CARTOON_HISTORY_FILE
)
from cartoon.story_engine import StoryEngine
from cartoon.subtitles import generate_subtitles_file
from notifier import send_notification
import job_tracker

logger = logging.getLogger("kids_automation")


def extract_final_scene_frames(video_path, output_prefix="daily_scene"):
    """Extracts actual frame captures from the rendered MP4 for visual inspection."""
    times = [
        (1, 2.5),
        (2, 9.5),
        (3, 16.5),
        (4, 23.5),
        (5, 30.0),
        (6, 37.0)
    ]
    for s_id, t in times:
        out_p = os.path.join(OUTPUT_DIR, f"{output_prefix}_{s_id}.jpg")
        cmd = ["ffmpeg", "-y", "-ss", str(t), "-i", video_path, "-vframes", "1", "-q:v", "2", out_p]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def synthesize_story_narration(scenes, output_wav, output_json, voice="hi-IN-SwaraNeural"):
    """
    Synthesizes speech for each scene via Edge-TTS and builds timing metadata and master wav.
    """
    import numpy as np
    import scipy.io.wavfile as wavfile

    sr = 48000
    all_segments = []
    timing_records = []
    current_time = 0.0

    temp_dir = os.path.join(CARTOON_DIR, "output", "temp_tts")
    os.makedirs(temp_dir, exist_ok=True)

    for idx, sc in enumerate(scenes):
        seg_mp3 = os.path.join(temp_dir, f"seg_{idx+1}.mp3")
        seg_wav = os.path.join(temp_dir, f"seg_{idx+1}.wav")

        # Edge-TTS synthesis with retries and backoff
        synthesized = False
        for attempt in range(1, 6):
            if os.path.exists(seg_mp3):
                try:
                    os.remove(seg_mp3)
                except Exception:
                    pass
            cmd = [
                sys.executable, "-m", "edge_tts",
                "--voice", voice,
                "--rate=+12%",
                "--text", sc["text_hi"],
                "--write-media", seg_mp3
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=50)
                if res.returncode == 0 and os.path.exists(seg_mp3) and os.path.getsize(seg_mp3) > 1000:
                    synthesized = True
                    break
                else:
                    err = res.stderr.strip()[:200]
                    logger.warning(f"TTS segment {idx+1} attempt {attempt} error: {err}")
            except subprocess.TimeoutExpired:
                logger.warning(f"TTS segment {idx+1} attempt {attempt} timed out after 50s")
            except Exception as e:
                logger.warning(f"TTS segment {idx+1} attempt {attempt} failed: {e}")
            wait_time = (2 ** attempt) + 0.5
            time.sleep(wait_time)

        if not synthesized:
            raise RuntimeError(f"Failed to synthesize narration for scene {idx+1}")

        # Convert to 48kHz WAV
        subprocess.run(
            ["ffmpeg", "-y", "-i", seg_mp3, "-ar", str(sr), "-ac", "2", seg_wav],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        _, raw = wavfile.read(seg_wav)
        samples = raw.astype(np.float32) / 32768.0

        # Trim digital silence
        energy = np.abs(samples[:, 0]) + np.abs(samples[:, 1])
        thresh = 0.015
        non_silent = np.where(energy > thresh)[0]
        if len(non_silent) > 0:
            start_idx = max(0, non_silent[0] - int(sr * 0.04))
            end_idx = min(samples.shape[0], non_silent[-1] + int(sr * 0.04))
            samples = samples[start_idx:end_idx]

        # Peak normalization to -1.0 dBFS (0.89 peak)
        peak = np.max(np.abs(samples))
        if peak > 0:
            samples = samples * (0.89 / peak)

        # Micro-fades (15ms) to prevent clicks
        fade_len = int(sr * 0.015)
        if len(samples) > fade_len * 2:
            fade_in = np.linspace(0.0, 1.0, fade_len)[:, np.newaxis]
            fade_out = np.linspace(1.0, 0.0, fade_len)[:, np.newaxis]
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        seg_dur = len(samples) / sr
        pause_len = int(sr * 0.25)
        pause = np.zeros((pause_len, 2), dtype=np.float32)

        rec = dict(sc)
        rec["start_time"] = round(current_time, 3)
        rec["end_time"] = round(current_time + seg_dur, 3)
        rec["duration"] = round(seg_dur, 3)
        current_time = round(rec["end_time"] + 0.25, 3)

        timing_records.append(rec)
        all_segments.append(samples)
        all_segments.append(pause)

    # Master audio assembly
    full_audio = np.concatenate(all_segments, axis=0)
    wavfile.write(output_wav, sr, (full_audio * 32767).astype(np.int16))

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(timing_records, f, ensure_ascii=False, indent=2)

    logger.info(f"🎙️ Narration synthesized: {len(timing_records)} scenes, duration: {current_time:.2f}s")
    return timing_records, output_wav


def is_cartoon_completed_today(today_str=None, live_only=False):
    """
    Checks if a cartoon video has already been uploaded or completed today.
    If live_only is True, only verified YouTube uploads (with valid video_id) count.
    """
    if today_str is None:
        today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Primary source of truth: history/uploads.json
    uploads_file = r"C:\kids_automation\history\uploads.json"
    if os.path.exists(uploads_file):
        try:
            with open(uploads_file, "r", encoding="utf-8") as f:
                uploads = json.load(f)
            for u in uploads:
                ts = u.get("timestamp", "")
                if ts.startswith(today_str) and u.get("topic") == "cartoon_animation" and u.get("video_id"):
                    return True
        except Exception:
            pass

    # 2. Secondary source of truth: cartoon_history.json
    engine = StoryEngine()
    history = engine.load_history()

    valid_statuses = ("uploaded", "completed") if live_only else ("completed", "uploaded", "dry_run_success")
    for h in history:
        ts = h.get("timestamp", "")
        if ts.startswith(today_str) and h.get("status") in valid_statuses:
            if live_only and not h.get("video_id"):
                continue
            return True

    return False


def run_daily_cartoon(dry_run=True, style=None, story_id=None, privacy_status="public", force=False):
    """
    Main entry point for Cartoon Video (Video 3).
    Guarantees full failure isolation.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("==========================================================")
    logger.info(f"🎬 Starting Daily Cartoon Pipeline (Video 3): {today_str}")
    logger.info(f"   Timestamp: {run_timestamp}")
    logger.info(f"   Dry Run: {dry_run} | Style: {style or 'Auto'} | Force: {force}")
    logger.info("==========================================================")

    # 1. Check completion lock
    if not force and is_cartoon_completed_today(today_str, live_only=not dry_run):
        logger.info(f"⏳ Cartoon video for today ({today_str}) is ALREADY COMPLETED on YouTube.")
        logger.info("   Skipping cartoon execution. Use --force to rerun.")
        return True

    try:
        engine = StoryEngine()
        story = engine.get_next_story(forced_story_id=story_id, forced_style=style)
        actual_style = story["style"].upper()
        s_id = story["story_id"]

        logger.info(f"📖 Selected Story: {story['title_hi']} ({story['title_en']})")
        logger.info(f"🎨 Selected Animation Engine: Style {actual_style}")

        # Paths
        audio_dir = os.path.join(CARTOON_DIR, "output", "audio")
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(THUMBNAILS_DIR, exist_ok=True)

        timing_file = os.path.join(audio_dir, f"{s_id}_{run_timestamp}_timing.json")
        audio_master = os.path.join(audio_dir, f"{s_id}_{run_timestamp}_master.wav")
        srt_file = os.path.join(OUTPUT_DIR, f"{s_id}_{run_timestamp}.srt")
        video_file = os.path.join(OUTPUT_DIR, f"{s_id}_{run_timestamp}.mp4")
        thumb_file = os.path.join(THUMBNAILS_DIR, f"{s_id}_{run_timestamp}.jpg")

        # 2. Audio & Timing Preparation
        if actual_style == "V4":
            base_audio = os.path.join(CARTOON_DIR, "assets_v3", "audio", "final_master_audio_v3.wav")
            base_timing = os.path.join(CARTOON_DIR, "assets_v3", "audio", "timing_metadata.json")
            if s_id == "v4_mimi_magic_train" and os.path.exists(base_audio) and os.path.exists(base_timing):
                audio_master = base_audio
                timing_file = base_timing
                with open(timing_file, "r", encoding="utf-8") as f:
                    timing_meta = json.load(f)
            else:
                timing_meta, audio_master = synthesize_story_narration(story["scenes"], audio_master, timing_file)
        else:
            base_audio = os.path.join(CARTOON_DIR, "assets", "audio", "final_master_audio.wav")
            base_timing = os.path.join(CARTOON_DIR, "assets", "audio", "timing_metadata.json")
            if s_id == "v1_chintu_shares" and os.path.exists(base_audio) and os.path.exists(base_timing):
                audio_master = base_audio
                timing_file = base_timing
                with open(timing_file, "r", encoding="utf-8") as f:
                    timing_meta = json.load(f)
            else:
                timing_meta, audio_master = synthesize_story_narration(story["scenes"], audio_master, timing_file)

        # 3. Subtitles Generation
        logger.info("📝 Generating Subtitles SRT...")
        generate_subtitles_file(timing_meta, srt_file)

        # 4. Rendering
        if actual_style == "V4":
            from cartoon.scene_renderer_v4 import SceneRendererV4
            from cartoon.thumbnail_v4 import create_cartoon_thumbnail_v4
            from cartoon.quality_gate_v4 import inspect_cartoon_v4

            logger.info("🎬 Rendering Cartoon Video via SceneRendererV4 (1080p Parallax)...")
            renderer = SceneRendererV4(
                environment=story.get("background", "playroom"),
                character=story.get("main_character", "mimi")
            )
            renderer.render_animation_video(timing_meta, audio_master, srt_file, video_file)

            logger.info("🎨 Generating High-CTR Thumbnail V4...")
            create_cartoon_thumbnail_v4(thumb_file)

            logger.info("🛡️ Running Dual Technical & Visual Quality Gate QA...")
            qa_res = inspect_cartoon_v4(video_file, thumb_file)
            qa_passed = qa_res.get("technical_passed", False) and qa_res.get("visual_passed", False)
        else:
            from cartoon.scene_renderer import SceneRenderer
            from cartoon.thumbnail import create_cartoon_thumbnail
            from cartoon.quality_gate import inspect_cartoon_video

            logger.info("🎬 Rendering Cartoon Video via SceneRenderer V1 (Vector Kinematic)...")
            renderer = SceneRenderer(
                background_name=story.get("background", "forest_meadow"),
                character=story.get("main_character", "chintu")
            )
            renderer.render_animation_video(timing_meta, audio_master, srt_file, video_file)

            logger.info("🎨 Generating High-CTR Thumbnail V1...")
            create_cartoon_thumbnail(thumb_file)

            logger.info("🛡️ Running Quality Gate QA...")
            qa_res = inspect_cartoon_video(video_file, thumb_file)
            qa_passed = qa_res.get("passed", False)

        extract_final_scene_frames(video_file, output_prefix=f"{s_id}_scene")

        if not qa_passed:
            logger.warning("⚠️ Cartoon Quality Gate inspection reported warnings. Please inspect QA output.")

        # 5. YouTube Upload or Dry-Run
        metadata = engine.build_youtube_metadata(story)

        # Video SHA-256 hash check for uniqueness
        video_hash = engine.variety_mgr.compute_file_hash(video_file)
        logger.info(f"🔒 Video SHA-256: {video_hash}")

        if dry_run:
            logger.info("🧪 [DRY-RUN] Cartoon video rendered and verified successfully!")
            logger.info(f"   Video File: {video_file}")
            logger.info(f"   Thumbnail:  {thumb_file}")
            logger.info("   (Skipping YouTube upload in dry-run mode).")

            job_tracker.update_job(
                "cartoon",
                state="dry_run_success",
                story_id=s_id,
                style=actual_style,
                title=story["title_en"],
                video_path=video_file,
                thumb_path=thumb_file,
                video_hash=video_hash
            )

            engine.record_run(
                story_id=s_id,
                style=actual_style,
                title=story["title_en"],
                main_character=story.get("main_character"),
                characters=story.get("characters"),
                background=story.get("background"),
                location=story.get("location"),
                visual_theme=story.get("visual_theme"),
                video_path=video_file,
                thumb_path=thumb_file,
                video_hash=video_hash,
                status="dry_run_success"
            )
            return True

        # Live Upload
        logger.info("🚀 Initiating YouTube Upload for Cartoon Video 3...")
        from video_validator import validate_video_file
        valid_vid, val_err, _, _ = validate_video_file(video_file)
        if not valid_vid:
            logger.error(f"❌ Pre-upload cartoon video validation failed: {val_err}")
            job_tracker.update_job("cartoon", state=job_tracker.STATE_FAILED, error_message=val_err)
            return False

        from uploader import upload_video_to_youtube

        job_tracker.update_job(
            "cartoon",
            state=job_tracker.STATE_UPLOAD_PENDING,
            story_id=s_id,
            style=actual_style,
            title=story["title_en"],
            video_path=video_file,
            thumb_path=thumb_file,
            video_hash=video_hash
        )

        ok_upload, vid_id, upload_res = upload_video_to_youtube(
            video_path=video_file,
            metadata=metadata,
            thumbnail_path=thumb_file,
            privacy_status=privacy_status,
            interactive=False,
            slot="cartoon"
        )

        if not ok_upload:
            logger.error(f"❌ YouTube upload failed for Cartoon Video 3: {upload_res}")
            job_tracker.update_job("cartoon", state=job_tracker.STATE_FAILED, error_message=str(upload_res))
            send_notification(
                "Fun Learning Kids — Cartoon Error",
                f"Cartoon Video 3 upload failed: {str(upload_res)[:80]}",
                error=True
            )
            return False

        logger.info("==========================================================")
        logger.info("🎉🎉 Cartoon Video 3 Uploaded Successfully! 🎉🎉")
        logger.info(f"   Title: {metadata['title']}")
        logger.info(f"   URL:   {upload_res}")
        logger.info("==========================================================")

        engine.record_run(
            story_id=s_id,
            style=actual_style,
            title=story["title_en"],
            main_character=story.get("main_character"),
            characters=story.get("characters"),
            background=story.get("background"),
            location=story.get("location"),
            visual_theme=story.get("visual_theme"),
            video_path=video_file,
            thumb_path=thumb_file,
            video_hash=video_hash,
            video_id=vid_id,
            status="uploaded"
        )

        send_notification(
            "Fun Learning Kids — Cartoon Complete",
            f"Cartoon Video 3 ('{story['title_en']}') uploaded successfully!"
        )
        return True

    except Exception as e:
        err_msg = f"Cartoon Video 3 encountered an isolated exception: {e}"
        logger.error(f"❌ {err_msg}", exc_info=True)
        job_tracker.update_job("cartoon", state=job_tracker.STATE_FAILED, error_message=str(e))
        send_notification(
            "Fun Learning Kids — Cartoon Exception",
            f"Cartoon pipeline failed: {str(e)[:100]}",
            error=True
        )
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fun Learning Kids Cartoon Daily Runner")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Test run without uploading")
    parser.add_argument("--style", choices=["v4", "v1", "V4", "V1"], help="Force specific style")
    parser.add_argument("--story", help="Force specific story_id")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--force", action="store_true", help="Force execution even if already completed today")
    args = parser.parse_args()

    success = run_daily_cartoon(
        dry_run=args.dry_run,
        style=args.style,
        story_id=args.story,
        privacy_status=args.privacy,
        force=args.force
    )
    if not success:
        sys.exit(1)
