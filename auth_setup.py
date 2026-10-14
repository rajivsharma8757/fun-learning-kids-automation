"""
auth_setup.py
-------------
Interactive YouTube OAuth setup and verification utility for Fun Learning Kids.

Safely configures and verifies OAuth 2.0 authorization for:
1. YouTube Data API v3 (upload, readonly)
2. YouTube Analytics API v2 (yt-analytics.readonly)

Safety features:
- Automatically creates a backup of token.json (token.json.bak).
- Explains requested scopes before launching browser.
- Prompts for explicit confirmation before launching browser (supports --yes / --check-only).
- Tests channel connection and reports channel name, ID, and subscriber count.
"""

import os
import sys
import json
import shutil
import argparse

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    CREDENTIALS_FILE, TOKEN_FILE, CHANNEL_NAME,
    SCOPES, UPLOAD_SCOPES, ANALYTICS_SCOPES
)
from uploader import get_authenticated_service


def backup_existing_token():
    """Safely creates a backup copy of token.json if present."""
    if os.path.exists(TOKEN_FILE):
        bak_file = TOKEN_FILE + ".bak"
        try:
            shutil.copy2(TOKEN_FILE, bak_file)
            print(f"📦 Backup created: {bak_file}")
            return bak_file
        except Exception as e:
            print(f"⚠️ Warning: Could not create token backup: {e}")
    return None


def inspect_current_token():
    """Returns (exists: bool, scopes: list, is_valid: bool)"""
    if not os.path.exists(TOKEN_FILE):
        return False, [], False
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        scopes = data.get("scopes", [])
        return True, scopes, True
    except Exception:
        return True, [], False


def main():
    parser = argparse.ArgumentParser(description="YouTube OAuth Setup & Verification")
    parser.add_argument("--check-only", action="store_true", help="Check current token status without launching browser")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirm browser launch")
    parser.add_argument("--force", action="store_true", help="Force re-authorization even if existing token has scopes")
    args = parser.parse_args()

    print("==================================================")
    print(f" YouTube OAuth Setup & Verification - {CHANNEL_NAME}")
    print("==================================================")
    print(f"Client Secrets: {CREDENTIALS_FILE}")
    print(f"Target Token:   {TOKEN_FILE}\n")

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Error: credentials.json not found at {CREDENTIALS_FILE}")
        print("Please download OAuth 2.0 Client credentials from Google Cloud Console.")
        sys.exit(1)

    print("Configured Scopes:")
    for s in SCOPES:
        desc = "Daily Video Uploads" if "upload" in s else (
            "Channel Analytics" if "analytics" in s else "Metadata / Channel Verification"
        )
        print(f"  • {s} ({desc})")
    print()

    exists, current_scopes, is_valid = inspect_current_token()

    if exists:
        print("Current Saved Token:")
        print(f"  • Status: {'Valid JSON' if is_valid else 'Corrupt / Unreadable'}")
        missing_scopes = [s for s in SCOPES if s not in current_scopes]
        if missing_scopes:
            print("  • Missing Scopes:")
            for ms in missing_scopes:
                print(f"    - {ms}")
        else:
            print("  • All required scopes present!")

        if not missing_scopes and not args.force:
            print("\n🔍 Verifying channel connection with current token...")
            try:
                youtube = get_authenticated_service(interactive=False, required_scopes=SCOPES)
                req = youtube.channels().list(part="snippet,statistics", mine=True)
                resp = req.execute()
                items = resp.get("items", [])
                if items:
                    ch_title = items[0]["snippet"]["title"]
                    ch_id = items[0]["id"]
                    subs = items[0].get("statistics", {}).get("subscriberCount", "Hidden")
                    print(f"✅ Connected to Channel: {ch_title} (ID: {ch_id})")
                    print(f"   Subscribers: {subs}")
                    print("\n🎉 Existing token.json is active and valid with all required scopes!")
                    print("   Daily uploads and analytics reporting are ready to run.")
                    return
            except Exception as e:
                print(f"⚠️ Existing token verification failed: {e}")
                print("   Re-authorization required.")

    if args.check_only:
        print("\n[--check-only] Exiting without opening browser.")
        return

    # Backup existing token before proceeding
    backup_existing_token()

    print("\n--------------------------------------------------")
    print("ACTION REQUIRED: Browser OAuth Consent")
    print("--------------------------------------------------")
    print("A browser window will open asking you to sign in with your YouTube Google account.")
    print("You will see consent screens requesting:")
    print("  1. Manage your YouTube videos (required for automated daily uploads)")
    print("  2. View YouTube Analytics reports (for automated view & retention tracking)")
    print("--------------------------------------------------\n")

    if not args.yes:
        try:
            choice = input("Open browser now to authorize? [Y/n]: ").strip().lower()
            if choice not in ("", "y", "yes"):
                print("❌ OAuth setup cancelled by user. Existing token left untouched.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Setup aborted.")
            return

    try:
        # Request all configured scopes during interactive setup
        youtube = get_authenticated_service(interactive=True, required_scopes=SCOPES)
        print("\n🔍 Checking YouTube channel connection...")

        req = youtube.channels().list(part="snippet,statistics", mine=True)
        resp = req.execute()

        items = resp.get("items", [])
        if items:
            ch_title = items[0]["snippet"]["title"]
            ch_id = items[0]["id"]
            subs = items[0].get("statistics", {}).get("subscriberCount", "Hidden")
            print(f"✅ Connected to Channel: {ch_title} (ID: {ch_id})")
            print(f"   Subscribers: {subs}")
            print("\n🎉 Reusable token.json is configured and verified with upload + analytics scopes!")
            print("   The system can now run 100% automated via Windows Task Scheduler.")
        else:
            print("✅ Authenticated successfully, but no channel found for this Google account.")

    except Exception as e:
        print(f"❌ Authorization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
