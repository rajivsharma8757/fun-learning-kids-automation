"""
scene_renderer_v3.py
--------------------
Studio-grade Scene Compositor & Renderer for Cartoon V3: "Mimi's Magic Toy Train".

Architecture:
1. Multi-plane Parallax Compositor:
   - Far Layer: Playroom wall, window, sunny yard, shelving (Parallax 0.35).
   - Midground Layer: Hardwood floor, green play rug, wooden rail circuit (Parallax 1.0).
   - Character & Prop Plane: Mimi the Kitten + Wooden Steam Train + Steam Puffs + Golden Sparkles.
   - Foreground Framing Layer: Soft-blurred potted plant leaves (Parallax 1.35).
2. Physical Acting Choreography across 6 continuous scenes.
3. Track-following toy train kinematics (x(t), y(t), theta(t)) with spinning wheels.
4. Dynamic particle systems:
   - Expanding, fading steam clouds from chimney.
   - Rotating golden sparkle bursts.
   - Ambient floating sunbeam dust motes.
5. Non-blocking FFmpeg rawvideo pipe encoding to H.264/AAC with synchronized subtitles.
"""

import os
import sys
import time
import math
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import (
    CARTOON_DIR,
    OUTPUT_DIR,
    WIDTH,
    HEIGHT,
    FPS,
)
from cartoon.character_rig_v3 import CharacterRigV3, ease_in_out_quad, ease_out_bounce

ASSETS_V3_DIR = os.path.join(CARTOON_DIR, "assets_v3")
BG_DIR = os.path.join(ASSETS_V3_DIR, "backgrounds")
PROPS_DIR = os.path.join(ASSETS_V3_DIR, "props")
AUDIO_V3_DIR = os.path.join(ASSETS_V3_DIR, "audio")


