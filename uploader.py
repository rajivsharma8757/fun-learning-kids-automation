import os
import sys
import json
import hashlib
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from config import (
    CREDENTIALS_FILE, TOKEN_FILE, SCOPES,
    UPLOADS_HISTORY_FILE, YOUTUBE_CATEGORY_ID,
    YOUTUBE_MADE_FOR_KIDS, DEFAULT_PRIVACY_STATUS
)

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def compute_file_hash(filepath):
    """Computes SHA-256 of video file to uniquely identify it."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_authenticated_service(interactive=False):
    """
    Retrieves or refreshes YouTube API credentials.
    Uses token.json if available to run 100% unattended without browser popups.
    Only launches interactive browser login if interactive=True and no valid token exists.
    """
    creds = None

    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"Missing OAuth credentials file at: {CREDENTIALS_FILE}")

    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as tf:
                tok_data = json.load(tf)
            tok_scopes = set(tok_data.get("scopes", []))
            if not all(s in tok_scopes for s in SCOPES):
                print(f"⚠️ Saved token.json is missing required scopes ({SCOPES}). Re-authorization required.")
                creds = None
            else:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"⚠️ Warning reading {TOKEN_FILE}: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired OAuth token automatically...")
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
                print("✅ Token refreshed successfully.")
            except Exception as e:
                print(f"⚠️ Could not auto-refresh token: {e}")
                creds = None

        if not creds:
            if not interactive:
                raise RuntimeError(
                    f"Authentication required: No valid token found at {TOKEN_FILE}.\n"
                    f"Please run 'python auth_setup.py' once interactively to complete initial authorization."
                )
            print("🔑 Opening browser for one-time YouTube OAuth authorization...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            print(f"✅ Authorization successful! Saved reusable token to {TOKEN_FILE}")

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

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
    with open(UPLOADS_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def is_already_uploaded(video_path):
    """
    Checks if a video has already been uploaded to prevent duplicate uploads.
    Matches by filename and SHA-256 hash.
    """
    if not os.path.exists(video_path):
        return False, None

    filename = os.path.basename(video_path)
    file_hash = compute_file_hash(video_path)
    history = load_upload_history()

    for item in history:
        if item.get("file_hash") == file_hash or item.get("filename") == filename:
            return True, item
    return False, None

def upload_video_to_youtube(video_path, metadata, thumbnail_path=None, privacy_status=None, interactive=False):
    """
    Uploads a video to YouTube with complete metadata and COPPA compliance.
    Returns (success, video_id, video_url).
    """
    if not os.path.exists(video_path):
        return False, None, f"Video file not found: {video_path}"

    # 1. Check duplicate upload
    already_done, record = is_already_uploaded(video_path)
    if already_done:
        vid_id = record.get("video_id")
        url = f"https://youtube.com/watch?v={vid_id}"
        print(f"🛑 Video already uploaded previously! Skipping duplicate upload.")
        print(f"🎥 Existing Video Link: {url}")
        return True, vid_id, url

    # 2. Get YouTube client
    try:
        youtube = get_authenticated_service(interactive=interactive)
    except Exception as e:
        print(f"❌ YouTube authentication error: {e}")
        return False, None, str(e)

    # 3. Prepare payload
    privacy = privacy_status or DEFAULT_PRIVACY_STATUS
    title = metadata.get("title", "Kids Learning Video | Fun Learning Kids")
    description = metadata.get("description", "Welcome to Fun Learning Kids!")
    tags = metadata.get("tags", ["kids", "learning", "fun learning kids"])
    topic = metadata.get("topic", "general")

    print("📤 Uploading video to YouTube...")
    print(f"   Title: {title}")
    print(f"   Privacy: {privacy}")
    print(f"   Made For Kids: {YOUTUBE_MADE_FOR_KIDS}")

    body = {
        "snippet": {
            "title": title[:100], # YouTube max title length is 100
            "description": description[:5000],
            "tags": tags,
            "categoryId": YOUTUBE_CATEGORY_ID
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": YOUTUBE_MADE_FOR_KIDS
        }
    }

    try:
        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            chunksize=1024 * 1024 * 4,
            resumable=True
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"   Upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        video_url = f"https://youtube.com/watch?v={video_id}"
        print(f"\n🎉 Upload Successful!")
        print(f"🎥 Video Link: {video_url}")

        # 4. Upload thumbnail if available
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                print(f"🖼️ Setting custom video thumbnail...")
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
                ).execute()
                print("✅ Thumbnail uploaded successfully!")
            except Exception as e:
                print(f"⚠️ Note: Custom thumbnail could not be set: {e}")
                print("   (YouTube requires account phone-verification for custom thumbnails; video upload is unaffected)")

        # 5. Record in history log
        record_upload_success({
            "timestamp": datetime.now().isoformat(),
            "filename": os.path.basename(video_path),
            "file_hash": compute_file_hash(video_path),
            "video_id": video_id,
            "url": video_url,
            "title": title,
            "topic": topic,
            "privacy": privacy
        })

        return True, video_id, video_url

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False, None, str(e)
