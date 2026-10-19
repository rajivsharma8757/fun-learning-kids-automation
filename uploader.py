"""
uploader.py
-----------
Production-grade YouTube Upload Engine for Fun Learning Kids.

Features:
1. Resumable chunked upload with exponential backoff and jitter.
2. Robust recovery from transient network drops, socket timeouts, and HTTP 5xx/429.
3. Ambiguous upload resolution (queries channel uploads playlist to verify if YouTube received the video).
4. Duplicate upload prevention via SHA-256, filename, and channel upload history.
5. Independent custom thumbnail upload with graceful handling of HTTP 403 (unverified channel).
6. Pre-flight video integrity validation via ffprobe.
7. Unattended OAuth refresh with explicit handling of invalid_grant and revoked tokens.
8. Verification of authenticated channel identity.
"""

import os
import sys
import json
import time
import socket
import random
import hashlib
import logging
from datetime import datetime, timezone, timedelta

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from config import (
    CREDENTIALS_FILE, TOKEN_FILE, SCOPES, UPLOAD_SCOPES,
    UPLOADS_HISTORY_FILE, YOUTUBE_CATEGORY_ID,
    YOUTUBE_MADE_FOR_KIDS, DEFAULT_PRIVACY_STATUS,
    CHANNEL_NAME, LEGACY_PROTECTED_CHANNEL_ID,
    ALLOW_LEGACY_CHANNEL_UPLOADS, ACTIVE_PROFILE_NAME,
    PROFILE_NANHE_SEEKHO, PROFILE_FUN_LEARNING
)
from video_validator import validate_video_file
import job_tracker

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger("kids_automation")

# Transient errors that can be retried during chunked upload
TRANSIENT_HTTP_STATUSES = {408, 429, 500, 502, 503, 504}
TRANSIENT_NETWORK_ERRORS = (
    socket.timeout,
    TimeoutError,
    ConnectionError,
    OSError
)


class UploadResult(tuple):
    """
    Backward-compatible tuple (success, video_id, video_url) that also
    exposes rich metadata attributes: thumbnail_status, error, is_duplicate.
    """
    def __new__(cls, success, video_id, video_url, thumbnail_status="none", error=None, is_duplicate=False):
        return super().__new__(cls, (success, video_id, video_url))

    def __init__(self, success, video_id, video_url, thumbnail_status="none", error=None, is_duplicate=False):
        self.success = success
        self.video_id = video_id
        self.video_url = video_url
        self.thumbnail_status = thumbnail_status
        self.error = error
        self.is_duplicate = is_duplicate


