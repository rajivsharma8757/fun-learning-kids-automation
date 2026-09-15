import os
import sys
import argparse
import logging
from datetime import datetime

from config import (
    BASE_DIR, AUDIO_DIR, VIDEO_DIR, THUMBNAIL_DIR, LOG_DIR,
    LOG_FILE, LAST_RUN_FILE, SCHEDULE_SLOTS, TOPICS
)
from content_manager import ContentManager
from voice_generator import generate_voice
from video_maker import generate_srt_file, create_video
from thumbnail_maker import create_thumbnail
from uploader import upload_video_to_youtube

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("kids_automation")

def determine_current_slot(requested_slot=None):
    """
    Determines whether this run belongs to the 'morning' or 'evening' slot.
    Morning: before 15:00 (3 PM). Evening: 15:00 onwards.
    """
    if requested_slot in ("morning", "evening"):
        return requested_slot

    current_hour = datetime.now().hour
    if current_hour < 15:
        return "morning"
    else:
        return "evening"

def check_and_acquire_lock(slot_id, force=False):
    """
    Checks if this slot has already run today to support 2 videos per day
    without duplicate executions.
    """
    if force:
        logger.info("⚡ Force flag enabled: bypassing slot lock.")
        return True

    if os.path.exists(LAST_RUN_FILE):
        try:
            with open(LAST_RUN_FILE, "r", encoding="utf-8") as f:
                last_run = f.read().strip()
            if last_run == slot_id:
                logger.info(f"⏳ Slot '{slot_id}' already completed today. Exiting safely.")
                return False
        except Exception as e:
            logger.warning(f"Could not read {LAST_RUN_FILE}: {e}")

    return True

def record_lock(slot_id):
    """Saves completed slot ID to last_run.txt."""
    try:
        with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
            f.write(slot_id)
    except Exception as e:
        logger.error(f"Failed to write lock to {LAST_RUN_FILE}: {e}")

