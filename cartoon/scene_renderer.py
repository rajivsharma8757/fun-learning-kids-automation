"""
scene_renderer.py
-----------------
Renders animated 2D scenes for "Fun Learning Kids" Cartoon Module.
Composites backgrounds, kinematic character rigs (Chintu Bunny, Golu Bear),
animated props, particle effects, and camera pans/zooms.
Pipes raw RGB24 frames into FFmpeg for high-speed H.264/AAC encoding.
"""

import os
import sys
import math
import subprocess
import json
import time
import numpy as np
from PIL import Image

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import (
    WIDTH, HEIGHT, FPS, BACKGROUNDS_DIR, PROPS_DIR,
    AUDIO_DIR, OUTPUT_DIR
)
from cartoon.character_rig import CharacterRig


class SceneRenderer:
    def __init__(self, background_name=None, character=None):
        self.rig = CharacterRig()
        self.character = character or "chintu"
        bg_name = background_name or "forest_meadow"
        bg_path = os.path.join(BACKGROUNDS_DIR, f"{bg_name}.png")
        if not os.path.exists(bg_path):
            bg_path = os.path.join(BACKGROUNDS_DIR, "forest_meadow.png")
        self.bg_meadow = Image.open(bg_path).convert("RGBA")
        self.tree = Image.open(os.path.join(BACKGROUNDS_DIR, "oak_tree.png")).convert("RGBA")
        self.props = {
            "apple_whole": Image.open(os.path.join(PROPS_DIR, "apple_whole.png")).convert("RGBA"),
            "sparkle": Image.open(os.path.join(PROPS_DIR, "sparkle_gold.png")).convert("RGBA"),
            "music_note": Image.open(os.path.join(PROPS_DIR, "music_note.png")).convert("RGBA"),
        }

    def render_frame(self, t, timing_metadata):
        # 1. Determine active scene and narration state
        active_scene = 1
        for i, item in enumerate(timing_metadata):
            next_start = timing_metadata[i + 1]["start_time"] if i + 1 < len(timing_metadata) else 999999.0
            if t < next_start:
                active_scene = item["scene_id"]
                break
        else:
            active_scene = timing_metadata[-1]["scene_id"]

        is_speech = any(item["start_time"] <= t <= (item["end_time"] + 0.15) for item in timing_metadata)

        # Default camera settings
        cam_x, cam_y, zoom = 200, 200, 1.0

        # Scene-specific camera & character kinematics
        if active_scene == 1:
            # Scene 1: Hook - gentle push-in zoom, Chintu hopping from left to center
            s_prog = min(1.0, max(0.0, t / 5.6))
            zoom = 1.0 + s_prog * 0.12
            cam_x = int(120 + s_prog * 100)
            cam_y = int(220 + s_prog * 40)

            # Chintu hops across meadow
            c_x = int(60 + s_prog * 480)
            c_y = 270
            c_im = self.rig.render_character(self.character, t, action="hop", facing=1, scale=0.85, is_speaking=is_speech)
            g_im = None
            tree_pos = None

        elif active_scene == 2:
            # Scene 2: Discovery - Tree on right, Chintu admiring then picking apple
            s_prog = min(1.0, max(0.0, (t - 5.85) / 8.0))
            zoom = 1.15
            cam_x = 340
            cam_y = 250
            tree_pos = (780, 50)

            if s_prog < 0.35:
                # Walking to tree
                c_x = int(320 + s_prog * 300)
                c_y = 260
                c_im = self.rig.render_character(self.character, t, action="hop", facing=1, scale=0.88, is_speaking=is_speech)
            elif s_prog < 0.6:
                # Bending/reaching for apple
                c_x = 425
                c_y = 265
                c_im = self.rig.render_character(self.character, t, action="give", facing=1, scale=0.88, is_speaking=is_speech)
            else:
                # Proudly holding apple
                c_x = 430
                c_y = 260
                c_im = self.rig.render_character(self.character, 
                    t, action="hold", eye_state="wide", mouth_state="smile",
                    held_item="apple_whole", facing=1, scale=0.88, is_speaking=is_speech
                )
            g_im = None

        elif active_scene == 3:
            # Scene 3: Conflict - Golu Bear arrives hungry & sad
            s_prog = min(1.0, max(0.0, (t - 14.1) / 6.5))
            zoom = 1.12
            cam_x = 320
            cam_y = 240
            tree_pos = (840, 50)

            # Chintu holding apple on left
            c_x, c_y = 330, 260
            c_im = self.rig.render_character(self.character, 
                t, action="hold", eye_state="open", held_item="apple_whole",
                facing=1, scale=0.85, is_speaking=is_speech
            )

            # Golu walks in from right holding tummy
            g_x = int(980 - s_prog * 250)
            g_y = 255
            g_im = self.rig.render_golu(
                t, action="sad_idle", eye_state="sad", mouth_state="sad",
                facing=-1, scale=0.88, is_speaking=False
            )

        elif active_scene == 4:
            # Scene 4: The WOW Moment - Chintu shares half the apple
            s_prog = min(1.0, max(0.0, (t - 20.876) / 6.8))
            zoom = 1.25
            cam_x = 350
            cam_y = 235
            tree_pos = None

            c_x = int(340 + min(s_prog * 2.0, 1.0) * 110)
            c_y = 255
            c_im = self.rig.render_character(self.character, 
                t, action="give", eye_state="happy",
                held_item="apple_half_chintu", facing=1, scale=0.90, is_speaking=is_speech
            )

            g_x, g_y = 710, 250
            g_eye = "sad" if s_prog < 0.3 else "happy"
            g_mouth = "sad" if s_prog < 0.3 else "smile"
            g_im = self.rig.render_golu(
                t, action="receive", eye_state=g_eye, mouth_state=g_mouth,
                held_item="apple_half_golu" if s_prog > 0.45 else None,
                facing=-1, scale=0.92, is_speaking=False
            )

        elif active_scene == 5:
            # Scene 5: Celebration - Both munch & dance with joy
            zoom = 1.15
            cam_x = 320
            cam_y = 230
            tree_pos = None

            c_x, c_y = 410, 255
            c_im = self.rig.render_character(self.character, 
                t, action="celebrate", eye_state="happy", mouth_state="wide_e",
                held_item="apple_half_chintu", facing=1, scale=0.88, is_speaking=is_speech
            )

            g_x, g_y = 730, 250
            g_im = self.rig.render_golu(
                t, action="celebrate", eye_state="happy", mouth_state="wide_e",
                held_item="apple_half_golu", facing=-1, scale=0.90, is_speaking=False
            )

        else:
            # Scene 6: Moral & Outro - Camera pulls back, both wave to camera
            s_prog = min(1.0, max(0.0, (t - 32.3) / 6.6))
            zoom = max(1.0, 1.15 - s_prog * 0.15)
            cam_x = int(320 - s_prog * 120)
            cam_y = int(230 - s_prog * 30)
            tree_pos = None

            c_x, c_y = 480, 270
            c_im = self.rig.render_character(self.character, 
                t, action="wave", eye_state="happy", mouth_state="smile",
                facing=1, scale=0.85, is_speaking=is_speech
            )

            g_x, g_y = 710, 265
            g_im = self.rig.render_golu(
                t, action="wave", eye_state="happy", mouth_state="smile",
                facing=-1, scale=0.88, is_speaking=False
            )

        # 2. Camera Viewport Crop & Resize from Background
        crop_w = int(WIDTH / zoom)
        crop_h = int(HEIGHT / zoom)
        crop_x = max(0, min(self.bg_meadow.width - crop_w, cam_x))
        crop_y = max(0, min(self.bg_meadow.height - crop_h, cam_y))

        cropped_bg = self.bg_meadow.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
        frame = cropped_bg.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

        # 3. Composite Tree if present in scene
        if tree_pos:
            tx = int((tree_pos[0] - crop_x) * zoom)
            ty = int((tree_pos[1] - crop_y) * zoom)
            scaled_tree = self.tree.resize(
                (int(self.tree.width * zoom * 0.8), int(self.tree.height * zoom * 0.8)),
                Image.Resampling.LANCZOS
            )
            frame.alpha_composite(scaled_tree, (tx, ty))

        # Static Apple on ground in Scene 2 before pickup
        if active_scene == 2:
            s_prog = (t - 5.85) / 8.0
            if s_prog < 0.45:
                ax = int((680 - crop_x) * zoom)
                ay = int((520 - crop_y) * zoom)
                apple_sc = self.props["apple_whole"].resize(
                    (int(130 * zoom), int(130 * zoom)), Image.Resampling.LANCZOS
                )
                frame.alpha_composite(apple_sc, (ax, ay))

        # 4. Composite Chintu
        cx_screen = int((c_x - crop_x) * zoom)
        cy_screen = int((c_y - crop_y) * zoom)
        frame.alpha_composite(c_im, (cx_screen, cy_screen))

        # 5. Composite Golu
        if g_im:
            gx_screen = int((g_x - crop_x) * zoom)
            gy_screen = int((g_y - crop_y) * zoom)
            frame.alpha_composite(g_im, (gx_screen, gy_screen))

        # 6. Dynamic Visual Particles
        if active_scene == 4:
            # Golden Sparkle burst on sharing
            sp = self.props["sparkle"]
            for s_idx, (ox, oy, sz) in enumerate([(0, -30, 80), (-50, 20, 60), (50, 15, 65), (-20, -70, 50), (30, -60, 55)]):
                pulse = 0.8 + 0.3 * math.sin(t * 10.0 + s_idx)
                cur_sz = int(sz * pulse)
                sp_sc = sp.resize((cur_sz, cur_sz), Image.Resampling.LANCZOS)
                sp_x = int(cx_screen + 240 + ox - cur_sz // 2)
                sp_y = int(cy_screen + 190 + oy - cur_sz // 2)
                frame.alpha_composite(sp_sc, (sp_x, sp_y))

        elif active_scene == 5:
            # Floating musical notes
            mn = self.props["music_note"]
            for n_idx, (base_x, speed, y_off) in enumerate([(480, 55, 0), (620, 45, 60), (780, 60, 30), (550, 50, 90)]):
                note_y = int(580 - ((t * speed + y_off) % 360))
                note_x = int(base_x + math.sin(t * 3.0 + n_idx) * 25)
                frame.alpha_composite(mn, (note_x, note_y))

        return frame.convert("RGB")

    def render_animation_video(self, timing_metadata, audio_path, srt_path, output_video_path):
        total_duration = timing_metadata[-1]["end_time"] + 0.5
        total_frames = int(total_duration * FPS)

        print(f"🎬 Rendering {total_frames} frames ({total_duration:.2f}s) at {FPS} FPS...")

        clean_srt = srt_path.replace("\\", "/").replace(":", "\\:")
        sub_filter = (
            f"subtitles='{clean_srt}':force_style="
            f"'Fontname=Arial,Fontsize=22,PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00201010,Outline=2.5,Shadow=1.5,MarginV=36,Alignment=2'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-nostats",
            "-loglevel", "warning",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{WIDTH}x{HEIGHT}",
            "-pix_fmt", "rgb24",
            "-r", str(FPS),
            "-i", "pipe:0",
            "-i", audio_path,
            "-vf", sub_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_video_path
        ]

        ffmpeg_log = os.path.join(OUTPUT_DIR, "ffmpeg_render.log")
        with open(ffmpeg_log, "w", encoding="utf-8") as f_err:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=f_err)

            t_start = time.time()

            for i in range(total_frames):
                t = i / float(FPS)
                frame_rgb = self.render_frame(t, timing_metadata)
                raw_bytes = frame_rgb.tobytes()
                proc.stdin.write(raw_bytes)
                if i > 0 and i % 150 == 0:
                    cur_fps = i / (time.time() - t_start + 0.001)
                    pct = (i / total_frames) * 100
                    print(f"  Frame {i}/{total_frames} ({pct:.1f}%) | Render speed: {cur_fps:.1f} fps", flush=True)

            proc.stdin.close()
            proc.wait()

        if proc.returncode != 0:
            err_msg = ""
            if os.path.exists(ffmpeg_log):
                with open(ffmpeg_log, "r", encoding="utf-8", errors="replace") as f_err:
                    err_msg = f_err.read()
            raise RuntimeError(f"FFmpeg encoding failed (exit {proc.returncode}):\n{err_msg[-600:]}")

        elapsed = time.time() - t_start
        file_size = os.path.getsize(output_video_path)
        print(f"✅ Cartoon video successfully rendered: {output_video_path}", flush=True)
        print(f"   Size: {file_size:,} bytes | Elapsed: {elapsed:.2f}s ({total_frames / elapsed:.1f} fps)", flush=True)
        return output_video_path


if __name__ == "__main__":
    timing_file = os.path.join(AUDIO_DIR, "timing_metadata.json")
    with open(timing_file, "r", encoding="utf-8") as f:
        timing_meta = json.load(f)

    audio_file = os.path.join(AUDIO_DIR, "final_master_audio.wav")
    srt_file = os.path.join(OUTPUT_DIR, "demo_subtitles.srt")
    out_file = os.path.join(OUTPUT_DIR, "demo_chintu_shares.mp4")

    renderer = SceneRenderer()
    renderer.render_animation_video(timing_meta, audio_file, srt_file, out_file)
