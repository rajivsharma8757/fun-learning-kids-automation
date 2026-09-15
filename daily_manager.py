import os
import sys
import time
import json
import socket
import urllib.request
import logging
from datetime import datetime

from config import (
    BASE_DIR, UPLOADS_HISTORY_FILE, LOG_FILE,
    LAST_RUN_FILE, DEFAULT_PRIVACY_STATUS
)
from notifier import send_notification

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger("kids_automation")

def is_internet_connected(timeout=4):
    """
    Checks if active internet connectivity is available.
    Tests DNS socket connection and HTTPS endpoint.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except socket.error:
        pass

    try:
        urllib.request.urlopen("https://www.google.com", timeout=timeout)
        return True
    except Exception:
        return False

def wait_for_internet(max_wait_seconds=120, check_interval=5):
    """
    Waits for internet connectivity when laptop boots up.
    Gives Wi-Fi / Ethernet time to establish connection.
    """
    logger.info(f"🌐 Verifying internet connectivity (timeout {max_wait_seconds}s)...")
    start_time = time.time()
    attempt = 1

    while time.time() - start_time < max_wait_seconds:
        if is_internet_connected(timeout=4):
            logger.info("✅ Internet connection verified active.")
            return True
        logger.info(f"⏳ Waiting for internet connection... (attempt {attempt}, {int(time.time() - start_time)}s elapsed)")
        time.sleep(check_interval)
        attempt += 1

    logger.warning("❌ Internet connection could not be established.")
    return False

def get_today_uploads(today_str=None):
    """
    Returns list of upload records for today from history/uploads.json.
    """
    if today_str is None:
        today_str = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(UPLOADS_HISTORY_FILE):
        return []

    try:
        with open(UPLOADS_HISTORY_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        logger.error(f"Error reading {UPLOADS_HISTORY_FILE}: {e}")
        return []

    today_records = []
    for item in records:
        ts = item.get("timestamp", "")
        # Checks if timestamp starts with YYYY-MM-DD and has a valid video_id
        if ts.startswith(today_str) and item.get("video_id"):
            today_records.append(item)

    return today_records

def get_today_normal_uploads(today_str=None):
    """Returns list of normal video records (topics: moral_story, numbers, etc.) uploaded today."""
    today_uploads = get_today_uploads(today_str)
    return [u for u in today_uploads if u.get("topic") != "cartoon_animation"]

def get_today_cartoon_uploads(today_str=None):
    """Returns list of cartoon video records uploaded today."""
    today_uploads = get_today_uploads(today_str)
    cart = [u for u in today_uploads if u.get("topic") == "cartoon_animation"]
    if cart:
        return cart

    # Also inspect history/cartoon_history.json
    try:
        from cartoon.story_engine import StoryEngine
        engine = StoryEngine()
        ch = engine.load_history()
        if today_str is None:
            today_str = datetime.now().strftime("%Y-%m-%d")
        return [h for h in ch if h.get("timestamp", "").startswith(today_str) and h.get("status") in ("uploaded", "completed") and h.get("video_id")]
    except Exception:
        return []

def is_cartoon_pending(today_str=None):
    """Checks if today's cartoon animation video (Video 3) is pending."""
    return len(get_today_cartoon_uploads(today_str)) == 0

def get_pending_slots(today_str=None):
    """
    Calculates which normal video slots are pending for today.
    Normal daily target = 2 videos.
    - If 0 normal uploaded: ['morning', 'evening'] (Video 1 and Video 2)
    - If 1 normal uploaded: ['evening'] (Video 2)
    - If 2+ normal uploaded: [] (Complete)
    """
    normal_uploads = get_today_normal_uploads(today_str)
    count = len(normal_uploads)

    if count == 0:
        return ["morning", "evening"]
    elif count == 1:
        return ["evening"]
    else:
        return []