def run_pipeline(topic=None, slot=None, dry_run=False, privacy_status="public", force=False, interactive=False):
    """
    Main execution pipeline for Fun Learning Kids:
    Topic -> Script -> Hindi Voice -> Images -> Video + Subtitles -> Thumbnail -> YouTube Upload -> Log
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_slot = determine_current_slot(slot)
    slot_id = f"{today_str}_{current_slot}"
    run_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    logger.info("==================================================")
    logger.info(f"🌟 Starting Fun Learning Kids Pipeline: {slot_id}")
    logger.info(f"   Timestamp: {run_timestamp}")
    logger.info(f"   Dry Run: {dry_run} | Privacy: {privacy_status} | Force: {force}")
    logger.info("==================================================")

    if not check_and_acquire_lock(slot_id, force=force):
        return True

    # 1. Select Topic, Script & Images
    cm = ContentManager()
    chosen_topic = cm.get_next_topic(requested_topic=topic, slot=current_slot)
    script = cm.get_next_script(chosen_topic)
    topic_images = cm.get_topic_images(chosen_topic, count=1, script=script)
    primary_image = topic_images[0]

    logger.info(f"📌 Chosen Topic: {chosen_topic}")
    logger.info(f"📝 Script ID: {script['id']} | Title: {script['title']}")
    logger.info(f"🖼️ Selected Image: {primary_image}")

    # Paths for artifacts
    audio_path = os.path.join(AUDIO_DIR, f"{chosen_topic}_{run_timestamp}.mp3")
    srt_path = os.path.join(VIDEO_DIR, f"{chosen_topic}_{run_timestamp}.srt")
    video_path = os.path.join(VIDEO_DIR, f"{chosen_topic}_{run_timestamp}.mp4")
    thumb_path = os.path.join(THUMBNAIL_DIR, f"{chosen_topic}_{run_timestamp}.jpg")

    # 2. Generate Hindi Voice Narration
    ok_voice, audio_duration = generate_voice(script["voice_text"], audio_path)
    if not ok_voice:
        logger.error("❌ Pipeline stopped: Voice generation failed.")
        return False

    # 3. Generate English Subtitles
    ok_srt = generate_srt_file(script.get("subtitles_en", []), audio_duration, srt_path)
    if not ok_srt:
        logger.warning("⚠️ Could not generate subtitles; video will proceed without subtitle overlay.")
        srt_to_use = None
    else:
        srt_to_use = srt_path

    # 4. Generate Video with FFmpeg
    ok_video, vid_err = create_video(
        image_path=primary_image,
        audio_path=audio_path,
        srt_path=srt_to_use,
        output_video_path=video_path,
        audio_duration=audio_duration
    )
    if not ok_video:
        logger.error(f"❌ Pipeline stopped: Video creation failed ({vid_err}).")
        return False

    # 5. Generate Thumbnail with Pillow
    short_title = script.get("short_title", chosen_topic.replace("_", " ").title())
    ok_thumb, thumb_err = create_thumbnail(
        image_path=primary_image,
        topic=chosen_topic,
        short_title=short_title,
        output_thumb_path=thumb_path
    )
    if not ok_thumb:
        logger.warning(f"⚠️ Thumbnail generation failed ({thumb_err}); proceeding with default video frame.")
        actual_thumb = None
    else:
        actual_thumb = thumb_path

    # 6. Upload to YouTube
    if dry_run:
        logger.info("🧪 [DRY-RUN] Skipping YouTube upload step as requested.")
        record_lock(slot_id)
        logger.info("🎉 [DRY-RUN] Pipeline completed successfully!")
        return True

    upload_metadata = {
        "title": script["title"],
        "description": script["description"],
        "tags": script["tags"],
        "topic": chosen_topic
    }

    ok_upload, vid_id, upload_res = upload_video_to_youtube(
        video_path=video_path,
        metadata=upload_metadata,
        thumbnail_path=actual_thumb,
        privacy_status=privacy_status,
        interactive=interactive
    )

    if not ok_upload:
        logger.error(f"❌ Pipeline stopped: YouTube upload failed: {upload_res}")
        logger.error("   (Lock not saved so this run can be safely retried.)")
        return False

    # 7. Record Completion
    record_lock(slot_id)

    # Clean up temporary audio/srt
    for temp_file in [audio_path, srt_path]:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

    logger.info("==================================================")
    logger.info("🎉🎉 Full Pipeline Completed Successfully! 🎉🎉")
    logger.info(f"   Video File: {video_path}")
    logger.info(f"   Thumbnail:  {actual_thumb}")
    logger.info(f"   YouTube URL: {upload_res}")
    logger.info("==================================================")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fun Learning Kids YouTube Automation")
    parser.add_argument("--topic", choices=TOPICS, help="Force a specific topic")
    parser.add_argument("--slot", choices=["morning", "evening", "cartoon"], help="Specify schedule slot")
    parser.add_argument("--style", choices=["v4", "v1", "V4", "V1"], help="Force cartoon animation style (V4 or V1)")
    parser.add_argument("--story", help="Force specific cartoon story_id")
    parser.add_argument("--dry-run", action="store_true", help="Generate video & thumbnail without uploading")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"], help="Upload privacy status")
    parser.add_argument("--force", action="store_true", help="Bypass slot completion check")
    parser.add_argument("--interactive", action="store_true", help="Allow interactive OAuth browser popup if needed")
    parser.add_argument("--daily", action="store_true", help="Run full daily manager for 3-video target")

    args = parser.parse_args()

    # If cartoon slot requested, dispatch directly to cartoon runner
    if args.slot == "cartoon":
        from cartoon.cartoon_daily_runner import run_daily_cartoon
        success = run_daily_cartoon(
            dry_run=args.dry_run,
            style=args.style,
            story_id=args.story,
            privacy_status=args.privacy,
            force=args.force
        )
    elif args.slot or args.topic or (args.dry_run and not args.daily):
        # Run single normal video pipeline slot
        success = run_pipeline(
            topic=args.topic,
            slot=args.slot,
            dry_run=args.dry_run,
            privacy_status=args.privacy,
            force=args.force,
            interactive=args.interactive
        )
    else:
        # Default laptop-on / scheduled daily automation mode (3 videos/day)
        from daily_manager import run_daily_automation
        success = run_daily_automation(
            privacy_status=args.privacy,
            force=args.force,
            dry_run=args.dry_run
        )

    if not success:
        sys.exit(1)
