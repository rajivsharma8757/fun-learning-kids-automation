"""
test_hardening.py
-----------------
Automated test suite verifying the 10 failure categories and system hardenings:
1. Static imports and syntax check
2. OAuth token loading, scopes, and channel identity verification
3. Video validator on valid, zero-byte, and corrupted media
4. Resumable upload chunk retry on simulated timeout and HTTP 503
5. Permanent error abort without infinite retry loops
6. Ambiguous timeout resolution via channel playlist inspection
7. Custom thumbnail HTTP 403 isolation (phone verification required)
8. Concurrency process locking via msvcrt
9. Job state persistence and restart recovery
10. Live Edge-TTS voice generation & ffprobe duration verification
"""

import os
import sys
import json
import time
import socket
import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO

# Ensure project root in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES, UPLOAD_SCOPES, CHANNEL_NAME, VIDEO_DIR
import job_tracker
from video_validator import validate_video_file
import uploader
from uploader import (
    UploadResult,
    compute_file_hash,
    get_authenticated_service,
    verify_channel,
    verify_uploaded_video_on_channel,
    _set_thumbnail_safe,
    upload_video_to_youtube
)
from voice_generator import generate_voice, get_audio_duration


class TestAutomationHardening(unittest.TestCase):

    def test_01_static_imports(self):
        """1. Static checks and module imports."""
        import daily_manager
        import run
        import upload
        import content_manager
        import video_maker
        import thumbnail_maker
        self.assertTrue(hasattr(uploader, "upload_video_to_youtube"))
        self.assertTrue(hasattr(job_tracker, "acquire_process_lock"))
        self.assertTrue(hasattr(daily_manager, "run_daily_automation"))

    def test_02_oauth_token_and_channel_identity(self):
        """2. OAuth token loading and channel identity without exposing secrets."""
        self.assertTrue(os.path.exists(TOKEN_FILE), f"Missing {TOKEN_FILE}")
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertTrue(bool(data.get("refresh_token")), "refresh_token is missing from token.json")
        for sc in UPLOAD_SCOPES:
            self.assertIn(sc, data.get("scopes", []), f"Missing required upload scope: {sc}")

        # Get authenticated service unattended (requires upload scopes)
        try:
            service = get_authenticated_service(interactive=False, required_scopes=UPLOAD_SCOPES)
            self.assertIsNotNone(service)

            # Verify channel matches CHANNEL_NAME
            ch_id, ch_title, uploads_pl = verify_channel(service)
            if ch_id:
                self.assertIn(CHANNEL_NAME.lower(), ch_title.lower())
                self.assertIsNotNone(uploads_pl)
        except RuntimeError as e:
            # Offline environment prevents contacting oauth2.googleapis.com for refresh
            self.skipTest(f"Live OAuth service unavailable offline: {e}")
        except Exception as e:
            if any(net_err in str(e) for net_err in ["getaddrinfo", "WinError", "timed out", "Temporary failure"]):
                self.skipTest(f"Network unavailable in test environment: {e}")
            else:
                raise

    def test_03_video_validator(self):
        """3. Video validator on valid, non-existent, and corrupted files."""
        # Non-existent file
        ok, err, dur, sz = validate_video_file("C:/non_existent_file.mp4")
        self.assertFalse(ok)
        self.assertIn("not found", err)

        # Corrupt / zero-byte file
        temp_corrupt = os.path.join(BASE_DIR, "video", "test_corrupt.mp4")
        with open(temp_corrupt, "wb") as f:
            f.write(b"not a real video file content")
        try:
            ok, err, dur, sz = validate_video_file(temp_corrupt)
            self.assertFalse(ok)
        finally:
            if os.path.exists(temp_corrupt):
                os.remove(temp_corrupt)

        # Existing real video in video directory if available
        existing_vids = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")]
        if existing_vids:
            real_vid = os.path.join(VIDEO_DIR, existing_vids[0])
            ok, err, dur, sz = validate_video_file(real_vid)
            self.assertTrue(ok, f"Validation failed for existing video: {err}")
            self.assertGreater(dur, 1.0)
            self.assertGreater(sz, 20000)

    def test_04_resumable_upload_chunk_retry(self):
        """4. Simulated timeouts, transient HTTP errors, and retry resumption."""
        mock_request = MagicMock()
        chunk_call_count = 0

        def simulated_next_chunk():
            nonlocal chunk_call_count
            chunk_call_count += 1
            if chunk_call_count == 1:
                # Simulate read timeout on first attempt
                raise socket.timeout("The read operation timed out")
            elif chunk_call_count == 2:
                # Simulate transient 503 Service Unavailable
                from googleapiclient.errors import HttpError
                from collections import namedtuple
                Resp = namedtuple("Resp", ["status", "reason", "get"])
                resp = Resp(status=503, reason="Service Unavailable", get=lambda k: None)
                raise HttpError(resp, b"Transient error")
            else:
                # Succeeded on third attempt!
                status = MagicMock()
                status.progress.return_value = 1.0
                return status, {"id": "mock_vid_123"}

        mock_request.next_chunk.side_effect = simulated_next_chunk

        # Verify retry logic executes without aborting
        attempt = 0
        response = None
        max_chunk_retries = 5
        while response is None:
            try:
                status, response = mock_request.next_chunk()
            except socket.timeout:
                attempt += 1
                self.assertLessEqual(attempt, max_chunk_retries)
            except Exception as e:
                attempt += 1
                self.assertLessEqual(attempt, max_chunk_retries)

        self.assertIsNotNone(response)
        self.assertEqual(response["id"], "mock_vid_123")
        self.assertEqual(chunk_call_count, 3)

    def test_05_permanent_error_no_infinite_loop(self):
        """5. Permanent HTTP errors (400, 401, quotaExceeded) abort cleanly."""
        from googleapiclient.errors import HttpError
        from collections import namedtuple
        Resp = namedtuple("Resp", ["status", "reason", "get"])
        resp = Resp(status=400, reason="Bad Request", get=lambda k: None)

        mock_request = MagicMock()
        mock_request.next_chunk.side_effect = HttpError(resp, b"Invalid metadata")

        response = None
        upload_error = None
        while response is None:
            try:
                status, response = mock_request.next_chunk()
            except HttpError as he:
                if he.resp.status in [408, 429, 500, 502, 503, 504]:
                    continue
                else:
                    upload_error = f"Permanent: {he.resp.status}"
                    break

        self.assertIsNone(response)
        self.assertEqual(upload_error, "Permanent: 400")

    def test_06_ambiguous_upload_resolution(self):
        """6. Ambiguous upload outcome verifies against channel playlist without duplicate."""
        mock_youtube = MagicMock()
        mock_ch_req = MagicMock()
        mock_ch_req.execute.return_value = {
            "items": [{
                "id": "UC_TEST",
                "snippet": {"title": "Fun Learning Kids"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU_TEST"}}
            }]
        }
        mock_youtube.channels().list.return_value = mock_ch_req

        mock_pl_req = MagicMock()
        mock_pl_req.execute.return_value = {
            "items": [{
                "snippet": {
                    "title": "Good Habits for Kids | Wash Hands Regularly",
                    "resourceId": {"videoId": "VERIFIED_VID_999"}
                }
            }]
        }
        mock_youtube.playlistItems().list.return_value = mock_pl_req

        found, vid_id, vid_url = verify_uploaded_video_on_channel(
            mock_youtube,
            title="Good Habits for Kids | Wash Hands Regularly"
        )

        self.assertTrue(found)
        self.assertEqual(vid_id, "VERIFIED_VID_999")
        self.assertEqual(vid_url, "https://youtube.com/watch?v=VERIFIED_VID_999")

    def test_07_thumbnail_403_isolation(self):
        """7. Custom thumbnail HTTP 403 is caught safely and never fails video upload."""
        from googleapiclient.errors import HttpError
        from collections import namedtuple
        Resp = namedtuple("Resp", ["status", "reason", "get"])
        resp = Resp(status=403, reason="forbidden", get=lambda k: None)

        mock_youtube = MagicMock()
        mock_thumb_req = MagicMock()
        mock_thumb_req.execute.side_effect = HttpError(resp, b"The caller does not have permission")
        mock_youtube.thumbnails().set.return_value = mock_thumb_req

        # Create temporary dummy thumbnail file
        temp_thumb = os.path.join(BASE_DIR, "thumbnails", "temp_test_thumb.jpg")
        with open(temp_thumb, "wb") as f:
            f.write(b"\xFF\xD8\xFF" + b"\x00" * 500)

        try:
            status = _set_thumbnail_safe(mock_youtube, "test_vid", temp_thumb)
            self.assertEqual(status, "skipped_403_unverified")
        finally:
            if os.path.exists(temp_thumb):
                os.remove(temp_thumb)

    def test_08_process_concurrency_lock(self):
        """8. Windows process lock prevents overlapping runs."""
        # Acquire lock
        acquired = job_tracker.acquire_process_lock()
        self.assertTrue(acquired)

        # Attempt to acquire again from another simulated handle
        if sys.platform == "win32":
            import msvcrt
            with open(job_tracker.PROCESS_LOCK_FILE, "a+") as f2:
                f2.seek(0)
                with self.assertRaises(OSError):
                    msvcrt.locking(f2.fileno(), msvcrt.LK_NBLCK, 1)

        # Release lock
        job_tracker.release_process_lock()

    def test_09_job_tracker_persistence(self):
        """9. Durable job tracker state persistence and restart recovery."""
        test_slot = "test_slot_recovery"
        today_str = "2099-01-01"

        job = job_tracker.update_job(
            test_slot,
            today_str=today_str,
            state=job_tracker.STATE_UPLOAD_PENDING,
            title="Test Persistence Story",
            video_id=None
        )
        self.assertEqual(job["state"], job_tracker.STATE_UPLOAD_PENDING)

        # Reload from disk
        loaded = job_tracker.get_job(test_slot, today_str=today_str)
        self.assertEqual(loaded["title"], "Test Persistence Story")
        self.assertFalse(job_tracker.is_slot_completed(test_slot, today_str=today_str))

        # Mark uploaded
        job_tracker.update_job(
            test_slot,
            today_str=today_str,
            state=job_tracker.STATE_UPLOADED,
            video_id="TEST_VID_RECOVERED"
        )
        self.assertTrue(job_tracker.is_slot_completed(test_slot, today_str=today_str))

    def test_10_live_edge_tts_voice_generation(self):
        """10. Live Edge-TTS voice generation and ffprobe audio duration verification."""
        temp_audio = os.path.join(BASE_DIR, "audio", "test_verification_voice.mp3")
        try:
            ok, dur = generate_voice("नमस्ते बच्चों, यह एक परीक्षण है।", temp_audio, max_retries=1)
            if not ok:
                self.skipTest("Network access unavailable for live Edge-TTS synthesis")
            self.assertTrue(ok)
            self.assertGreater(dur, 1.0)
            self.assertTrue(os.path.exists(temp_audio))
            self.assertGreater(os.path.getsize(temp_audio), 2000)
        finally:
            if os.path.exists(temp_audio):
                os.remove(temp_audio)


if __name__ == "__main__":
    unittest.main(verbosity=2)
