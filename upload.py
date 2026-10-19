import os
import sys
from config import BASE_DIR, VIDEO_DIR, THUMBNAIL_DIR
from uploader import get_authenticated_service, upload_video_to_youtube, is_already_uploaded

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def get_latest_unuploaded_video():
    """Finds the latest video that has not yet been uploaded."""
    files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")]
    if not files:
        print("❌ No video files found in video directory:", VIDEO_DIR)
        return None

    # Sort by modification time descending (newest first)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(VIDEO_DIR, x)), reverse=True)

    for f in files:
        path = os.path.join(VIDEO_DIR, f)
        already_done, _ = is_already_uploaded(path)
        if not already_done:
            return path

    print("ℹ️ All videos in the video folder have already been uploaded.")
    return None

def detect_topic(video_path):
    from config import TOPICS
    filename = os.path.basename(video_path).lower()
    for topic in TOPICS:
        if topic in filename:
            return topic
    return "moral_story"

if __name__ == "__main__":
    print("🚀 Starting YouTube Upload...")

    target_video = get_latest_unuploaded_video()
    if not target_video:
        print("Nothing to upload. Exiting.")
        sys.exit(0)

    print(f"✅ Selected Video: {target_video}")
    topic = detect_topic(target_video)

    # Check for corresponding thumbnail
    base_name = os.path.splitext(os.path.basename(target_video))[0]
    thumb_path = os.path.join(THUMBNAIL_DIR, f"{base_name}.jpg")
    if not os.path.exists(thumb_path):
        thumb_path = None

    from config import CHANNEL_NAME
    metadata = {
        "title": f"{topic.replace('_', ' ').title()} for Kids | {CHANNEL_NAME}",
        "description": f"Welcome to {CHANNEL_NAME}!\n\nEnjoy today's educational {topic.replace('_', ' ')}.\n\nLike, Share & Subscribe!",
        "tags": [topic.replace("_", " "), "kids learning", CHANNEL_NAME.lower()],
        "topic": topic
    }

    res = upload_video_to_youtube(
        video_path=target_video,
        metadata=metadata,
        thumbnail_path=thumb_path,
        interactive=True
    )
    success, vid_id, url = res

    if success:
        print(f"\n🎉 Finished successfully! Video Link: {url}")
        print(f"   Thumbnail Status: {res.thumbnail_status}")
    else:
        print(f"\n❌ Upload failed: {res.error or 'Unknown upload error'}")
        sys.exit(1)
