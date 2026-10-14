"""
job_tracker.py
--------------
Durable state tracking and process concurrency management for
Fun Learning Kids YouTube Automation.

Durable states:
- PENDING: Job identified for execution
- GENERATING: Video / audio / asset synthesis in progress
- UPLOAD_PENDING: Generation validated and ready for YouTube upload
- UPLOADING: Active upload session to YouTube
- UPLOADED: Confirmed successful YouTube upload with video ID
- FAILED: Job failed (with recorded error details)
- NEEDS_MANUAL_REVIEW: Ambiguous upload state requiring manual inspection
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# Windows process-level locking via msvcrt
if sys.platform == "win32":
    import msvcrt
else:
    msvcrt = None

from config import BASE_DIR, HISTORY_DIR, LOG_DIR

DAILY_JOB_STATES_FILE = os.path.join(HISTORY_DIR, "daily_job_states.json")
PROCESS_LOCK_FILE = os.path.join(LOG_DIR, "daily_manager.lock")

logger = logging.getLogger("kids_automation")

STATE_PENDING = "pending"
STATE_GENERATING = "generating"
STATE_UPLOAD_PENDING = "upload_pending"
STATE_UPLOADING = "uploading"
STATE_UPLOADED = "uploaded"
STATE_FAILED = "failed"
STATE_NEEDS_MANUAL_REVIEW = "needs_manual_review"

_lock_file_handle = None


def acquire_process_lock():
    """
    Acquires an exclusive, non-blocking process lock to prevent
    duplicate simultaneous runs of the automation (e.g. logon trigger + scheduled task).
    Returns True if acquired, False if another process holds the lock.
    """
    global _lock_file_handle
    if msvcrt is None:
        return True

    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        _lock_file_handle = open(PROCESS_LOCK_FILE, "a+")
        _lock_file_handle.seek(0)
        msvcrt.locking(_lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        # Record PID and start timestamp
        _lock_file_handle.truncate(0)
        _lock_file_handle.write(f"PID={os.getpid()} START={datetime.now().isoformat()}\n")
        _lock_file_handle.flush()
        return True
    except (OSError, IOError):
        if _lock_file_handle:
            try:
                _lock_file_handle.close()
            except Exception:
                pass
            _lock_file_handle = None
        return False


def release_process_lock():
    """Releases the process lock file."""
    global _lock_file_handle
    if _lock_file_handle is not None and msvcrt is not None:
        try:
            _lock_file_handle.seek(0)
            msvcrt.locking(_lock_file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            _lock_file_handle.close()
        except Exception:
            pass
        finally:
            _lock_file_handle = None


def _load_job_states():
    if not os.path.exists(DAILY_JOB_STATES_FILE):
        return {}
    try:
        with open(DAILY_JOB_STATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not read {DAILY_JOB_STATES_FILE}: {e}")
        return {}


def _save_job_states(data):
    os.makedirs(os.path.dirname(DAILY_JOB_STATES_FILE), exist_ok=True)
    temp_file = DAILY_JOB_STATES_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Atomic rename/replace on Windows
    if os.path.exists(DAILY_JOB_STATES_FILE):
        os.replace(temp_file, DAILY_JOB_STATES_FILE)
    else:
        os.rename(temp_file, DAILY_JOB_STATES_FILE)


def get_job_id(slot, today_str=None):
    if today_str is None:
        today_str = datetime.now().strftime("%Y-%m-%d")
    return f"{today_str}_{slot}"


def get_job(slot, today_str=None):
    """Retrieves current job record for the given slot today."""
    job_id = get_job_id(slot, today_str)
    states = _load_job_states()
    return states.get(job_id)


def update_job(slot, today_str=None, **kwargs):
    """
    Updates or creates a job record with atomic persistence.
    """
    job_id = get_job_id(slot, today_str)
    states = _load_job_states()
    job = states.get(job_id, {
        "job_id": job_id,
        "slot": slot,
        "date": today_str or datetime.now().strftime("%Y-%m-%d"),
        "state": STATE_PENDING,
        "created_at": datetime.now().isoformat()
    })

    for k, v in kwargs.items():
        job[k] = v
    job["updated_at"] = datetime.now().isoformat()

    states[job_id] = job
    _save_job_states(states)
    return job


def is_slot_completed(slot, today_str=None):
    """
    Checks if this slot has a confirmed uploaded video today.
    Verifies state == UPLOADED and valid video_id.
    """
    job = get_job(slot, today_str)
    if job and job.get("state") == STATE_UPLOADED and job.get("video_id"):
        return True
    return False


def get_daily_summary(today_str=None):
    """
    Returns a consolidated status dictionary for the 3 daily slots:
    'morning' (Video 1), 'evening' (Video 2), 'cartoon' (Video 3).
    """
    if today_str is None:
        today_str = datetime.now().strftime("%Y-%m-%d")

    slots = ["morning", "evening", "cartoon"]
    summary = {}
    states = _load_job_states()

    for s in slots:
        j_id = get_job_id(s, today_str)
        job = states.get(j_id)
        if job:
            summary[s] = job
        else:
            summary[s] = {
                "job_id": j_id,
                "slot": s,
                "date": today_str,
                "state": STATE_PENDING,
                "video_id": None,
                "video_url": None,
                "thumbnail_status": None,
                "error_message": None
            }
    return summary
