"""
auth_setup.py
-------------
Interactive YouTube OAuth setup and verification utility.
Supports multi-channel profiles:
  - nanhe_seekho_club (New Target Channel, saved to token_nanhe_seekho_club.json)
  - fun_learning_kids (Legacy Protected Channel, saved to token.json)

Safely configures and verifies OAuth 2.0 authorization for:
1. YouTube Data API v3 (upload, readonly)
2. YouTube Analytics API v2 (yt-analytics.readonly)

Safety features:
- Automatically backs up active token.
- Multi-channel profile support via --profile.
- Explains requested scopes before launching browser.
- Warns if old channel account is mistakenly selected for the new channel profile.
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
from config import BASE_DIR, TOKEN_FILE


def inspect_current_token(target_token_file=None):
    """Returns (exists: bool, scopes: list, is_valid: bool)"""
    tf = target_token_file or TOKEN_FILE
    if not os.path.exists(tf) and target_token_file is None:
        legacy_tf = os.path.join(BASE_DIR, "token.json")
        if os.path.exists(legacy_tf):
            tf = legacy_tf
    if not os.path.exists(tf):
        return False, [], False
    try:
        with open(tf, "r", encoding="utf-8") as f:
            data = json.load(f)
        scopes = data.get("scopes", [])
        return True, scopes, True
    except Exception:
        return True, [], False



def main():
    parser = argparse.ArgumentParser(description="YouTube OAuth Setup & Verification")
    parser.add_argument("--profile", default=None, choices=["nanhe_seekho_club", "fun_learning_kids"],
                        help="Channel profile to authorize (default: nanhe_seekho_club)")
    parser.add_argument("--check-only", action="store_true", help="Check current token status without launching browser")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirm browser launch")
    parser.add_argument("--force", action="store_true", help="Force re-authorization even if existing token has scopes")
    args = parser.parse_args()

    # Set profile if requested before loading config
    if args.profile:
        os.environ["CHANNEL_PROFILE"] = args.profile

    from config import (
        CREDENTIALS_FILE, CHANNEL_PROFILES, ACTIVE_PROFILE_NAME,
        ACTIVE_PROFILE, SCOPES, UPLOAD_SCOPES, ANALYTICS_SCOPES,
        LEGACY_PROTECTED_CHANNEL_ID
    )
    from uploader import get_authenticated_service

    profile_name = ACTIVE_PROFILE_NAME
    channel_name = ACTIVE_PROFILE["name"]
    token_file = ACTIVE_PROFILE["token_file"]

    print("==================================================")
    print(f" YouTube OAuth Setup & Verification")
    print(f" Channel: {channel_name} (Profile: {profile_name})")
    print("==================================================")
    print(f"Client Secrets: {CREDENTIALS_FILE}")
    print(f"Target Token:   {token_file}\n")

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

    # Inspect current token
    exists = os.path.exists(token_file)
    current_scopes = []
    is_valid = False
    if exists:
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                tdata = json.load(f)
            current_scopes = tdata.get("scopes", [])
            is_valid = True
        except Exception:
            is_valid = False

    if exists:
        print(f"Current Saved Token ({os.path.basename(token_file)}):")
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

                    if profile_name == "nanhe_seekho_club" and ch_id == LEGACY_PROTECTED_CHANNEL_ID:
                        print(f"\n⚠️ WARNING: This token is authenticated as the OLD channel 'Fun Learning Kids' ({ch_id}).")
                        print("   For 'Nanhe Seekho Club', please run with --force to authorize the new channel account.")
                        if args.check_only:
                            return
                    else:
                        print(f"\n🎉 Token {os.path.basename(token_file)} is active and valid with all required scopes!")
                        print(f"   Automation for '{channel_name}' is ready to run.")
                        return
            except Exception as e:
                print(f"⚠️ Existing token verification failed: {e}")
                print("   Re-authorization required.")

    if args.check_only:
        print("\n[--check-only] Exiting without opening browser.")
        return

    # Backup existing token if present
    if os.path.exists(token_file):
        bak_file = token_file + ".bak"
        try:
            shutil.copy2(token_file, bak_file)
            print(f"📦 Backup created: {bak_file}")
        except Exception as e:
            print(f"⚠️ Warning: Could not create token backup: {e}")

    print("\n--------------------------------------------------")
    print(f"ACTION REQUIRED: Google OAuth Browser Consent ({channel_name})")
    print("--------------------------------------------------")
    print(f"A browser window will open asking you to sign in with your Google account for:")
    print(f"  >> {channel_name} <<")
    print("Scopes requested:")
    print("  1. Manage your YouTube videos (required for automated video uploads)")
    print("  2. View YouTube Analytics reports (for automated view & retention tracking)")
    print(f"Credentials will be saved securely to: {os.path.basename(token_file)}")
    print("--------------------------------------------------\n")

    if not args.yes:
        try:
            choice = input(f"Open browser now to authorize '{channel_name}'? [Y/n]: ").strip().lower()
            if choice not in ("", "y", "yes"):
                print("❌ OAuth setup cancelled by user. Existing files left untouched.")
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

            if profile_name == "nanhe_seekho_club" and ch_id == LEGACY_PROTECTED_CHANNEL_ID:
                print("\n🛑 ATTENTION: You selected the OLD channel 'Fun Learning Kids' in Google login.")
                print(f"   Channel ID {ch_id} is the protected old channel.")
                print("   To authorize 'Nanhe Seekho Club', please re-run 'python auth_setup.py' and choose the new account/channel.")
            else:
                print(f"\n🎉 Token {os.path.basename(token_file)} successfully configured for '{channel_name}'!")
                print("   The system is ready for automated generation and uploads.")
        else:
            print("✅ Authenticated successfully, but no channel found for this Google account.")

    except Exception as e:
        print(f"❌ Authorization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
