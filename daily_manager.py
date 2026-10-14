"""
daily_manager.py
----------------
Master Orchestrator for Fun Learning Kids Automation (Daily Target: 3 Videos).

Video Target:
1. Normal Video 1 (Morning slot: Educational / Story)
2. Normal Video 2 (Evening slot: Educational / Story)
3. Cartoon Video 3 (Cartoon Animation slot: Alternating V1 Vector / V4 Parallax)

Key Guarantees:
- Windows process lock prevents duplicate overlapping runs (e.g. logon trigger + schedule).
- Failure Isolation: A failure in any video NEVER blocks the remaining videos.
- Idempotency & Resumption: Only uncompleted slots are generated/uploaded.
- Persistent state tracking via job_tracker.py and history/uploads.json.
- Structured, truthful end-of-run daily summary.
"""

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
import job_tracker

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger("kids_automation")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )


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


def wait_for_internet(max_wait_seconds=90, check_interval=5):
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
    """Returns list of upload records for today from history/uploads.json."""
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
        if ts.startswith(today_str) and item.get("video_id"):
            today_records.append(item)

    return today_records


def get_today_normal_uploads(today_str=None):
    """Returns list of normal educational videos uploaded today."""
    today_uploads = get_today_uploads(today_str)
    return [u for u in today_uploads if u.get("topic") != "cartoon_animation"]


def get_today_cartoon_uploads(today_str=None):
    """Returns list of cartoon animation videos uploaded today."""
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
        return [
            h for h in ch
            if h.get("timestamp", "").startswith(today_str)
            and h.get("status") in ("uploaded", "completed")
            and h.get("video_id")
        ]
    except Exception:
        return []


