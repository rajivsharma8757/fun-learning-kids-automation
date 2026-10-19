import os
import sys
import argparse
import logging
from datetime import datetime

from config import (
    BASE_DIR, AUDIO_DIR, VIDEO_DIR, THUMBNAIL_DIR, LOG_DIR,
    LOG_FILE, LAST_RUN_FILE, SCHEDULE_SLOTS, TOPICS,
    UPLOADS_HISTORY_FILE, VIDEO_FORMAT, CHANNEL_NAME
)
from content_manager import ContentManager
from voice_generator import generate_voice
from video_maker import generate_srt_file, create_video
from thumbnail_maker import create_thumbnail
from uploader import upload_video_to_youtube
from video_validator import validate_video_file
import job_tracker

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

def check_and_acquire_lock(slot_id, slot_name=None, force=False):
    """
    Checks if this slot has already run today to support 2 videos per day
    without duplicate executions.
    """
    if force:
        logger.info("⚡ Force flag enabled: bypassing slot lock.")
        return True

    today_str = datetime.now().strftime("%Y-%m-%d")
    if slot_name and job_tracker.is_slot_completed(slot_name, today_str):
        logger.info(f"⏳ Slot '{slot_name}' already confirmed UPLOADED today. Exiting safely.")
        return False

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

def run_pipeline(topic=None, slot=None, dry_run=False, privacy_status="public", force=False, interactive=False, format_profile=None):
    """
    Main execution pipeline for Fun Learning Kids:
    Topic -> Script -> Hindi Voice -> Images -> Video + Subtitles -> Thumbnail -> YouTube Upload -> Log
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_slot = determine_current_slot(slot)
    slot_id = f"{today_str}_{current_slot}"
    run_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    from config import FORMAT_PROFILES, DEFAULT_FORMAT, FORMAT_SHORTS, FORMAT_LANDSCAPE, DAILY_SLOT_FORMATS
    active_format = (
        format_profile
        or os.getenv("VIDEO_FORMAT")
        or DAILY_SLOT_FORMATS.get(current_slot)
        or DEFAULT_FORMAT
    ).lower()
    if active_format not in FORMAT_PROFILES:
        active_format = DEFAULT_FORMAT
    prof = FORMAT_PROFILES[active_format]

    logger.info("==================================================")
    logger.info(f"🌟 Starting {CHANNEL_NAME} Pipeline: {slot_id}")
    logger.info(f"   Timestamp: {run_timestamp}")
    logger.info(f"   Profile:   {prof['name'].upper()} ({prof['width']}x{prof['height']}, {prof['aspect_ratio']})")
    logger.info(f"   Dry Run: {dry_run} | Privacy: {privacy_status} | Force: {force}")
    logger.info("==================================================")

    if not check_and_acquire_lock(slot_id, slot_name=current_slot, force=force):
        return True

    job_tracker.update_job(current_slot, state=job_tracker.STATE_GENERATING)

    # 1. Select Topic, Script & Images
    cm = ContentManager()
    chosen_topic = cm.get_next_topic(requested_topic=topic, slot=current_slot)
    script = cm.get_next_script(chosen_topic)
    topic_images = cm.get_topic_images(chosen_topic, count=1, script=script)
    primary_image = topic_images[0]

    job_tracker.update_job(
        current_slot,
        topic=chosen_topic,
        script_id=script["id"],
        title=script["title"]
    )

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
        job_tracker.update_job(current_slot, state=job_tracker.STATE_FAILED, error_message="Voice generation failed")
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
        audio_duration=audio_duration,
        format_profile=active_format
    )
    if not ok_video:
        logger.error(f"❌ Pipeline stopped: Video creation failed ({vid_err}).")
        job_tracker.update_job(current_slot, state=job_tracker.STATE_FAILED, error_message=f"Video creation failed: {vid_err}")
        return False

    # Pre-upload integrity check
    valid_vid, val_err, _, _ = validate_video_file(video_path)
    if not valid_vid:
        logger.error(f"❌ Pre-upload video validation failed: {val_err}")
        job_tracker.update_job(current_slot, state=job_tracker.STATE_FAILED, error_message=val_err)
        return False

    # 5. Generate Thumbnail with Pillow
    short_title = script.get("short_title", chosen_topic.replace("_", " ").title())
    ok_thumb, thumb_err = create_thumbnail(
        image_path=primary_image,
        topic=chosen_topic,
        short_title=short_title,
        output_thumb_path=thumb_path,
        format_profile=active_format
    )
    if not ok_thumb:
        logger.warning(f"⚠️ Thumbnail generation failed ({thumb_err}); proceeding with default video frame.")
        actual_thumb = None
    else:
        actual_thumb = thumb_path

    job_tracker.update_job(
        current_slot,
        state=job_tracker.STATE_UPLOAD_PENDING,
        video_path=video_path,
        thumb_path=actual_thumb
    )

    # 6. Upload to YouTube
    if dry_run:
        logger.info("🧪 [DRY-RUN] Skipping YouTube upload step as requested.")
        job_tracker.update_job(current_slot, state="dry_run_success", video_path=video_path, thumb_path=actual_thumb)
        logger.info("🎉 [DRY-RUN] Pipeline completed successfully!")
        return True

    # Format a unique, high-CTR title to prevent YouTube spam filtering on repeated scripts
    script_usage_count = 1
    all_uploads = []
    if os.path.exists(UPLOADS_HISTORY_FILE):
        try:
            with open(UPLOADS_HISTORY_FILE, "r", encoding="utf-8") as f:
                all_uploads.extend(json.load(f))
        except Exception:
            pass
    audit_file = os.path.join(os.path.dirname(UPLOADS_HISTORY_FILE), "all_youtube_videos_audit.json")
    if os.path.exists(audit_file):
        try:
            with open(audit_file, "r", encoding="utf-8") as af:
                all_uploads.extend(json.load(af))
        except Exception:
            pass

    clean_base = " ".join(script.get("title", "").lower().split())
    script_usage_count = sum(
        1 for u in all_uploads
        if u.get("script_id") == script.get("id")
        or " ".join(u.get("title", "").lower().split()) == clean_base
        or " ".join(u.get("title", "").lower().split()).startswith(clean_base.split(" | ")[0].lower())
    ) + 1

    base_title = script["title"]
    # Strip any old legacy channel suffix
    for old_suffix in [" | Fun Learning Kids", " - Fun Learning Kids", " | fun learning kids"]:
        base_title = base_title.replace(old_suffix, "")

    if script_usage_count > 1:
        final_title = f"{base_title} | Ep {script_usage_count} | {CHANNEL_NAME}"
    else:
        final_title = f"{base_title} | {CHANNEL_NAME}"

    if active_format == FORMAT_SHORTS:
        if "#Shorts" not in final_title and len(final_title) <= 91:
            final_title = f"{final_title} #Shorts"

    if len(final_title) > 100:
        final_title = final_title[:97] + "..."

    raw_desc = script["description"]
    # Dynamically rebrand description to active channel name
    final_desc = raw_desc.replace("Fun Learning Kids", CHANNEL_NAME).replace("fun learning kids", CHANNEL_NAME)
    final_desc = final_desc.replace("#FunLearningKids", f"#{CHANNEL_NAME.replace(' ', '')}")

    if active_format == FORMAT_SHORTS and "#Shorts" not in final_desc:
        final_desc = f"{final_desc}\n\n#Shorts #YouTubeShorts"

    # Rebrand tags
    raw_tags = script.get("tags", [])
    final_tags = [
        t.replace("fun learning kids", CHANNEL_NAME.lower()).replace("Fun Learning Kids", CHANNEL_NAME)
        for t in raw_tags
    ]
    if CHANNEL_NAME.lower() not in [t.lower() for t in final_tags]:
        final_tags.append(CHANNEL_NAME.lower())
    if active_format == FORMAT_SHORTS:
        final_tags.extend(["Shorts", "YouTube Shorts"])

    upload_metadata = {
        "title": final_title,
        "description": final_desc,
        "tags": final_tags,
        "topic": chosen_topic
    }

    ok_upload, vid_id, upload_res = upload_video_to_youtube(
        video_path=video_path,
        metadata=upload_metadata,
        thumbnail_path=actual_thumb,
        privacy_status=privacy_status,
        interactive=interactive,
        slot=current_slot
    )

    if not ok_upload:
        logger.error(f"❌ Pipeline stopped: YouTube upload failed: {upload_res}")
        logger.error("   (Lock not saved so this run can be safely retried.)")
        job_tracker.update_job(current_slot, state=job_tracker.STATE_FAILED, error_message=str(upload_res))
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
    parser.add_argument("--format", choices=["landscape", "shorts"], default=None, help="Explicit format profile: 'landscape' (16:9, 1280x720) or 'shorts' (9:16, 1080x1920)")
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
            interactive=args.interactive,
            format_profile=args.format
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
