"""
tools/audit_duplicate_titles.py
-------------------------------
Audits all existing YouTube uploads for duplicate titles.
Produces:
1. Structured duplicate title groups with affected video IDs.
2. Safe proposed title corrections (with episode/part numbers) for user approval.
3. Does NOT modify, rename, or delete any live YouTube videos.
"""

import os
import sys
import json
from collections import defaultdict

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from config import HISTORY_DIR

AUDIT_FILE = os.path.join(HISTORY_DIR, "all_youtube_videos_audit.json")
OUTPUT_MD = os.path.join(BASE_DIR, "docs", "duplicate_titles_audit.md")
PROPOSED_JSON = os.path.join(BASE_DIR, "docs", "proposed_title_corrections.json")


def analyze_titles(audit_path=AUDIT_FILE):
    if not os.path.exists(audit_path):
        print(f"Audit file not found: {audit_path}")
        return None

    with open(audit_path, "r", encoding="utf-8") as f:
        videos = json.load(f)

    # Sort chronologically
    videos = sorted(videos, key=lambda v: v.get("published_at", ""))

    title_groups = defaultdict(list)
    for v in videos:
        raw_title = v.get("title", "")
        clean_title = " ".join(raw_title.strip().split())
        title_groups[clean_title].append(v)

    duplicate_groups = {k: v for k, v in title_groups.items() if len(v) > 1}
    total_videos = len(videos)
    affected_videos = sum(len(v) for v in duplicate_groups.values())

    # Build proposed corrections
    corrections = []
    for base_title, vids in duplicate_groups.items():
        # Clean title base for tagging
        for idx, vid in enumerate(vids, start=1):
            vid_id = vid.get("video_id")
            pub = vid.get("published_at", "")[:10]
            dur = vid.get("duration_sec", 0)
            views = vid.get("views", 0)

            # Generate distinct truthful title preserving <100 char limit
            # Format: Insert (Ep {idx}) or (Part {idx})
            suffix = f" (Ep {idx})" if ("Cartoon" in base_title or "बंटू" in base_title or "कोको" in base_title or "मीमी" in base_title) else f" (Part {idx})"
            
            if " | " in base_title:
                parts = base_title.split(" | ", 1)
                proposed = f"{parts[0]}{suffix} | {parts[1]}"
            else:
                proposed = f"{base_title}{suffix}"

            # Truncate if exceeds 100
            if len(proposed) > 100:
                proposed = proposed[:96] + "..."

            corrections.append({
                "video_id": vid_id,
                "published_date": pub,
                "current_title": base_title,
                "proposed_title": proposed,
                "duration_sec": dur,
                "views": views,
                "episode_number": idx,
                "group_size": len(vids)
            })

    return {
        "total_videos": total_videos,
        "unique_titles": len(title_groups),
        "duplicate_groups_count": len(duplicate_groups),
        "affected_videos_count": affected_videos,
        "duplicate_groups": duplicate_groups,
        "proposed_corrections": corrections
    }


def generate_reports():
    data = analyze_titles()
    if not data:
        return

    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    os.makedirs(os.path.dirname(PROPOSED_JSON), exist_ok=True)

    # Save JSON proposed corrections
    with open(PROPOSED_JSON, "w", encoding="utf-8") as f:
        json.dump(data["proposed_corrections"], f, ensure_ascii=False, indent=2)

    # Save Markdown Report
    lines = [
        "# Duplicate Title Audit & Proposed Corrections Report",
        "",
        f"**Channel:** Fun Learning Kids (`UCcOA6heUaTbOUnx7ERF23Gw`)  ",
        f"**Total Uploads Audited:** {data['total_videos']}  ",
        f"**Unique Title Strings:** {data['unique_titles']}  ",
        f"**Duplicate Title Groups:** {data['duplicate_groups_count']}  ",
        f"**Affected Uploads:** {data['affected_videos_count']} ({data['affected_videos_count'] / data['total_videos'] * 100:.1f}%)  ",
        "",
        "> [!IMPORTANT]",
        "> Per channel safety policy, **NO live YouTube videos have been modified, renamed, or privatized.**",
        "> This document is an audit and proposed correction roster requiring user approval before any YouTube Studio edit.",
        "",
        "## Summary of Duplicate Title Groups",
        "",
        "| # | Duplicate Title | Repeated Count | Affected Video IDs |",
        "| :--- | :--- | :--- | :--- |"
    ]

    sorted_groups = sorted(data["duplicate_groups"].items(), key=lambda x: len(x[1]), reverse=True)
    for i, (title, vids) in enumerate(sorted_groups, 1):
        vid_ids = ", ".join(f"`{v.get('video_id')}`" for v in vids[:6])
        if len(vids) > 6:
            vid_ids += f" (+{len(vids) - 6} more)"
        clean_display_title = title.replace("|", "\\|")
        lines.append(f"| {i} | {clean_display_title} | **{len(vids)}** | {vid_ids} |")

    lines.extend([
        "",
        "## Proposed Title Corrections (Safe Roster)",
        "",
        "Below is the proposed distinct title roster adding legitimate episode/part numbers while remaining under the 100-character YouTube limit:",
        "",
        "| Video ID | Published | Current Title | Proposed Distinct Title |",
        "| :--- | :--- | :--- | :--- |"
    ])

    for c in data["proposed_corrections"][:40]:  # Show top 40 examples
        c_title = c["current_title"].replace("|", "\\|")
        p_title = c["proposed_title"].replace("|", "\\|")
        lines.append(f"| `{c['video_id']}` | {c['published_date']} | {c_title} | **{p_title}** |")

    if len(data["proposed_corrections"]) > 40:
        lines.append(f"\n*(Complete list of all {len(data['proposed_corrections'])} proposed titles saved to `{PROPOSED_JSON}`)*")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Duplicate Title Audit complete:")
    print(f"   • Total Videos: {data['total_videos']}")
    print(f"   • Duplicate Groups: {data['duplicate_groups_count']}")
    print(f"   • Affected Videos: {data['affected_videos_count']}")
    print(f"   • Markdown report: {OUTPUT_MD}")
    print(f"   • Proposed JSON:   {PROPOSED_JSON}")


if __name__ == "__main__":
    generate_reports()
