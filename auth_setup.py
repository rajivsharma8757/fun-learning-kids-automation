import os
import sys
from uploader import get_authenticated_service
from config import TOKEN_FILE, CHANNEL_NAME

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def main():
    print("==================================================")
    print(f" YouTube OAuth Setup - {CHANNEL_NAME}")
    print("==================================================")
    print(f"Target token file: {TOKEN_FILE}\n")

    try:
        youtube = get_authenticated_service(interactive=True)
        print("\n🔍 Checking YouTube channel connection...")
        
        # Test API connection by fetching channel info
        req = youtube.channels().list(part="snippet,statistics", mine=True)
        resp = req.execute()

        items = resp.get("items", [])
        if items:
            ch_title = items[0]["snippet"]["title"]
            ch_id = items[0]["id"]
            subs = items[0].get("statistics", {}).get("subscriberCount", "Hidden")
            print(f"✅ Connected to Channel: {ch_title} (ID: {ch_id})")
            print(f"   Subscribers: {subs}")
            print("\n🎉 Reusable token.json is configured and verified!")
            print("   The system can now run 100% automated via Windows Task Scheduler.")
        else:
            print("✅ Authenticated successfully, but no channel found for this Google account.")

    except Exception as e:
        print(f"❌ Authorization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