def run_daily_automation(privacy_status=None, force=False, dry_run=False):
    """
    Master daily automation runner for Fun Learning Kids (Target: 3 Videos/Day):
    - Video 1: Normal Educational Video (Morning slot)
    - Video 2: Normal Educational Video (Evening slot)
    - Video 3: Cartoon Animation Video (Style A: V4 / Style B: V1 rotation)
    With complete failure isolation: failures in any video never block remaining videos.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info("==================================================")
    logger.info(f"🚀 Fun Learning Kids Daily Manager Started: {today_str} (Target: 3 Videos/Day)")
    logger.info(f"   Dry Run: {dry_run} | Force: {force} | Privacy: {privacy_status or DEFAULT_PRIVACY_STATUS}")
    logger.info("==================================================")

    # 1. Check Internet Connectivity
    if not wait_for_internet(max_wait_seconds=90, check_interval=5):
        msg = "Internet connection is unavailable. Automation will retry automatically on next check."
        logger.error(f"❌ {msg}")
        send_notification("Fun Learning Kids — Alert", msg, error=True)
        return False

    # 2. Check Today's Status
    normal_uploads = get_today_normal_uploads(today_str)
    cartoon_uploads = get_today_cartoon_uploads(today_str)
    normal_count = len(normal_uploads)
    cartoon_count = len(cartoon_uploads)
    total_count = normal_count + cartoon_count

    logger.info(f"📊 Today's Progress ({today_str}): {total_count}/3 videos completed.")
    logger.info(f"   - Normal Videos: {normal_count}/2 | Cartoon Video: {cartoon_count}/1")

    pending_normal_slots = get_pending_slots(today_str)
    cartoon_pending = is_cartoon_pending(today_str)

    if not pending_normal_slots and not cartoon_pending and not force:
        logger.info("🎉 Today's daily target of 3 videos is ALREADY COMPLETED!")
        logger.info("   (2 Normal Videos + 1 Cartoon Video). Laptop is free for other work.")
        return True

    if force:
        if not pending_normal_slots:
            pending_normal_slots = ["evening"]
        cartoon_pending = True

    logger.info(f"🎯 Pending Normal Video Slots: {pending_normal_slots} | Cartoon Pending: {cartoon_pending}")

    from run import run_pipeline
    from cartoon.cartoon_daily_runner import run_daily_cartoon

    target_privacy = privacy_status or DEFAULT_PRIVACY_STATUS

    # Step A: Execute Pending Normal Slots (Videos 1 & 2)
    for slot in pending_normal_slots:
        video_num = 1 if slot == "morning" else 2
        logger.info(f"\n▶️ Processing Today's Normal Video {video_num} (Slot: {slot})...")

        try:
            success = run_pipeline(
                slot=slot,
                privacy_status=target_privacy,
                dry_run=dry_run,
                force=True  # Force since slot logic was verified by daily manager
            )

            if success:
                action_type = "created (dry-run)" if dry_run else "created and uploaded"
                success_msg = f"Normal Video {video_num} {action_type} successfully!"
                logger.info(f"✅ {success_msg}")
                if not dry_run:
                    send_notification(
                        "Fun Learning Kids",
                        f"Normal Video {video_num} uploaded successfully to YouTube."
                    )
            else:
                fail_msg = f"Normal Video {video_num} failed during generation/upload. Check logs."
                logger.error(f"❌ {fail_msg}")
                send_notification(
                    "Fun Learning Kids — Error",
                    fail_msg,
                    error=True
                )
        except Exception as e:
            err_msg = f"Normal Video {video_num} encountered exception: {e}"
            logger.error(f"❌ {err_msg}")
            send_notification(
                "Fun Learning Kids — Exception",
                f"Normal Video {video_num} failed: {str(e)[:100]}",
                error=True
            )

    # Step B: Execute Pending Cartoon Slot (Video 3) with Full Failure Isolation
    if cartoon_pending:
        logger.info("\n▶️ Processing Today's Cartoon Animation Video (Video 3)...")
        try:
            c_success = run_daily_cartoon(
                dry_run=dry_run,
                privacy_status=target_privacy,
                force=force
            )
            if c_success:
                action_type = "created and verified (dry-run)" if dry_run else "created and uploaded"
                logger.info(f"✅ Cartoon Video 3 {action_type} successfully!")
            else:
                logger.error("❌ Cartoon Video 3 failed. Inspect cartoon logs.")
        except Exception as e:
            logger.error(f"❌ Cartoon Video 3 encountered an isolated exception: {e}", exc_info=True)
            # Failure isolation: cartoon error never breaks the daily manager

    # Step C: Final Daily Summary Verification
    final_norm = len(get_today_normal_uploads(today_str))
    final_cart = len(get_today_cartoon_uploads(today_str))
    final_total = final_norm + final_cart

    logger.info("==================================================")
    logger.info(f"📋 Daily Run Finished: {final_total}/3 videos completed today.")
    logger.info(f"   Normal Videos: {final_norm}/2 | Cartoon Video: {final_cart}/1")
    logger.info("==================================================")

    if final_total >= 3 or (dry_run and final_norm >= 2 and final_cart >= 1):
        final_msg = "Today's 3 videos (2 Normal + 1 Cartoon) have been successfully completed! Today's work is complete."
        logger.info(f"🎉🎉 {final_msg}")
        if not dry_run:
            send_notification("Fun Learning Kids", final_msg)
        return True
    else:
        pending_rem = 3 - final_total
        logger.warning(f"⚠️ {pending_rem} video(s) still pending for today. Will retry on next check.")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fun Learning Kids Daily Manager (3 Videos/Day)")
    parser.add_argument("--privacy", default=None, choices=["public", "unlisted", "private"])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Run full daily manager in dry-run mode without uploading")
    args = parser.parse_args()

    run_daily_automation(privacy_status=args.privacy, force=args.force, dry_run=args.dry_run)