def compute_file_hash(filepath):
    """Computes SHA-256 of video file to uniquely identify it."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_channel(youtube):
    """
    Verifies that the authenticated YouTube account corresponds to the intended channel.
    Returns (channel_id, channel_title, uploads_playlist_id).
    """
    try:
        resp = youtube.channels().list(mine=True, part="snippet,contentDetails").execute()
        items = resp.get("items", [])
        if not items:
            logger.warning("⚠️ Authenticated account has no YouTube channel associated.")
            return None, None, None

        item = items[0]
        ch_id = item["id"]
        ch_title = item["snippet"].get("title", "")
        uploads_pl = item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")

        logger.info(f"📺 Authenticated Channel: '{ch_title}' (ID: {ch_id})")

        if CHANNEL_NAME and CHANNEL_NAME.lower() not in ch_title.lower():
            logger.warning(
                f"⚠️ Note: Authorized channel '{ch_title}' differs from expected '{CHANNEL_NAME}'."
            )

        return ch_id, ch_title, uploads_pl
    except Exception as e:
        logger.warning(f"⚠️ Could not verify channel details: {e}")
        return None, None, None


def check_channel_upload_safety(youtube):
    """
    Enforces two-layer upload safeguards:
    Layer 1: Hard block against legacy channel UCcOA6heUaTbOUnx7ERF23Gw (Fun Learning Kids).
    Layer 2: Verification of authenticated channel identity to prevent cross-channel contamination.
    """
    ch_id, ch_title, uploads_pl = verify_channel(youtube)
    if not ch_id:
        logger.warning("⚠️ Could not verify channel identity from YouTube API.")
        return ch_id, ch_title, uploads_pl

    # Layer 1: Strict lock against old channel
    if ch_id == LEGACY_PROTECTED_CHANNEL_ID:
        if not ALLOW_LEGACY_CHANNEL_UPLOADS:
            err = (
                f"🛑 CRITICAL SAFETY INTERVENTION: Attempted upload to protected legacy channel '{ch_title}' (ID: {ch_id}).\n"
                f"Uploads to Fun Learning Kids are STRICTLY LOCKED to preserve the existing channel!\n"
                f"Please authorize the new 'Nanhe Seekho Club' account via 'python auth_setup.py'."
            )
            logger.critical(err)
            raise RuntimeError(err)

    # Layer 2: Profile mismatch check
    if ACTIVE_PROFILE_NAME == PROFILE_NANHE_SEEKHO:
        if ch_title and "fun learning kids" in ch_title.lower():
            err = (
                f"🛑 CRITICAL SAFETY INTERVENTION: Active profile is '{PROFILE_NANHE_SEEKHO}' but authenticated channel is '{ch_title}'!\n"
                f"Halting upload immediately to prevent uploading to the wrong channel."
            )
            logger.critical(err)
            raise RuntimeError(err)

    return ch_id, ch_title, uploads_pl



def get_authenticated_service(interactive=False, required_scopes=None):
    """
    Retrieves or refreshes YouTube API credentials.
    Uses token.json to run unattended.
    If token is expired or within 10 minutes of expiry, proactively refreshes it.
    Catches invalid_grant / revoked tokens and gives actionable instructions.

    required_scopes: Scopes needed for this operation. Defaults to UPLOAD_SCOPES
                     so daily video uploads succeed even if analytics scope is pending.
    """
    creds = None
    target_scopes = required_scopes or UPLOAD_SCOPES

    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"Missing OAuth credentials file at: {CREDENTIALS_FILE}\n"
            f"Please place your Google Cloud OAuth client secret at this location."
        )

    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as tf:
                tok_data = json.load(tf)
            tok_scopes = set(tok_data.get("scopes", []))
            if not all(s in tok_scopes for s in target_scopes):
                logger.warning(f"⚠️ Saved token.json is missing required scopes ({target_scopes}). Re-authorization required.")
                creds = None
            else:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, list(tok_scopes))
        except Exception as e:
            logger.warning(f"⚠️ Warning reading {TOKEN_FILE}: {e}")
            creds = None

    # Check validity and proactive refresh
    needs_refresh = False
    if creds:
        if not creds.valid:
            needs_refresh = True
        elif creds.expiry:
            # Refresh if expires within 10 minutes
            now_utc = datetime.now(timezone.utc)
            expiry_utc = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry.tzinfo is None else creds.expiry
            if expiry_utc - now_utc < timedelta(minutes=10):
                needs_refresh = True

    if creds and needs_refresh and creds.refresh_token:
        logger.info("🔄 Refreshing OAuth token automatically...")
        try:
            creds.refresh(Request())
            # Save refreshed token atomically
            temp_tok = TOKEN_FILE + ".tmp"
            with open(temp_tok, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            if os.path.exists(TOKEN_FILE):
                os.replace(temp_tok, TOKEN_FILE)
            else:
                os.rename(temp_tok, TOKEN_FILE)
            logger.info("✅ Token refreshed and saved successfully.")
        except RefreshError as re:
            logger.error(f"❌ YouTube OAuth refresh failed (token expired or revoked): {re}")
            creds = None
        except Exception as e:
            logger.warning(f"⚠️ Auto-refresh warning: {e}")
            # If creds is still somehow usable, continue, otherwise nullify
            if not creds.valid:
                creds = None

    if not creds or not creds.valid:
        if not interactive:
            raise RuntimeError(
                f"Authentication required: No valid OAuth token found at {TOKEN_FILE}.\n"
                f"The token may have expired or been revoked.\n"
                f"ACTION REQUIRED: Run 'python auth_setup.py' interactively once to authorize."
            )
        logger.info("🔑 Opening browser for YouTube OAuth authorization...")
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, target_scopes)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        logger.info(f"✅ Authorization successful! Saved reusable token to {TOKEN_FILE}")

    # Build client with reasonable timeout configuration
    socket.setdefaulttimeout(120)
    service = googleapiclient.discovery.build("youtube", "v3", credentials=creds, cache_discovery=False)
    return service


def load_upload_history():
    if os.path.exists(UPLOADS_HISTORY_FILE):
        try:
            with open(UPLOADS_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def record_upload_success(record):
    history = load_upload_history()
    history.append(record)
    os.makedirs(os.path.dirname(UPLOADS_HISTORY_FILE), exist_ok=True)
    temp_hist = UPLOADS_HISTORY_FILE + ".tmp"
    with open(temp_hist, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    if os.path.exists(UPLOADS_HISTORY_FILE):
        os.replace(temp_hist, UPLOADS_HISTORY_FILE)
    else:
        os.rename(temp_hist, UPLOADS_HISTORY_FILE)


def is_already_uploaded(video_path):
    """
    Checks if a video has already been uploaded to prevent duplicate uploads.
    Matches by filename, SHA-256 hash, or job state.
    """
    if not os.path.exists(video_path):
        return False, None

    filename = os.path.basename(video_path)
    file_hash = compute_file_hash(video_path)
    history = load_upload_history()

    for item in history:
        if item.get("file_hash") == file_hash or item.get("filename") == filename:
            if item.get("video_id"):
                return True, item
    return False, None


def is_legacy_upload(video_path):
    """
    Checks if a video was already uploaded to the legacy Fun Learning Kids channel.
    Cross-checks the legacy uploads.json and catalog to prevent un-rebranded uploads.
    """
    if not os.path.exists(video_path):
        return False, None

    filename = os.path.basename(video_path)
    file_hash = compute_file_hash(video_path)

    legacy_uploads_file = os.path.join(os.path.dirname(UPLOADS_HISTORY_FILE), "uploads.json")
    if os.path.exists(legacy_uploads_file) and legacy_uploads_file != UPLOADS_HISTORY_FILE:
        try:
            with open(legacy_uploads_file, "r", encoding="utf-8") as f:
                leg_hist = json.load(f)
            for item in leg_hist:
                if (file_hash and item.get("file_hash") == file_hash) or item.get("filename") == filename:
                    if item.get("video_id"):
                        return True, item
        except Exception:
            pass

    return False, None



def verify_uploaded_video_on_channel(youtube, title, lookback_hours=12):
    """
    Queries the channel's uploads playlist (1 quota unit) to verify if a video
    with the matching title was successfully received by YouTube within the lookback window.
    This resolves ambiguous upload states (e.g. read timeout on final chunk).
    """
    try:
        ch_id, ch_title, uploads_pl = verify_channel(youtube)
        if not uploads_pl:
            return False, None, None

        resp = youtube.playlistItems().list(
            playlistId=uploads_pl,
            part="snippet,status",
            maxResults=10
        ).execute()

        clean_target = "".join(c for c in title.lower() if c.isalnum() or c.isspace()).strip()

        for item in resp.get("items", []):
            snip = item.get("snippet", {})
            v_title = snip.get("title", "")
            clean_v = "".join(c for c in v_title.lower() if c.isalnum() or c.isspace()).strip()

            # Check for title match
            if clean_target and (clean_target in clean_v or clean_v in clean_target):
                v_id = snip.get("resourceId", {}).get("videoId")
                if v_id:
                    v_url = f"https://youtube.com/watch?v={v_id}"
                    logger.info(f"🔎 Found matching video on channel uploads playlist: '{v_title}' (ID: {v_id})")
                    return True, v_id, v_url

        return False, None, None
    except Exception as e:
        logger.warning(f"⚠️ Could not query channel playlist to verify upload: {e}")
        return False, None, None


def check_duplicate_title(title, history=None):
    """
    Checks if a title has already been used in previous uploads.
    Inspects both uploads.json and historical all_youtube_videos_audit.json.
    Returns (is_duplicate: bool, previous_count: int, previous_record: dict or None)
    """
    if history is None:
        history = list(load_upload_history())
        audit_file = os.path.join(os.path.dirname(UPLOADS_HISTORY_FILE), "all_youtube_videos_audit.json")
        if os.path.exists(audit_file):
            try:
                with open(audit_file, "r", encoding="utf-8") as af:
                    history.extend(json.load(af))
            except Exception:
                pass
    clean_target = " ".join(title.lower().split())
    matches = [
        u for u in history
        if " ".join(u.get("title", "").lower().split()) == clean_target
    ]
    if matches:
        return True, len(matches), matches[-1]
    return False, 0, None


def check_video_processing_status(youtube, video_id, max_wait_sec=10):
    """
    Checks remote processing status on YouTube after upload.
    Verifies YouTube accepted the file and did not reject it immediately
    (e.g., corrupted container, bad audio codec, duplicate upload).
    Returns (upload_status: str, rejection_reason: str or None, processing_status: str).
    """
    start = time.time()
    while time.time() - start < max_wait_sec:
        try:
            res = youtube.videos().list(
                part="status,processingDetails",
                id=video_id
            ).execute()
            items = res.get("items", [])
            if not items:
                time.sleep(2)
                continue

            item = items[0]
            status_obj = item.get("status", {})
            proc_obj = item.get("processingDetails", {})

            upload_status = status_obj.get("uploadStatus", "unknown")
            rejection_reason = status_obj.get("rejectionReason")
            proc_status = proc_obj.get("processingStatus", "unknown")

            if upload_status == "rejected":
                logger.error(f"❌ Video {video_id} was rejected by YouTube: {rejection_reason}")
                return upload_status, rejection_reason, proc_status

            if upload_status == "processed" or proc_status == "succeeded":
                logger.info(f"✅ Video processing confirmed on YouTube (status: {upload_status}, proc: {proc_status})")
                return upload_status, None, proc_status

            time.sleep(2.5)
        except Exception as e:
            logger.warning(f"⚠️ Could not check video processing status: {e}")
            break

    logger.info(f"ℹ️ Video {video_id} is queued/processing on YouTube servers.")
    return "uploaded", None, "processing"


def _set_thumbnail_safe(youtube, video_id, thumbnail_path):
    """
    Uploads custom thumbnail with isolated error handling.
    If 403 Forbidden (account requires phone verification), logs a warning,
    preserves local file, and returns 'skipped_403_unverified'.
    Never causes video upload to fail.
    """
    if not thumbnail_path or not os.path.exists(thumbnail_path):
        return "none"

    logger.info(f"🖼️ Setting custom video thumbnail for video {video_id}...")
    media = None
    try:
        media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=media
        ).execute()
        logger.info("✅ Custom thumbnail uploaded successfully!")
        return "uploaded"
    except HttpError as he:
        if he.resp.status == 403:
            logger.warning(
                "⚠️ Note: Custom thumbnail could not be set (HTTP 403 Forbidden).\n"
                "   YouTube requires phone verification on this channel account to enable custom thumbnails.\n"
                "   The video upload succeeded unaffected with the default video frame."
            )
            return "skipped_403_unverified"
        else:
            logger.warning(f"⚠️ Thumbnail upload HttpError ({he.resp.status}): {he}")
            return f"failed_http_{he.resp.status}"
    except Exception as e:
        logger.warning(f"⚠️ Thumbnail upload exception: {e}")
        return f"failed: {str(e)[:60]}"
    finally:
        if media is not None:
            try:
                if hasattr(media, "_fd") and media._fd:
                    media._fd.close()
            except Exception:
                pass


def upload_video_to_youtube(video_path, metadata, thumbnail_path=None, privacy_status=None, interactive=False, slot=None):
    """
    Uploads a video to YouTube with complete metadata and COPPA compliance.
    Features:
    - Pre-flight video validation (ffprobe)
    - Resumable chunked upload with exponential backoff & jitter for transient errors
    - Ambiguous outcome verification against channel playlist
    - Independent custom thumbnail upload
    - Atomic history and job state persistence
    - Returns UploadResult (compatible with 3-tuple unpacking)
    """
    # 1. Pre-flight Video Integrity Check
    is_valid, val_err, duration, size_bytes = validate_video_file(video_path)
    if not is_valid:
        err_msg = f"Video validation failed: {val_err}"
        logger.error(f"❌ {err_msg}")
        if slot:
            job_tracker.update_job(slot, state=job_tracker.STATE_FAILED, error_message=err_msg)
        return UploadResult(False, None, None, error=err_msg)

    # 2. Check Duplicate Upload
    already_done, record = is_already_uploaded(video_path)
    if already_done:
        vid_id = record.get("video_id")
        url = f"https://youtube.com/watch?v={vid_id}"
        logger.info(f"🛑 Video already uploaded previously! Skipping duplicate upload.")
        logger.info(f"🎥 Existing Video Link: {url}")
        if slot:
            job_tracker.update_job(
                slot,
                state=job_tracker.STATE_UPLOADED,
                video_id=vid_id,
                video_url=url,
                file_hash=record.get("file_hash"),
                video_path=video_path
            )
        return UploadResult(True, vid_id, url, thumbnail_status="already_uploaded", is_duplicate=True)

    # 2b. Check Duplicate Title Warning
    title = metadata.get("title", "")
    is_dupe_title, dupe_count, last_dupe = check_duplicate_title(title)
    if is_dupe_title:
        logger.warning(
            f"⚠️ Duplicate title warning: Title '{title}' was uploaded {dupe_count} time(s) previously "
            f"(last ID: {last_dupe.get('video_id')}). Ensure dynamic episode numbering is applied."
        )

    # 2c. Check Un-rebranded Legacy Channel Video (Fun Learning Kids)
    if ACTIVE_PROFILE_NAME == PROFILE_NANHE_SEEKHO and not metadata.get("allow_repurposed_legacy"):
        is_leg, leg_rec = is_legacy_upload(video_path)
        if is_leg:
            err_msg = (
                f"🛑 Video '{os.path.basename(video_path)}' was previously uploaded to legacy channel "
                f"(Video ID: {leg_rec.get('video_id')}). Un-rebranded re-uploads are blocked.\n"
                f"Please re-render this video with '{CHANNEL_NAME}' branding and outro."
            )
            logger.error(f"❌ {err_msg}")
            if slot:
                job_tracker.update_job(slot, state=job_tracker.STATE_FAILED, error_message=err_msg)
            return UploadResult(False, None, None, error=err_msg)

    # 3. Authenticate YouTube Client
    try:
        youtube = get_authenticated_service(interactive=interactive)
    except Exception as e:
        err_msg = f"YouTube authentication error: {e}"
        logger.error(f"❌ {err_msg}")
        if slot:
            job_tracker.update_job(slot, state=job_tracker.STATE_FAILED, error_message=err_msg)
        return UploadResult(False, None, None, error=err_msg)

    # 3b. Verify Channel Upload Safety (Two-Layer Safeguard)
    try:
        ch_id, ch_title, uploads_pl = check_channel_upload_safety(youtube)
    except Exception as e:
        err_msg = f"Channel upload safety check failed: {e}"
        logger.error(f"❌ {err_msg}")
        if slot:
            job_tracker.update_job(slot, state=job_tracker.STATE_FAILED, error_message=err_msg)
        return UploadResult(False, None, None, error=err_msg)

    # 4. Prepare Metadata & State
    privacy = privacy_status or DEFAULT_PRIVACY_STATUS
    title = metadata.get("title", f"Kids Learning Video | {CHANNEL_NAME}")
    description = metadata.get("description", f"Welcome to {CHANNEL_NAME}!")
    tags = metadata.get("tags", ["kids", "learning", CHANNEL_NAME.lower()])
    topic = metadata.get("topic", "general")

    file_hash = compute_file_hash(video_path)

    if slot:
        job_tracker.update_job(
            slot,
            state=job_tracker.STATE_UPLOADING,
            title=title,
            topic=topic,
            video_path=video_path,
            file_hash=file_hash,
            privacy=privacy
        )

    logger.info("📤 Uploading video to YouTube (Resumable)...")
    logger.info(f"   Title: {title}")
    logger.info(f"   Privacy: {privacy}")
    logger.info(f"   Made For Kids: {YOUTUBE_MADE_FOR_KIDS}")
    logger.info(f"   Size: {size_bytes:,} bytes | Duration: {duration:.2f}s")

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": YOUTUBE_CATEGORY_ID
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": YOUTUBE_MADE_FOR_KIDS
        }
    }

    # 5. Execute Resumable Upload with Chunk Retries
    max_chunk_retries = 10
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        chunksize=1024 * 1024 * 4,  # 4MB chunks
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    upload_error = None
    attempt = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                logger.info(f"   Upload progress: {int(status.progress() * 100)}%")
            # Successful chunk resets retry counter
            attempt = 0
        except HttpError as he:
            status_code = he.resp.status
            if status_code in TRANSIENT_HTTP_STATUSES and attempt < max_chunk_retries:
                attempt += 1
                retry_after = he.resp.get("retry-after")
                delay = float(retry_after) if retry_after else (2 ** min(attempt, 6)) + random.uniform(0.5, 1.5)
                logger.warning(
                    f"⚠️ Transient HTTP {status_code} during chunk upload (attempt {attempt}/{max_chunk_retries}). "
                    f"Resuming in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                upload_error = f"YouTube API HttpError {status_code}: {he}"
                logger.error(f"❌ Permanent upload HttpError: {upload_error}")
                break
        except TRANSIENT_NETWORK_ERRORS as net_err:
            if attempt < max_chunk_retries:
                attempt += 1
                delay = (2 ** min(attempt, 6)) + random.uniform(0.5, 1.5)
                logger.warning(
                    f"⚠️ Transient network/timeout error during chunk upload ({net_err.__class__.__name__}: {net_err}) "
                    f"(attempt {attempt}/{max_chunk_retries}). Resuming in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                upload_error = f"Network retries exhausted: {net_err}"
                logger.error(f"❌ {upload_error}")
                break
        except Exception as e:
            upload_error = f"Unexpected upload exception: {e}"
            logger.error(f"❌ {upload_error}")
            break

    # 6. Ambiguous Outcome Resolution
    video_id = None
    if response is not None:
        video_id = response.get("id")
    else:
        # If response was None, did YouTube receive the video anyway despite client timeout?
        logger.info("🔎 Verifying whether video reached YouTube channel despite client disconnect/timeout...")
        found, v_id, v_url = verify_uploaded_video_on_channel(youtube, title)
        if found:
            logger.info(f"✅ Ambiguous upload verified! Video is present on channel: {v_url}")
            video_id = v_id
        else:
            logger.error(f"❌ Upload could not be completed: {upload_error}")
            if slot:
                job_tracker.update_job(
                    slot,
                    state=job_tracker.STATE_FAILED,
                    error_message=upload_error
                )
            return UploadResult(False, None, None, error=upload_error)

    video_url = f"https://youtube.com/watch?v={video_id}"
    logger.info(f"\n🎉 Upload Confirmed Successful!")
    logger.info(f"🎥 Video Link: {video_url}")

    # 7. Check Remote Video Processing Status
    logger.info("⏳ Checking remote processing status on YouTube...")
    up_status, rej_reason, proc_status = check_video_processing_status(youtube, video_id, max_wait_sec=10)
    if up_status == "rejected":
        rej_msg = f"YouTube rejected uploaded video: {rej_reason}"
        logger.error(f"❌ {rej_msg}")
        if slot:
            job_tracker.update_job(slot, state=job_tracker.STATE_FAILED, error_message=rej_msg)
        return UploadResult(False, video_id, video_url, error=rej_msg)

    # 8. Independent Custom Thumbnail Upload
    thumb_status = _set_thumbnail_safe(youtube, video_id, thumbnail_path)

    # 9. Record in History & Job Tracker
    record_upload_success({
        "timestamp": datetime.now().isoformat(),
        "filename": os.path.basename(video_path),
        "file_hash": file_hash,
        "video_id": video_id,
        "url": video_url,
        "title": title,
        "topic": topic,
        "privacy": privacy,
        "thumbnail_status": thumb_status,
        "upload_status": up_status,
        "processing_status": proc_status
    })

    if slot:
        job_tracker.update_job(
            slot,
            state=job_tracker.STATE_UPLOADED,
            video_id=video_id,
            video_url=video_url,
            file_hash=file_hash,
            video_path=video_path,
            thumbnail_status=thumb_status,
            error_message=None
        )

    return UploadResult(True, video_id, video_url, thumbnail_status=thumb_status)
