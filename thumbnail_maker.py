import os
import sys
from PIL import Image, ImageDraw, ImageFont
from config import THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, CHANNEL_NAME

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TOPIC_COLORS = {
    "moral_story": {"primary": (255, 179, 0), "text": (255, 255, 255), "label": "MORAL STORY 🐰"},
    "animal_story": {"primary": (76, 175, 80), "text": (255, 255, 255), "label": "ANIMAL STORY 🦊"},
    "good_habits": {"primary": (3, 169, 244), "text": (255, 255, 255), "label": "GOOD HABITS ✨"},
    "abc": {"primary": (156, 39, 176), "text": (255, 255, 255), "label": "ABC LEARNING 🔤"},
    "numbers": {"primary": (233, 30, 99), "text": (255, 255, 255), "label": "NUMBERS FUN 🔢"}
}

def get_font(size):
    font_candidates = [
        "C:/Windows/Fonts/comicbd.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arial.ttf"
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def create_thumbnail(image_path, topic, short_title, output_thumb_path, format_profile=None):
    """
    Creates an eye-catching, kid-friendly YouTube thumbnail (1280x720 landscape or 1080x1920 shorts).
    - Crops and centers the topic image
    - Adds vibrant category banner and story title
    - Adds channel watermark badge
    """
    from config import FORMAT_PROFILES, DEFAULT_FORMAT
    prof = FORMAT_PROFILES.get(format_profile or DEFAULT_FORMAT, FORMAT_PROFILES[DEFAULT_FORMAT])
    thumb_w = prof['thumbnail_width']
    thumb_h = prof['thumbnail_height']

    try:
        os.makedirs(os.path.dirname(output_thumb_path), exist_ok=True)
        img = Image.open(image_path).convert("RGBA")

        # Scale and crop to fit target aspect ratio
        target_aspect = thumb_w / thumb_h
        im_aspect = img.width / img.height

        if im_aspect > target_aspect:
            new_h = thumb_h
            new_w = int(new_h * im_aspect)
        else:
            new_w = thumb_w
            new_h = int(new_w / im_aspect)

        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - thumb_w) // 2
        top = (new_h - thumb_h) // 2
        thumb = resized.crop((left, top, left + thumb_w, top + thumb_h))

        # Create overlay for text
        overlay = Image.new("RGBA", thumb.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        info = TOPIC_COLORS.get(topic, {
            "primary": (255, 152, 0),
            "text": (255, 255, 255),
            "label": topic.upper()
        })
        primary_col = info["primary"]

        # Dynamic font scaling and placement based on format
        is_shorts = (thumb_h > 1000)
        if is_shorts:
            font_large = get_font(68)
            font_med = get_font(48)
            font_badge = get_font(36)
            banner_y = thumb_h - 420  # Safe zone above YouTube Shorts title/UI overlay
            margin_x = 50
        else:
            font_large = get_font(52)
            font_med = get_font(42)
            font_badge = get_font(30)
            banner_y = thumb_h - 170
            margin_x = 40

        # 1. Top Category Pill / Banner
        category_text = info["label"]
        cat_box = draw.textbbox((0, 0), category_text, font=font_med)
        cat_w = cat_box[2] - cat_box[0]
        cat_h = cat_box[3] - cat_box[1]

        pill_pad_x, pill_pad_y = 30, 15
        draw.rounded_rectangle(
            [margin_x, margin_x, margin_x + cat_w + pill_pad_x * 2, margin_x + cat_h + pill_pad_y * 2],
            radius=15,
            fill=(*primary_col, 240),
            outline=(255, 255, 255, 255),
            width=3
        )
        draw.text((margin_x + pill_pad_x, margin_x + pill_pad_y - 4), category_text, font=font_med, fill=(255, 255, 255, 255))

        # 2. Main Title Banner
        title_text = short_title.upper()
        title_box = draw.textbbox((0, 0), title_text, font=font_large)
        title_w = title_box[2] - title_box[0]
        title_h = title_box[3] - title_box[1]

        banner_w = min(title_w + 60, thumb_w - (margin_x * 2))

        # Background shadow card for title
        draw.rounded_rectangle(
            [margin_x, banner_y, margin_x + banner_w, banner_y + title_h + 35],
            radius=18,
            fill=(0, 0, 0, 210),
            outline=(255, 255, 255, 240),
            width=4
        )
        # Title text with outline
        draw.text(
            (margin_x + 20, banner_y + 12),
            title_text,
            font=font_large,
            fill=(255, 235, 59, 255), # Bright golden yellow
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255)
        )

        # 3. Channel Watermark Pill (Bottom Right)
        wm_text = CHANNEL_NAME.upper()
        wm_box = draw.textbbox((0, 0), wm_text, font=font_badge)
        wm_w = wm_box[2] - wm_box[0]
        wm_h = wm_box[3] - wm_box[1]

        wm_x = thumb_w - wm_w - 65
        wm_y = thumb_h - 75 if is_shorts else thumb_h - 65
        draw.rounded_rectangle(
            [wm_x, wm_y, thumb_w - 30, wm_y + wm_h + 20],
            radius=10,
            fill=(233, 30, 99, 235), # Pink/Magenta kids pill
            outline=(255, 255, 255, 230),
            width=2
        )
        draw.text((wm_x + 15, wm_y + 4), wm_text, font=font_badge, fill=(255, 255, 255, 255))

        # Composite and save
        final_thumb = Image.alpha_composite(thumb, overlay).convert("RGB")
        final_thumb.save(output_thumb_path, "JPEG", quality=95)
        print(f"✅ Thumbnail created successfully: {output_thumb_path}")
        return True, output_thumb_path

    except Exception as e:
        print(f"❌ Thumbnail creation error: {e}")
        return False, str(e)

if __name__ == "__main__":
    from content_manager import ContentManager
    cm = ContentManager()
    img = cm.get_topic_images("moral_story")[0]
    out = os.path.join("thumbnails", "test_thumb.jpg")
    ok, path = create_thumbnail(img, "moral_story", "The Kind Rabbit", out)
    print("Success:", ok)
    if ok and os.path.exists(out):
        os.remove(out)
