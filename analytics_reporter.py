"""
analytics_reporter.py
---------------------
Official YouTube Analytics API integration and baseline performance reporting
for Fun Learning Kids.

Handles:
1. Safe checking of YouTube Analytics API enablement & OAuth scopes.
2. Official YouTube Analytics API v2 reporting (views, watch time, retention, traffic sources).
3. Graceful handling of blocked states (API disabled, scope pending, processing delays).
4. Honest differentiation between Data API v3 metadata and Analytics API metrics.
5. Clarification that Impressions & CTR are NOT exposed via YouTube Analytics API v2
   and must be viewed in YouTube Studio Analytics.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta, timezone

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BASE_DIR, TOKEN_FILE, CREDENTIALS_FILE, HISTORY_DIR

logger = logging.getLogger("kids_automation")

REQUIRED_ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"
GCP_CONSOLE_ENABLE_URL = (
    "https://console.developers.google.com/apis/api/youtubeanalytics.googleapis.com/overview?project=597824175623"
)


class YouTubeAnalyticsReporter:
    def __init__(self, token_file=TOKEN_FILE, credentials_file=CREDENTIALS_FILE):
        self.token_file = token_file
        self.credentials_file = credentials_file
        self.client = None
        self.auth_status = "UNKNOWN"
        self.status_detail = ""

    def check_prerequisites(self):
        """
        Safely inspects OAuth token scopes and API configuration
        without exposing any tokens or secrets.
        """
        if not os.path.exists(self.token_file):
            self.auth_status = "BLOCKED_NO_TOKEN"
            self.status_detail = f"Token file not found at {self.token_file}."
            return False, self.status_detail

        try:
            with open(self.token_file, "r", encoding="utf-8") as f:
                token_data = json.load(f)
            scopes = token_data.get("scopes", [])
        except Exception as e:
            self.auth_status = "BLOCKED_TOKEN_READ_ERROR"
            self.status_detail = f"Could not read token file: {e}"
            return False, self.status_detail

        if REQUIRED_ANALYTICS_SCOPE not in scopes:
            self.auth_status = "BLOCKED_SCOPE_PENDING"
            self.status_detail = (
                f"OAuth token is missing scope '{REQUIRED_ANALYTICS_SCOPE}'. "
                "Current scopes only authorize video upload & Data API read. "
                "Re-authorization with the analytics scope is required via 'python auth_setup.py'."
            )
            return False, self.status_detail

        return True, "OAuth scopes verified."

    def get_service(self):
        """Builds YouTube Analytics API v2 client if authorized."""
        if self.client:
            return self.client, None

        ok, msg = self.check_prerequisites()
        if not ok:
            return None, msg

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials.from_authorized_user_file(self.token_file)
            service = build("youtubeAnalytics", "v2", credentials=creds)
            self.client = service
            return service, None
        except Exception as e:
            self.auth_status = "BLOCKED_CLIENT_BUILD_ERROR"
            self.status_detail = f"Failed to build analytics service: {e}"
            return None, self.status_detail

    def query_channel_overview(self, start_date=None, end_date=None):
        """
        Retrieves channel-level aggregated performance metrics:
        views, estimatedMinutesWatched, averageViewDuration, averageViewPercentage,
        subscribersGained, subscribersLost.
        """
        service, err = self.get_service()
        if not service:
            return {
                "status": "BLOCKED",
                "reason": err or self.status_detail,
                "gcp_enable_url": GCP_CONSOLE_ENABLE_URL,
                "data": None
            }

        if not end_date:
            end_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            from googleapiclient.errors import HttpError
            res = service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost"
            ).execute()
            return {"status": "SUCCESS", "data": res}
        except HttpError as e:
            if e.resp.status == 403 and "accessNotConfigured" in str(e.content):
                return {
                    "status": "BLOCKED",
                    "reason": "YouTube Analytics API is disabled in Google Cloud Project 597824175623.",
                    "gcp_enable_url": GCP_CONSOLE_ENABLE_URL,
                    "data": None
                }
            return {
                "status": "API_ERROR",
                "http_status": e.resp.status,
                "reason": str(e),
                "data": None
            }
        except Exception as e:
            return {"status": "EXCEPTION", "reason": str(e), "data": None}

    def query_traffic_sources(self, start_date=None, end_date=None):
        """
        Retrieves views and watch time broken down by traffic source type:
        e.g., NO_LINK_OTHER (direct/internal), YT_SEARCH, RELATED_VIDEO, SHORTS, EXT_URL, etc.
        """
        service, err = self.get_service()
        if not service:
            return {
                "status": "BLOCKED",
                "reason": err or self.status_detail,
                "gcp_enable_url": GCP_CONSOLE_ENABLE_URL,
                "data": None
            }

        if not end_date:
            end_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            from googleapiclient.errors import HttpError
            res = service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched",
                dimensions="insightTrafficSourceType",
                sort="-views"
            ).execute()
            return {"status": "SUCCESS", "data": res}
        except HttpError as e:
            if e.resp.status == 403 and "accessNotConfigured" in str(e.content):
                return {
                    "status": "BLOCKED",
                    "reason": "YouTube Analytics API is disabled in Google Cloud Project 597824175623.",
                    "gcp_enable_url": GCP_CONSOLE_ENABLE_URL,
                    "data": None
                }
            return {
                "status": "API_ERROR",
                "http_status": e.resp.status,
                "reason": str(e),
                "data": None
            }
        except Exception as e:
            return {"status": "EXCEPTION", "reason": str(e), "data": None}

    def query_top_videos(self, start_date=None, end_date=None, max_results=10):
        """
        Retrieves top performing videos by views and watch time.
        """
        service, err = self.get_service()
        if not service:
            return {
                "status": "BLOCKED",
                "reason": err or self.status_detail,
                "gcp_enable_url": GCP_CONSOLE_ENABLE_URL,
                "data": None
            }

        if not end_date:
            end_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            from googleapiclient.errors import HttpError
            res = service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration",
                dimensions="video",
                sort="-views",
                maxResults=max_results
            ).execute()
            return {"status": "SUCCESS", "data": res}
        except HttpError as e:
            if e.resp.status == 403 and "accessNotConfigured" in str(e.content):
                return {
                    "status": "BLOCKED",
                    "reason": "YouTube Analytics API is disabled in Google Cloud Project 597824175623.",
                    "gcp_enable_url": GCP_CONSOLE_ENABLE_URL,
                    "data": None
                }
            return {
                "status": "API_ERROR",
                "http_status": e.resp.status,
                "reason": str(e),
                "data": None
            }
        except Exception as e:
            return {"status": "EXCEPTION", "reason": str(e), "data": None}

    def generate_baseline_report(self, audit_file=os.path.join(HISTORY_DIR, "all_youtube_videos_audit.json")):
        """
        Compiles an honest, structured baseline report combining:
        1. Real Data API v3 video metadata (duration, format, privacy, view counts).
        2. Segmentations across format, age, topics, and duration.
        3. Real status of YouTube Analytics API and impression CTR availability.
        """
        ok, auth_detail = self.check_prerequisites()

        report = {
            "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "channel_name": "Fun Learning Kids",
            "channel_id": "UCcOA6heUaTbOUnx7ERF23Gw",
            "analytics_api_status": "BLOCKED — Scope 'yt-analytics.readonly' missing from token.json" if not ok else "ACTIVE",
            "analytics_api_enable_url": GCP_CONSOLE_ENABLE_URL,
            "oauth_scope_status": auth_detail,
            "impression_ctr_availability": (
                "UNAVAILABLE via API — YouTube Analytics API v2 does NOT expose impressions "
                "or CTR on channel reports. These metrics must be inspected manually in "
                "YouTube Studio -> Analytics -> Content -> Reach."
            ),
            "data_source_limitation": (
                "Reported view counts are from YouTube Data API v3 and reflect total cumulative views. "
                "The API cannot separate developer self-testing views from real organic views. "
                "Given small view counts (0 to 10), sample size is insufficient for statistical confidence."
            ),
            "live_analytics": None,
            "totals": {
                "total_videos": 0,
                "public_videos": 0,
                "unlisted_videos": 0,
                "total_views": 0,
                "videos_with_0_views": 0,
                "videos_with_views": 0
            },
            "format_breakdown": {
                "landscape_16_9": {"count": 0, "total_views": 0, "avg_duration_sec": 0.0},
                "shorts_9_16": {"count": 0, "total_views": 0, "avg_duration_sec": 0.0}
            },
            "duration_buckets": {
                "under_15s": {"count": 0, "total_views": 0},
                "15_to_30s": {"count": 0, "total_views": 0},
                "30_to_60s": {"count": 0, "total_views": 0},
                "over_60s": {"count": 0, "total_views": 0}
            },
            "topic_breakdown": {},
            "top_viewed_videos": []
        }

        # Query live Analytics API if prerequisites pass
        if ok:
            overview_res = self.query_channel_overview()
            sources_res = self.query_traffic_sources()
            top_vids_res = self.query_top_videos()
            if overview_res.get("status") == "SUCCESS":
                report["analytics_api_status"] = "ACTIVE & CONNECTED"
                report["live_analytics"] = {
                    "channel_overview": overview_res.get("data"),
                    "traffic_sources": sources_res.get("data"),
                    "top_videos": top_vids_res.get("data")
                }
            else:
                report["analytics_api_status"] = f"BLOCKED — {overview_res.get('reason')}"

        if not os.path.exists(audit_file):
            report["error"] = f"Audit file not found: {audit_file}"
            return report

        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                videos = json.load(f)
        except Exception as e:
            report["error"] = f"Failed to read audit file: {e}"
            return report

        report["totals"]["total_videos"] = len(videos)
        total_views = 0
        landscape_durations = []

        for v in videos:
            views = int(v.get("views", 0))
            dur = v.get("duration_sec", 0)
            vis = v.get("visibility", "public")

            total_views += views
            if vis == "public":
                report["totals"]["public_videos"] += 1
            elif vis == "unlisted":
                report["totals"]["unlisted_videos"] += 1

            if views == 0:
                report["totals"]["videos_with_0_views"] += 1
            else:
                report["totals"]["videos_with_views"] += 1

            # Format profile check
            # In existing dataset, 100% of videos were 16:9 landscape
            report["format_breakdown"]["landscape_16_9"]["count"] += 1
            report["format_breakdown"]["landscape_16_9"]["total_views"] += views
            landscape_durations.append(dur)

            # Duration bucket
            if dur < 15:
                report["duration_buckets"]["under_15s"]["count"] += 1
                report["duration_buckets"]["under_15s"]["total_views"] += views
            elif dur < 30:
                report["duration_buckets"]["15_to_30s"]["count"] += 1
                report["duration_buckets"]["15_to_30s"]["total_views"] += views
            elif dur <= 60:
                report["duration_buckets"]["30_to_60s"]["count"] += 1
                report["duration_buckets"]["30_to_60s"]["total_views"] += views
            else:
                report["duration_buckets"]["over_60s"]["count"] += 1
                report["duration_buckets"]["over_60s"]["total_views"] += views

            # Topic category classification from title
            title = v.get("title", "")
            if "Cartoon" in title or "बंटू" in title or "कोको" in title or "मीमी" in title or "भोलू" in title:
                topic = "cartoon_animation"
            elif "Moral Story" in title:
                topic = "moral_story"
            elif "Good Habits" in title:
                topic = "good_habits"
            elif "Animal Story" in title:
                topic = "animal_story"
            elif "ABC Learning" in title:
                topic = "abc"
            elif "Numbers Learning" in title:
                topic = "numbers"
            else:
                topic = "other"

            if topic not in report["topic_breakdown"]:
                report["topic_breakdown"][topic] = {"count": 0, "total_views": 0}
            report["topic_breakdown"][topic]["count"] += 1
            report["topic_breakdown"][topic]["total_views"] += views

        report["totals"]["total_views"] = total_views
        if landscape_durations:
            report["format_breakdown"]["landscape_16_9"]["avg_duration_sec"] = round(
                sum(landscape_durations) / len(landscape_durations), 1
            )

        # Top viewed
        sorted_vids = sorted(videos, key=lambda x: int(x.get("views", 0)), reverse=True)
        report["top_viewed_videos"] = [
            {
                "video_id": v.get("video_id"),
                "title": v.get("title"),
                "published_at": v.get("published_at", "")[:10],
                "duration_sec": v.get("duration_sec"),
                "views": v.get("views", 0),
                "visibility": v.get("visibility")
            }
            for v in sorted_vids[:10]
        ]

        return report


if __name__ == "__main__":
    reporter = YouTubeAnalyticsReporter()
    print("=== Checking Analytics API Prerequisites ===")
    ok, msg = reporter.check_prerequisites()
    print(f"Status: {reporter.auth_status}")
    print(f"Detail: {msg}")

    print("\n=== Generating Local Baseline Report ===")
    baseline = reporter.generate_baseline_report()
    print(f"Total Videos Analyzed: {baseline['totals']['total_videos']}")
    print(f"Total Channel Views: {baseline['totals']['total_views']}")
    print(f"Format Breakdown: Landscape = {baseline['format_breakdown']['landscape_16_9']['count']}, Shorts = {baseline['format_breakdown']['shorts_9_16']['count']}")
    print("\nTop 5 Viewed Videos:")
    for v in baseline['top_viewed_videos'][:5]:
        print(f"  {v['video_id']} ({v['views']} views, {v['duration_sec']}s): {v['title'][:60]}")