class SceneRendererV3:
    def __init__(self):
        self.rig = CharacterRigV3()
        self._load_environment()

    def _load_environment(self):
        # 1. Multi-plane background layers (1920x1080)
        self.bg_far = Image.open(os.path.join(BG_DIR, "bg_playroom_far.png")).convert("RGBA")
        self.bg_mid = Image.open(os.path.join(BG_DIR, "bg_playroom_mid.png")).convert("RGBA")
        self.bg_fg = Image.open(os.path.join(BG_DIR, "bg_playroom_fg.png")).convert("RGBA")

        # 2. Environmental Sprites
        self.spr_steam = Image.open(os.path.join(PROPS_DIR, "steam_cloud.png")).convert("RGBA")
        self.spr_sparkle = Image.open(os.path.join(PROPS_DIR, "sparkle_gold.png")).convert("RGBA")

    def render_frame(self, t, timing_metadata):
        """Renders a single high-fidelity 1080p frame at timestamp t."""
        # ---------------------------------------------------------------------
        # 1. Identify Active Scene and Speech Activity
        # ---------------------------------------------------------------------
        active_scene = 1
        for i, item in enumerate(timing_metadata):
            next_start = timing_metadata[i + 1]["start_time"] if i + 1 < len(timing_metadata) else 999999.0
            if t < next_start:
                active_scene = item["scene_id"]
                break
        else:
            active_scene = timing_metadata[-1]["scene_id"]

        is_speech = any(item["start_time"] <= t <= (item["end_time"] + 0.15) for item in timing_metadata)

        # Base camera in world space (1920x1080)
        cam_x, cam_y, zoom = 960, 540, 1.0

        # Mimi Transform
        m_world_x, m_world_y = 500, 480
        m_scale = 0.54
        m_flip = False
        m_tilt = 0.0
        m_squash = (1.0, 1.0)
        m_eye = "open"
        m_mouth = None

        # Train Transform
        t_world_x, t_world_y = 1150, 750
        t_scale = 0.28
        t_flip = False
        t_tilt = 0.0
        t_wheel_rot = 0.0
        show_train = True
        steam_puffs = []
        sparkles = []

        # ---------------------------------------------------------------------
        # 2. Scene Choreography & Physical Kinematics
        # ---------------------------------------------------------------------
        if active_scene == 1:
            # SCENE 1 (0.0 - 6.36s): Playroom Intro & Entrance
            s_dur = 6.36
            s_prog = min(1.0, max(0.0, t / s_dur))

            # Camera: Smooth push-in tracking Mimi entering
            zoom = 1.0 + s_prog * 0.12
            cam_x = int(800 + s_prog * 180)
            cam_y = 540

            # Mimi trots in from left toward center
            walk_dist = 520
            m_world_x = int(180 + s_prog * walk_dist)
            bounce = abs(math.sin(t * 8.5)) * 18.0
            m_world_y = int(500 - bounce)
            m_tilt = math.sin(t * 8.5) * 2.5
            m_squash = (1.0 + math.sin(t * 8.5) * 0.04, 1.0 - math.sin(t * 8.5) * 0.04)
            m_eye = "happy" if (t % 2.0 < 1.0) else "look_right"

            # Train sits idle on floor near blocks
            t_world_x, t_world_y = 1180, 750
            t_scale = 0.28

        elif active_scene == 2:
            # SCENE 2 (6.61 - 13.55s): Discovery & Picking Up
            s_start, s_dur = 6.61, 6.94
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))

            # Camera: Medium close-up on discovery
            zoom = 1.18 + min(0.12, s_prog * 0.15)
            cam_x = 1040
            cam_y = 560

            if s_prog < 0.25:
                # Approaching train
                p = s_prog / 0.25
                m_world_x = int(700 + p * 260)
                bounce = abs(math.sin(t * 8.0)) * 14.0
                m_world_y = int(500 - bounce)
                m_tilt = math.sin(t * 8.0) * 2.0
                m_eye = "look_down"
                t_world_x, t_world_y = 1180, 750
            elif s_prog < 0.50:
                # Crouching down to pick up train
                p = (s_prog - 0.25) / 0.25
                crouch = math.sin(p * math.pi) * 35.0
                m_world_x = 960
                m_world_y = int(500 + crouch * 0.6)
                m_squash = (1.0 + crouch * 0.003, 1.0 - crouch * 0.003)
                m_tilt = 4.0
                m_eye = "look_down"
                t_world_x = 1180 - int(p * 50)
                t_world_y = int(750 - p * 80)
            else:
                # Holding train up with proud curious expression
                p = (s_prog - 0.50) / 0.50
                m_world_x = 960
                breath = math.sin(t * 3.5) * 6.0
                m_world_y = int(500 - breath)
                m_squash = (1.0, 1.0)
                m_eye = "wide" if (p < 0.6) else "happy"
                t_world_x = 1060
                t_world_y = int(620 - breath)
                t_scale = 0.26

        elif active_scene == 3:
            # SCENE 3 (13.80 - 19.65s): Placing on Track
            s_start, s_dur = 13.80, 5.85
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))

            # Camera: Tracking placement onto the green rug track loop
            zoom = 1.20
            cam_x = int(1040 + s_prog * 60)
            cam_y = 570

            if s_prog < 0.45:
                p = s_prog / 0.45
                m_world_x = int(960 + p * 120)
                bounce = abs(math.sin(t * 7.5)) * 12.0
                m_world_y = int(500 - bounce)
                m_eye = "look_down"
                t_world_x = m_world_x + 90
                t_world_y = m_world_y + 110 - int(bounce * 0.5)
                t_scale = 0.26
            elif s_prog < 0.75:
                p = (s_prog - 0.45) / 0.30
                bend = math.sin(p * math.pi) * 30.0
                m_world_x = 1080
                m_world_y = int(500 + bend * 0.5)
                m_squash = (1.0 + bend * 0.003, 1.0 - bend * 0.003)
                m_tilt = 5.0
                m_eye = "look_down"
                t_world_x = 1170
                t_world_y = int(630 + p * 120)
                t_scale = 0.28
            else:
                m_world_x = 1040
                m_world_y = 490
                m_eye = "happy"
                m_mouth = "smile"
                t_world_x, t_world_y = 1170, 750
                t_scale = 0.28

        elif active_scene == 4:
            # SCENE 4 (19.90 - 27.51s): Magic Sparkle, Whistle & Joyful Clapping!
            s_start, s_dur = 19.90, 7.61
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))

            # Camera: Punchy reaction frame
            zoom = 1.24
            cam_x = 1080
            cam_y = 570

            # Train starts vibrating, wheels spin, steam rises!
            t_world_x, t_world_y = 1170, 750
            t_scale = 0.28
            t_wheel_rot = (t - s_start) * 540.0

            # Steam puffs shoot out of chimney
            chimney_x = t_world_x + int(190 * t_scale)
            chimney_y = t_world_y + int(45 * t_scale)
            puff_rate = 0.38
            for puff_i in range(8):
                puff_t = s_start + puff_i * puff_rate + 0.6
                if puff_t <= t:
                    age = t - puff_t
                    if age < 1.4:
                        px = chimney_x - int(age * 45)
                        py = chimney_y - int(age * 75)
                        psz = int(35 + age * 65)
                        palpha = max(0.0, 1.0 - (age / 1.4))
                        steam_puffs.append((px, py, psz, palpha))

            # Golden magic sparkles around train awakening
            if 0.15 <= s_prog <= 0.85:
                for sp_i, (ox, oy, spd) in enumerate([(60, -40, 6.0), (120, 20, -7.0), (30, 40, 8.0), (150, -20, -5.0)]):
                    sp_x = t_world_x + ox
                    sp_y = t_world_y + oy
                    sp_sz = int(55 + math.sin(t * spd + sp_i) * 20)
                    sparkles.append((sp_x, sp_y, sp_sz, t * spd * 20.0))

            # Mimi jumps with joy and claps her paws!
            clap_bounce = abs(math.sin((t - s_start) * 9.0)) * 26.0
            m_world_x = 940
            m_world_y = int(500 - clap_bounce)
            m_squash = (1.0 - clap_bounce * 0.004, 1.0 + clap_bounce * 0.004)
            m_eye = "happy" if (int(t * 4.0) % 2 == 0) else "wide"

        elif active_scene == 5:
            # SCENE 5 (27.76 - 32.85s): Train Chugging Around Track & Mimi Cheering
            s_start, s_dur = 27.76, 5.09
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))

            # Camera: Wide dynamic playroom tracking
            zoom = 1.15
            cam_x = 1000
            cam_y = 560

            # Train moves along elliptical track loop: center (1080, 750), Rx=260, Ry=75
            track_cx, track_cy = 1080, 750
            rx, ry = 250, 70
            omega = 1.35
            ang = (t - s_start) * omega
            t_world_x = int(track_cx + rx * math.cos(ang))
            t_world_y = int(track_cy + ry * math.sin(ang))
            t_wheel_rot = (t - s_start) * 720.0
            t_flip = math.sin(ang) < 0.0

            chim_ox = 60 if not t_flip else -60
            chimney_x = t_world_x + chim_ox
            chimney_y = t_world_y - 20
            for puff_i in range(12):
                puff_t = s_start + puff_i * 0.32
                if puff_t <= t:
                    age = t - puff_t
                    if age < 1.3:
                        px = chimney_x - int(age * 50 * (-1 if t_flip else 1))
                        py = chimney_y - int(age * 60)
                        psz = int(30 + age * 60)
                        palpha = max(0.0, 1.0 - (age / 1.3))
                        steam_puffs.append((px, py, psz, palpha))

            # Mimi happily trots alongside the track cheering!
            m_ang = ang - 0.45
            m_world_x = int(track_cx - 80 + (rx + 90) * math.cos(m_ang))
            m_bounce = abs(math.sin(t * 8.5)) * 18.0
            m_world_y = int(track_cy - 220 + ry * math.sin(m_ang) - m_bounce)
            m_tilt = math.sin(t * 8.5) * 3.0
            m_flip = math.sin(m_ang) < 0.0
            m_eye = "happy"

        elif active_scene == 6:
            # SCENE 6 (33.10 - 39.96s): Outro Moral & Friendly Goodbye Wave
            s_start, s_dur = 33.10, 6.86
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))

            # Camera: Gentle pull-out to wide friendly framing
            zoom = 1.20 - s_prog * 0.14
            cam_x = 1000
            cam_y = 540

            t_world_x, t_world_y = 1200, 750
            t_scale = 0.28
            t_wheel_rot = 0.0

            if int(t * 1.5) % 2 == 0:
                steam_puffs.append((t_world_x + 60, t_world_y - 30, 50, 0.6))

            # Mimi stands proudly in center, swaying with gentle warmth
            m_world_x = 920
            sway = math.sin((t - s_start) * 4.0) * 8.0
            m_world_y = int(480 - abs(math.sin((t - s_start) * 4.0)) * 6.0)
            m_tilt = math.sin((t - s_start) * 4.0) * 3.5
            m_eye = "happy" if (t % 3.0 < 2.0) else "open"

            # Outro golden sparkles
            if s_prog > 0.4:
                for sp_i, (ox, oy, spd) in enumerate([(-180, -60, 4.0), (220, -40, -4.5), (0, -120, 5.0), (140, 80, -5.5)]):
                    sp_x = m_world_x + ox
                    sp_y = m_world_y + oy
                    sp_sz = int(60 + math.sin(t * spd + sp_i) * 18)
                    sparkles.append((sp_x, sp_y, sp_sz, t * spd * 18.0))

        # ---------------------------------------------------------------------
        # 3. Multi-Plane Parallax Compositing
        # ---------------------------------------------------------------------
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

        crop_w = int(WIDTH / zoom)
        crop_h = int(HEIGHT / zoom)

        # Layer 1: Far Background (Parallax 0.35)
        far_cam_x = int(cam_x * 0.35 + (960 * 0.65))
        far_cam_y = int(cam_y * 0.35 + (540 * 0.65))
        far_cx = max(0, min(1920 - crop_w, far_cam_x - crop_w // 2))
        far_cy = max(0, min(1080 - crop_h, far_cam_y - crop_h // 2))
        far_crop = self.bg_far.crop((far_cx, far_cy, far_cx + crop_w, far_cy + crop_h))
        far_scaled = far_crop.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)
        frame.alpha_composite(far_scaled, (0, 0))

        # Layer 2: Midground (Parallax 1.0)
        mid_cx = max(0, min(1920 - crop_w, cam_x - crop_w // 2))
        mid_cy = max(0, min(1080 - crop_h, cam_y - crop_h // 2))
        mid_crop = self.bg_mid.crop((mid_cx, mid_cy, mid_cx + crop_w, mid_cy + crop_h))
        mid_scaled = mid_crop.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)
        frame.alpha_composite(mid_scaled, (0, 0))

        # Layer 3: Character & Prop Action Plane (Parallax 1.0)
        if show_train:
            im_train = self.rig.render_toy_train(wheel_rot_deg=t_wheel_rot, scale=t_scale, flip_h=t_flip)
            tx_scr = int((t_world_x - mid_cx) * zoom)
            ty_scr = int((t_world_y - mid_cy) * zoom)
            frame.alpha_composite(im_train, (tx_scr, ty_scr))

        for px, py, psz, palpha in steam_puffs:
            sx_scr = int((px - mid_cx) * zoom)
            sy_scr = int((py - mid_cy) * zoom)
            sc_sz = int(psz * zoom)
            if sc_sz > 4 and 0 <= sx_scr < WIDTH and 0 <= sy_scr < HEIGHT:
                sp_img = self.spr_steam.resize((sc_sz, sc_sz), Image.Resampling.BILINEAR)
                if palpha < 0.98:
                    arr_sp = np.array(sp_img)
                    arr_sp[:, :, 3] = (arr_sp[:, :, 3] * palpha).astype(np.uint8)
                    sp_img = Image.fromarray(arr_sp, "RGBA")
                frame.alpha_composite(sp_img, (sx_scr, sy_scr))

        for sp_x, sp_y, sp_sz, sp_rot_deg in sparkles:
            spx_scr = int((sp_x - mid_cx) * zoom)
            spy_scr = int((sp_y - mid_cy) * zoom)
            cur_sz = int(sp_sz * zoom)
            if cur_sz > 4 and 0 <= spx_scr < WIDTH and 0 <= spy_scr < HEIGHT:
                sp_rot = self.spr_sparkle.rotate(sp_rot_deg, resample=Image.Resampling.BILINEAR)
                sp_img = sp_rot.resize((cur_sz, cur_sz), Image.Resampling.BILINEAR)
                frame.alpha_composite(sp_img, (spx_scr - cur_sz // 2, spy_scr - cur_sz // 2))

        im_mimi = self.rig.render_mimi(
            t,
            acting_state="acting",
            is_speaking=is_speech,
            eye_state=m_eye,
            mouth_state=m_mouth,
            squash_stretch=m_squash,
            tilt_deg=m_tilt,
            flip_h=m_flip,
        )
        mw = int(im_mimi.width * m_scale * zoom)
        mh = int(im_mimi.height * m_scale * zoom)
        im_mimi_sc = im_mimi.resize((mw, mh), Image.Resampling.BILINEAR)
        mx_scr = int((m_world_x - mid_cx) * zoom)
        my_scr = int((m_world_y - mid_cy) * zoom)
        frame.alpha_composite(im_mimi_sc, (mx_scr, my_scr))

        # Layer 4: Foreground Framing Layer (Parallax 1.35)
        fg_cam_x = int(cam_x * 1.35 - (960 * 0.35))
        fg_cam_y = int(cam_y * 1.35 - (540 * 0.35))
        fg_cx = max(0, min(1920 - crop_w, fg_cam_x - crop_w // 2))
        fg_cy = max(0, min(1080 - crop_h, fg_cam_y - crop_h // 2))
        fg_crop = self.bg_fg.crop((fg_cx, fg_cy, fg_cx + crop_w, fg_cy + crop_h))
        fg_scaled = fg_crop.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)
        frame.alpha_composite(fg_scaled, (0, 0))

        return frame.convert("RGB")

    def render_animation_video(self, timing_metadata, audio_path, srt_path, output_video_path):
        """Pipes raw RGB24 video frames into FFmpeg with stderr redirected to log."""
        total_duration = timing_metadata[-1]["end_time"] + 0.4
        total_frames = int(total_duration * FPS)

        print(f"🎬 [V3] Rendering {total_frames} frames ({total_duration:.2f}s) at {FPS} FPS...", flush=True)

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

        ffmpeg_log = os.path.join(OUTPUT_DIR, "ffmpeg_render_v3.log")
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
                    print(f"  Frame {i}/{total_frames} ({pct:.1f}%) | Speed: {cur_fps:.1f} fps", flush=True)

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
        print(f"✅ Cartoon Video V3 successfully rendered: {output_video_path}", flush=True)
        print(f"   Size: {file_size:,} bytes | Elapsed: {elapsed:.2f}s ({total_frames / elapsed:.1f} fps)", flush=True)
        return output_video_path


def test_frame():
    print("Testing SceneRendererV3 frame generation...", flush=True)
    timing_file = os.path.join(AUDIO_V3_DIR, "timing_metadata.json")
    with open(timing_file, "r", encoding="utf-8") as f:
        timing_meta = json.load(f)

    renderer = SceneRendererV3()
    test_times = [2.0, 9.0, 16.0, 22.0, 30.0, 36.0]
    for s_idx, t in enumerate(test_times, 1):
        f = renderer.render_frame(t, timing_meta)
        out_p = os.path.join(OUTPUT_DIR, f"preview_v3_scene{s_idx}.jpg")
        f.save(out_p, quality=90)
        print(f"  Scene {s_idx} preview frame saved: {out_p}", flush=True)

    print("✅ All 6 scene preview frames rendered successfully!", flush=True)


if __name__ == "__main__":
    test_frame()