def run_daily_automation(privacy_status=None, force=False, dry_run=False):
    """
    Master daily automation runner for Fun Learning Kids (Target: 3 Videos/Day):
    - Video 1: Normal Educational Video (Morning slot)
    - Video 2: Normal Educational Video (Evening slot)
    - Video 3: Cartoon Animation Video (Alternating V1 / V4 styles)

    Features:
    - Concurrency process lock prevents multiple simultaneous executions.
    - Full failure isolation: one video failure never cancels remaining videos.
    - Detailed per-slot structured tracking and end-of-run audit report.
    """
    # 0. Acquire Concurrency Lock
    if not job_tracker.acquire_process_lock():
        logger.info(
            "⏳ Another instance of Fun Learning Kids automation is currently running.\n"
            "   Exiting cleanly to prevent duplicate runs and conflicting uploads."
        )
        return True

    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        target_privacy = privacy_status or DEFAULT_PRIVACY_STATUS

        logger.info("==================================================")
        logger.info(f"🚀 Fun Learning Kids Daily Manager Started: {today_str} (Target: 3 Videos/Day)")
        logger.info(f"   Dry Run: {dry_run} | Force: {force} | Privacy: {target_privacy}")
        logger.info("==================================================")

        # 1. Verify Internet Connectivity
        if not wait_for_internet(max_wait_seconds=90, check_interval=5):
            msg = "Internet connection is unavailable. Automation will retry automatically on next scheduled trigger."
            logger.error(f"❌ {msg}")
            send_notification("Fun Learning Kids — Alert", msg, error=True)
            return False

        # 2. Check Existing Progress for Today
        normal_uploads = get_today_normal_uploads(today_str)
        cartoon_uploads = get_today_cartoon_uploads(today_str)

        norm_count = len(normal_uploads)
        cart_count = len(cartoon_uploads)
        total_count = norm_count + cart_count

        logger.info(f"📊 Current Today Progress ({today_str}): {total_count}/3 videos confirmed on YouTube.")
        logger.info(f"   - Normal Videos: {norm_count}/2 | Cartoon Video: {cart_count}/1")

        # Determine which slots need execution
        # Normal Slot 1 ('morning')
        morning_done = job_tracker.is_slot_completed("morning", today_str) or (norm_count >= 1)
        # Normal Slot 2 ('evening')
        evening_done = job_tracker.is_slot_completed("evening", today_str) or (norm_count >= 2)
        # Cartoon Slot 3 ('cartoon')
        cartoon_done = job_tracker.is_slot_completed("cartoon", today_str) or (cart_count >= 1)

        if not force and morning_done and evening_done and cartoon_done:
            logger.info("🎉 Today's daily target of 3 videos is ALREADY COMPLETED!")
            logger.info("   (2 Normal Educational Videos + 1 Cartoon Video). System is idle.")
            return True

        from run import run_pipeline
        from cartoon.cartoon_daily_runner import run_daily_cartoon

        # Step A: Normal Video 1 (Morning Slot)
        if not morning_done or force:
            logger.info("\n▶️ Processing Today's Normal Video 1 (Slot: morning)...")
            try:
                m_ok = run_pipeline(
                    slot="morning",
                    privacy_status=target_privacy,
                    dry_run=dry_run,
                    force=force
                )
                if m_ok:
                    action = "verified (dry-run)" if dry_run else "uploaded"
                    logger.info(f"✅ Normal Video 1 {action} successfully!")
                else:
                    logger.error("❌ Normal Video 1 failed during generation/upload. Continuing to remaining jobs.")
            except Exception as e:
                logger.error(f"❌ Normal Video 1 encountered isolated exception: {e}", exc_info=True)
        else:
            logger.info("⏩ Normal Video 1 (morning slot) already completed today. Skipping.")

        # Step B: Normal Video 2 (Evening Slot)
        if not evening_done or force:
            logger.info("\n▶️ Processing Today's Normal Video 2 (Slot: evening)...")
            try:
                e_ok = run_pipeline(
                    slot="evening",
                    privacy_status=target_privacy,
                    dry_run=dry_run,
                    force=force
                )
                if e_ok:
                    action = "verified (dry-run)" if dry_run else "uploaded"
                    logger.info(f"✅ Normal Video 2 {action} successfully!")
                else:
                    logger.error("❌ Normal Video 2 failed during generation/upload. Continuing to remaining jobs.")
            except Exception as e:
                logger.error(f"❌ Normal Video 2 encountered isolated exception: {e}", exc_info=True)
        else:
            logger.info("⏩ Normal Video 2 (evening slot) already completed today. Skipping.")

        # Step C: Cartoon Video 3 (Cartoon Slot) - Complete Failure Isolation
        if not cartoon_done or force:
            logger.info("\n▶️ Processing Today's Cartoon Animation Video (Video 3)...")
            try:
                c_ok = run_daily_cartoon(
                    dry_run=dry_run,
                    privacy_status=target_privacy,
                    force=force
                )
                if c_ok:
                    action = "verified (dry-run)" if dry_run else "uploaded"
                    logger.info(f"✅ Cartoon Video 3 {action} successfully!")
                else:
                    logger.error("❌ Cartoon Video 3 failed. Inspect cartoon logs.")
            except Exception as e:
                logger.error(f"❌ Cartoon Video 3 encountered isolated exception: {e}", exc_info=True)
        else:
            logger.info("⏩ Cartoon Video 3 already completed today. Skipping.")

        # Step D: Final Structured Daily Audit & Reporting
        final_norm = len(get_today_normal_uploads(today_str))
        final_cart = len(get_today_cartoon_uploads(today_str))
        final_total = final_norm + final_cart

        summary = job_tracker.get_daily_summary(today_str)

        logger.info("\n" + "=" * 70)
        logger.info(f"📋 FUN LEARNING KIDS — MASTER DAILY SUMMARY ({today_str})")
        logger.info("=" * 70)

        slots_display = [
            ("Slot 1 (Normal Video 1 - morning)", "morning"),
            ("Slot 2 (Normal Video 2 - evening)", "evening"),
            ("Slot 3 (Cartoon Video 3 - cartoon)", "cartoon")
        ]

        for label, s_key in slots_display:
            j = summary.get(s_key, {})
            state = j.get("state", "pending").upper()
            v_id = j.get("video_id") or "N/A"
            v_url = j.get("video_url") or "N/A"
            t_status = j.get("thumbnail_status") or "none"
            err = j.get("error_message")

            if state == "UPLOADED":
                logger.info(f"  {label}:")
                logger.info(f"     Status: UPLOADED | Video ID: {v_id}")
                logger.info(f"     URL: {v_url}")
                logger.info(f"     Thumbnail: {t_status}")
            elif dry_run and state == "DRY_RUN_SUCCESS":
                logger.info(f"  {label}:")
                logger.info(f"     Status: DRY_RUN_SUCCESS (Local render & QA verified)")
                logger.info(f"     File: {j.get('video_path')}")
            elif state == "NEEDS_MANUAL_REVIEW":
                logger.warning(f"  {label}:")
                logger.warning(f"     Status: NEEDS VERIFICATION (Upload outcome ambiguous)")
                logger.warning(f"     Details: {err or 'Timeout occurred on final upload response'}")
            else:
                logger.info(f"  {label}:")
                logger.info(f"     Status: {state} | Error: {err or 'Pending or uncompleted'}")

        logger.info("-" * 70)
        logger.info(f"🎯 Daily Result: {final_total}/3 confirmed uploads on YouTube.")
        logger.info(f"   Normal Videos: {final_norm}/2 | Cartoon Video: {final_cart}/1")
        logger.info("=" * 70)

        all_completed = (final_total >= 3) or (dry_run and final_norm >= 2 and final_cart >= 1)

        if all_completed:
            success_msg = f"All 3 daily videos for {today_str} have been successfully produced and uploaded!"
            logger.info(f"🎉🎉 {success_msg}")
            if not dry_run:
                send_notification("Fun Learning Kids", success_msg)
            return True
        else:
            pending_count = 3 - final_total
            logger.warning(f"⚠️ {pending_count} video(s) still pending for today ({today_str}). Will resume on next trigger.")
            return False

    finally:
        # Always release the process lock
        job_tracker.release_process_lock()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fun Learning Kids Daily Manager (3 Videos/Day)")
    parser.add_argument("--privacy", default=None, choices=["public", "unlisted", "private"])
    parser.add_argument("--force", action="store_true", help="Force re-execution of all slots")
    parser.add_argument("--dry-run", action="store_true", help="Run full daily manager in dry-run mode without uploading")
    args = parser.parse_args()

    run_daily_automation(privacy_status=args.privacy, force=args.force, dry_run=args.dry_run)
