"""
branding/generate_branding_assets.py
-----------------------------------
Generates high-resolution, production-grade visual branding assets for
Nanhe Seekho Club (नन्हे सीखो क्लब):
1. Profile Picture / Avatar (800x800 circular safe)
2. YouTube Channel Banner (2560x1440 with 1546x423 mobile-safe zone)
3. Video Watermark / Corner Stamp (150x150)
"""

import os
import sys
import math

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont

BRANDING_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = r"C:\Windows\Fonts"

# Color Palette
SUNSHINE_YELLOW = (255, 214, 102)     # #FFD666
SKY_BLUE = (17, 138, 178)              # #118AB2
DEEP_NAVY = (7, 59, 76)                # #073B4C
CORAL_PINK = (239, 71, 111)            # #EF476F
EMERALD_GREEN = (6, 214, 160)          # #06D6A0
CLOUD_WHITE = (255, 255, 255)
CREAM_BG = (255, 250, 240)


def get_font(font_name, size):
    """Safely retrieves a Windows font or falls back gracefully."""
    font_path = os.path.join(FONTS_DIR, font_name)
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    for fb in ["ARIALUNI.TTF", "segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"]:
        p = os.path.join(FONTS_DIR, fb)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def get_hindi_font(size):
    """Specifically uses Arial Unicode MS for clean Devanagari Hindi text."""
    p = os.path.join(FONTS_DIR, "ARIALUNI.TTF")
    if os.path.exists(p):
        return ImageFont.truetype(p, size)
    return get_font("segoeuib.ttf", size)


def draw_smooth_circle(draw, center, radius, fill_color, outline_color=None, outline_width=0):
    """Draws a circle."""
    cx, cy = center
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.ellipse(bbox, fill=fill_color, outline=outline_color, width=outline_width)


def draw_rounded_card(draw, box, radius, fill_color, outline_color=None, outline_width=0):
    """Draws a pill or rounded rectangle."""
    draw.rounded_rectangle(box, radius=radius, fill=fill_color, outline=outline_color, width=outline_width)


def draw_star(draw, center, outer_r, inner_r, fill_color, outline_color=None, outline_width=0):
    """Draws a mathematically perfect 5-pointed star."""
    cx, cy = center
    points = []
    for i in range(10):
        r = outer_r if i % 2 == 0 else inner_r
        angle = i * math.pi / 5 - math.pi / 2
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=fill_color, outline=outline_color, width=outline_width)


def draw_sparkle(draw, center, size, fill_color):
    """Draws a 4-pointed diamond sparkle."""
    cx, cy = center
    points = [
        (cx, cy - size),
        (cx + size * 0.3, cy - size * 0.3),
        (cx + size, cy),
        (cx + size * 0.3, cy + size * 0.3),
        (cx, cy + size),
        (cx - size * 0.3, cy + size * 0.3),
        (cx - size, cy),
        (cx - size * 0.3, cy - size * 0.3)
    ]
    draw.polygon(points, fill=fill_color)


