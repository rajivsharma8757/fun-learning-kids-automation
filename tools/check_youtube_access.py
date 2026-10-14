"""
tools/check_youtube_access.py
-----------------------------
Safe read-only YouTube channel & API status inspector for Fun Learning Kids.
1. Inspects credentials and token scopes without exposing secrets.
2. Performs read-only channel and video queries.
3. Checks status of stuck/defective video HhotZWPAYaU.
4. Checks YouTube Analytics API status.
5. Never performs uploads, edits, renames, or deletions.
"""

import os
import sys
import json
from datetime import datetime, timezone

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from config import CREDENTIALS_FILE, TOKEN_FILE, UPLOAD_SCOPES, ANALYTICS_SCOPES, SCOPES
from uploader import get_authenticated_service
from analytics_reporter import YouTubeAnalyticsReporter


def inspect_credentials_and_token():
    status = {
        "credentials_file_exists": os.path.exists(CREDENTIALS_FILE),
        "token_file_exists": os.path.exists(TOKEN_FILE),
        "credentials_type": None,
        "token_scopes": [],
        "has_upload_scopes": False,
        "has_analytics_scope": False,
        "token_expired": None,
        "token_expiry": None
    }

    if status["credentials_file_exists"]:
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            client_type = "installed" if "installed" in cdata else ("web" if "web" in cdata else "unknown")
            status["credentials_type"] = client_type
            status["client_id_prefix"] = (cdata.get(client_type, {}).get("client_id", "")[:12] + "...") if client_type in cdata else "N/A"
        except Exception as e:
            status["credentials_error"] = str(e)

    if status["token_file_exists"]:
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                tdata = json.load(f)
            scopes = tdata.get("scopes", [])
            status["token_scopes"] = scopes
            status["has_upload_scopes"] = all(s in scopes for s in UPLOAD_SCOPES)
            status["has_analytics_scope"] = all(s in scopes for s in ANALYTICS_SCOPES)
            status["has_refresh_token"] = bool(tdata.get("refresh_token"))
            
            exp_str = tdata.get("expiry")
            if exp_str:
                status["token_expiry"] = exp_str
                # Parse ISO date
                try:
                    exp_dt = datetime.fromisoformat(exp_str.replace("Z", "+00:00"))
                    now_dt = datetime.now(timezone.utc)
                    status["token_expired"] = (exp_dt < now_dt)
                except Exception:
                    pass
        except Exception as e:
            status["token_error"] = str(e)

    return status