def create_profile_picture(output_path):
    """
    Creates an 800x800 YouTube Channel Profile Picture.
    """
    size = (800, 800)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = 400, 400
    outer_r = 385
    draw_smooth_circle(draw, (cx, cy), outer_r, fill_color=SKY_BLUE)
    draw_smooth_circle(draw, (cx, cy), outer_r - 12, fill_color=CORAL_PINK)
    draw_smooth_circle(draw, (cx, cy), outer_r - 24, fill_color=SUNSHINE_YELLOW)
    draw_smooth_circle(draw, (cx, cy), outer_r - 40, fill_color=CREAM_BG)

    # Decorative background bubbles
    bubbles = [
        ((220, 200), 50, (17, 138, 178, 45)),
        ((590, 210), 55, (239, 71, 111, 45)),
        ((190, 580), 52, (6, 214, 160, 45)),
        ((610, 570), 50, (255, 214, 102, 75)),
        ((400, 150), 35, (239, 71, 111, 55)),
    ]
    for pos, r, col in bubbles:
        draw_smooth_circle(draw, pos, r, fill_color=col)

    # Vector stars & sparkles
    draw_star(draw, (220, 195), 26, 11, fill_color=CORAL_PINK)
    draw_star(draw, (590, 205), 28, 12, fill_color=SKY_BLUE)
    draw_sparkle(draw, (190, 575), 24, fill_color=EMERALD_GREEN)
    draw_sparkle(draw, (610, 565), 24, fill_color=DEEP_NAVY)

    # Center Brand Card
    badge_w, badge_h = 600, 250
    badge_box = [cx - badge_w // 2, cy - 90, cx + badge_w // 2, cy + 155]
    draw_rounded_card(draw, badge_box, radius=36, fill_color=CLOUD_WHITE, outline_color=SKY_BLUE, outline_width=6)

    # Top pill with Devanagari Hindi text
    top_pill = [cx - 200, cy - 132, cx + 200, cy - 72]
    draw_rounded_card(draw, top_pill, radius=24, fill_color=CORAL_PINK)

    hindi_font = get_hindi_font(30)
    draw.text((cx, cy - 102), "नन्हे सीखो क्लब", font=hindi_font, fill=CLOUD_WHITE, anchor="mm")

    # Main Brand Name
    title_font = get_font("trebucbd.ttf", 56)
    draw.text((cx, cy - 25), "NANHE SEEKHO", font=title_font, fill=DEEP_NAVY, anchor="mm")

    # Club with vector stars
    club_font = get_font("trebucbd.ttf", 46)
    draw.text((cx, cy + 42), "CLUB", font=club_font, fill=SKY_BLUE, anchor="mm")
    draw_star(draw, (cx - 95, cy + 42), 16, 7, fill_color=CORAL_PINK)
    draw_star(draw, (cx + 95, cy + 42), 16, 7, fill_color=CORAL_PINK)

    # Tagline Pill
    tag_pill = [cx - 250, cy + 92, cx + 250, cy + 138]
    draw_rounded_card(draw, tag_pill, radius=18, fill_color=SUNSHINE_YELLOW)
    tag_font = get_font("segoeuib.ttf", 26)
    draw.text((cx, cy + 115), "Little Minds, Big Discoveries!", font=tag_font, fill=DEEP_NAVY, anchor="mm")

    img.save(output_path, format="PNG")
    print(f"✅ Created Profile Picture: {output_path} ({size[0]}x{size[1]})")


def create_channel_banner(output_path):
    """
    Creates a 2560x1440 YouTube Channel Banner.
    Conforms strictly to YouTube Specifications:
    - Total Canvas: 2560 x 1440 (TV display)
    - Mobile Safe Area: 1546 x 423 centered (X: 507 to 2053, Y: 508 to 931)
    """
    canvas_w, canvas_h = 2560, 1440
    img = Image.new("RGBA", (canvas_w, canvas_h), (245, 248, 252, 255))
    draw = ImageDraw.Draw(img)

    # TV Background Gradient
    for y in range(canvas_h):
        r = int(230 + (255 - 230) * (y / canvas_h))
        g = int(242 + (250 - 242) * (y / canvas_h))
        b = int(250 + (255 - 250) * (y / canvas_h))
        draw.line([(0, y), (canvas_w, y)], fill=(r, g, b, 255))

    safe_w, safe_h = 1546, 423
    safe_x1 = (canvas_w - safe_w) // 2  # 507
    safe_y1 = (canvas_h - safe_h) // 2  # 508
    safe_x2 = safe_x1 + safe_w          # 2053
    safe_y2 = safe_y1 + safe_h          # 931
    cx = canvas_w // 2                  # 1280
    cy = canvas_h // 2                  # 720

    # Draw Banner Band across safe height
    band_y1 = safe_y1 - 10
    band_y2 = safe_y2 + 10
    draw.rectangle([0, band_y1, canvas_w, band_y2], fill=(255, 255, 255, 255))

    # Top and bottom colored stripes
    draw.rectangle([0, band_y1, canvas_w, band_y1 + 12], fill=SUNSHINE_YELLOW)
    draw.rectangle([0, band_y1 + 12, canvas_w, band_y1 + 22], fill=SKY_BLUE)
    draw.rectangle([0, band_y2 - 22, canvas_w, band_y2 - 12], fill=CORAL_PINK)
    draw.rectangle([0, band_y2 - 12, canvas_w, band_y2], fill=EMERALD_GREEN)

    # Soft Background Bubbles inside Safe Area
    decorations = [
        ((safe_x1 + 120, cy - 80), 90, (17, 138, 178, 30)),
        ((safe_x1 + 180, cy + 90), 65, (255, 214, 102, 60)),
        ((safe_x2 - 140, cy - 70), 85, (239, 71, 111, 30)),
        ((safe_x2 - 200, cy + 90), 70, (6, 214, 160, 40)),
    ]
    for pos, r, col in decorations:
        draw_smooth_circle(draw, pos, r, fill_color=col)

    # Left Badge (Discovery / Wonder)
    left_cx = safe_x1 + 220
    draw_smooth_circle(draw, (left_cx, cy), 125, fill_color=SUNSHINE_YELLOW, outline_color=CLOUD_WHITE, outline_width=6)
    draw_smooth_circle(draw, (left_cx, cy), 100, fill_color=CLOUD_WHITE)
    draw_star(draw, (left_cx, cy - 14), 48, 22, fill_color=CORAL_PINK)
    sub_star = get_font("segoeuib.ttf", 22)
    draw.text((left_cx, cy + 44), "DISCOVER", font=sub_star, fill=DEEP_NAVY, anchor="mm")

    # Right Badge (Learning / Fun)
    right_cx = safe_x2 - 220
    draw_smooth_circle(draw, (right_cx, cy), 125, fill_color=EMERALD_GREEN, outline_color=CLOUD_WHITE, outline_width=6)
    draw_smooth_circle(draw, (right_cx, cy), 100, fill_color=CLOUD_WHITE)
    draw_sparkle(draw, (right_cx, cy - 14), 44, fill_color=SKY_BLUE)
    draw.text((right_cx, cy + 44), "LEARN & GROW", font=sub_star, fill=DEEP_NAVY, anchor="mm")

    # Center Hindi Pill with Arial Unicode MS
    hi_pill = [cx - 260, cy - 150, cx + 260, cy - 90]
    draw_rounded_card(draw, hi_pill, radius=24, fill_color=CORAL_PINK)
    hi_font = get_hindi_font(34)
    draw.text((cx, cy - 120), "नन्हे सीखो क्लब", font=hi_font, fill=CLOUD_WHITE, anchor="mm")
    draw_star(draw, (cx - 200, cy - 120), 14, 6, fill_color=SUNSHINE_YELLOW)
    draw_star(draw, (cx + 200, cy - 120), 14, 6, fill_color=SUNSHINE_YELLOW)

    # Main Channel Name
    name_font = get_font("trebucbd.ttf", 88)
    draw.text((cx, cy - 32), "NANHE SEEKHO CLUB", font=name_font, fill=DEEP_NAVY, anchor="mm")

    # Tagline with star badges
    tag_font = get_font("segoeuib.ttf", 36)
    draw.text((cx, cy + 42), "Little Minds, Big Discoveries!", font=tag_font, fill=SKY_BLUE, anchor="mm")
    draw_star(draw, (cx - 310, cy + 42), 16, 7, fill_color=CORAL_PINK)
    draw_star(draw, (cx + 310, cy + 42), 16, 7, fill_color=CORAL_PINK)

    # Schedule Pill
    sched_box = [cx - 520, cy + 90, cx + 520, cy + 148]
    draw_rounded_card(draw, sched_box, radius=28, fill_color=SUNSHINE_YELLOW, outline_color=DEEP_NAVY, outline_width=3)
    sched_font = get_font("segoeuib.ttf", 25)
    draw.text(
        (cx, cy + 119),
        "NEW SHORTS DAILY AT 9:00 AM  •  SPECIAL STORIES WED & SUN AT 5:00 PM",
        font=sched_font,
        fill=DEEP_NAVY,
        anchor="mm"
    )

    img.save(output_path, format="PNG")
    print(f"✅ Created Channel Banner: {output_path} ({canvas_w}x{canvas_h})")


def create_watermark(output_path):
    """Creates a 150x150 corner watermark."""
    size = (150, 150)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = 75, 75
    draw_smooth_circle(draw, (cx, cy), 70, fill_color=CORAL_PINK, outline_color=CLOUD_WHITE, outline_width=4)
    draw_smooth_circle(draw, (cx, cy), 60, fill_color=SUNSHINE_YELLOW)

    font_top = get_font("trebucbd.ttf", 24)
    font_bot = get_font("trebucbd.ttf", 20)
    draw.text((cx, cy - 14), "NANHE", font=font_top, fill=DEEP_NAVY, anchor="mm")
    draw.text((cx, cy + 14), "SEEKHO", font=font_bot, fill=SKY_BLUE, anchor="mm")

    img.save(output_path, format="PNG")
    print(f"✅ Created Watermark: {output_path} ({size[0]}x{size[1]})")


if __name__ == "__main__":
    pfp_path = os.path.join(BRANDING_DIR, "profile_picture.png")
    banner_path = os.path.join(BRANDING_DIR, "channel_banner.png")
    watermark_path = os.path.join(BRANDING_DIR, "watermark.png")

    create_profile_picture(pfp_path)
    create_channel_banner(banner_path)
    create_watermark(watermark_path)
    print("\n🎉 All visual branding assets generated with crisp vector stars and Hindi support!")