def inspect_channel_and_videos():
    report = {
        "timestamp": datetime.now().isoformat(),
        "auth_inspection": inspect_credentials_and_token(),
        "channel_data": None,
        "defective_video": None,
        "analytics_status": None,
        "errors": []
    }

    # 1. Test YouTube Data API v3
    if not report["auth_inspection"]["has_upload_scopes"]:
        report["errors"].append("Missing required upload/read scopes in token.json")
        return report

    try:
        service = get_authenticated_service(interactive=False, required_scopes=UPLOAD_SCOPES)
        
        # Channel Overview
        ch_resp = service.channels().list(part="snippet,statistics,contentDetails", mine=True).execute()
        items = ch_resp.get("items", [])
        if items:
            item = items[0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})
            uploads_pl = content.get("relatedPlaylists", {}).get("uploads")

            report["channel_data"] = {
                "id": item.get("id"),
                "title": snippet.get("title"),
                "description": snippet.get("description", "")[:100],
                "custom_url": snippet.get("customUrl"),
                "published_at": snippet.get("publishedAt"),
                "view_count": stats.get("viewCount"),
                "subscriber_count": stats.get("subscriberCount"),
                "video_count": stats.get("videoCount"),
                "hidden_subscriber_count": stats.get("hiddenSubscriberCount"),
                "uploads_playlist_id": uploads_pl
            }

        # 2. Inspect Defective Video HhotZWPAYaU
        target_vid_id = "HhotZWPAYaU"
        try:
            v_resp = service.videos().list(
                part="snippet,status,processingDetails,contentDetails",
                id=target_vid_id
            ).execute()
            v_items = v_resp.get("items", [])
            if v_items:
                v = v_items[0]
                report["defective_video"] = {
                    "id": target_vid_id,
                    "title": v.get("snippet", {}).get("title"),
                    "published_at": v.get("snippet", {}).get("publishedAt"),
                    "upload_status": v.get("status", {}).get("uploadStatus"),
                    "privacy_status": v.get("status", {}).get("privacyStatus"),
                    "rejection_reason": v.get("status", {}).get("rejectionReason"),
                    "processing_status": v.get("processingDetails", {}).get("processingStatus"),
                    "duration": v.get("contentDetails", {}).get("duration"),
                    "definition": v.get("contentDetails", {}).get("definition")
                }
            else:
                report["defective_video"] = {"id": target_vid_id, "status": "NOT_FOUND_ON_YOUTUBE"}
        except Exception as e:
            report["defective_video"] = {"id": target_vid_id, "error": str(e)}

        # 2b. Scan uploads playlist for any other stuck or 0-duration videos
        report["stuck_videos"] = []
        if uploads_pl:
            try:
                pl_items = service.playlistItems().list(
                    playlistId=uploads_pl,
                    part="contentDetails",
                    maxResults=50
                ).execute().get("items", [])
                video_ids = [it["contentDetails"]["videoId"] for it in pl_items]
                if video_ids:
                    v_resps = service.videos().list(
                        id=",".join(video_ids),
                        part="status,processingDetails,contentDetails,snippet"
                    ).execute().get("items", [])
                    for v in v_resps:
                        dur = v.get("contentDetails", {}).get("duration", "")
                        proc = v.get("processingDetails", {}).get("processingStatus", "")
                        up_st = v.get("status", {}).get("uploadStatus", "")
                        if dur == "P0D" or proc in ("failed", "processing") or up_st in ("rejected", "failed"):
                            report["stuck_videos"].append({
                                "id": v.get("id"),
                                "title": v.get("snippet", {}).get("title"),
                                "duration": dur,
                                "processing_status": proc,
                                "upload_status": up_st
                            })
            except Exception as e:
                report["stuck_videos_error"] = str(e)

    except Exception as e:
        report["errors"].append(f"YouTube Data API error: {e}")

    # 3. Check YouTube Analytics Status
    reporter = YouTubeAnalyticsReporter()
    ok, auth_msg = reporter.check_prerequisites()
    report["analytics_status"] = {
        "prerequisites_ok": ok,
        "auth_status": reporter.auth_status,
        "status_detail": auth_msg
    }

    if ok:
        query_res = reporter.query_channel_overview()
        report["analytics_status"]["query_result"] = query_res.get("status")
        report["analytics_status"]["query_data"] = query_res.get("data")
    else:
        report["analytics_status"]["exact_blocker"] = (
            "Scope 'yt-analytics.readonly' is missing from local token.json. "
            "Re-authorization requires running 'python auth_setup.py' interactively once."
        )

    return report


if __name__ == "__main__":
    data = inspect_channel_and_videos()
    print("==================================================")
    print(" YouTube Read-Only Access & Channel Verification")
    print("==================================================")
    auth = data["auth_inspection"]
    print(f"Credentials File: {'Found' if auth['credentials_file_exists'] else 'Missing'}")
    print(f"Token File:       {'Found' if auth['token_file_exists'] else 'Missing'}")
    print(f"Has Upload Scopes: {auth['has_upload_scopes']}")
    print(f"Has Analytics Scope: {auth['has_analytics_scope']}")
    print(f"Token Expiry:      {auth['token_expiry']} (Expired: {auth['token_expired']})")

    ch = data.get("channel_data")
    if ch:
        print("\n--- Channel Overview ---")
        print(f"Channel Name:  {ch['title']}")
        print(f"Channel ID:    {ch['id']}")
        print(f"Subscribers:   {ch['subscriber_count']}")
        print(f"Total Views:   {ch['view_count']}")
        print(f"Total Videos:  {ch['video_count']}")

    dv = data.get("defective_video")
    if dv:
        print("\n--- Defective Video (HhotZWPAYaU) ---")
        for k, v in dv.items():
            print(f"  {k}: {v}")

    stuck = data.get("stuck_videos", [])
    print(f"\n--- Channel Upload Processing Scan (Latest 50 Videos) ---")
    if stuck:
        print(f"⚠️ Found {len(stuck)} video(s) stuck in processing or 0 duration:")
        for sv in stuck:
            print(f"  • ID: {sv['id']} | Title: {sv['title'][:50]} | Duration: {sv['duration']} | Status: {sv['processing_status']}")
    else:
        print("✅ Zero stuck videos found across latest 50 uploads! All recent videos processed successfully.")

    ana = data.get("analytics_status")
    if ana:
        print("\n--- YouTube Analytics API Status ---")
        print(f"Status: {ana['auth_status']}")
        print(f"Detail: {ana.get('exact_blocker') or ana['status_detail']}")

    if data["errors"]:
        print("\n--- Errors ---")
        for err in data["errors"]:
            print(f"❌ {err}")
