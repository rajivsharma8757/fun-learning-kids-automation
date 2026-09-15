"""
scene_renderer_v2.py
--------------------
Master Scene Renderer for Cartoon Version 2: Professional Kids Animation.
Implements:
1. 6 Distinct Illustrated Scenes with Multi-Layer Parallax Scrolling (Sky, Midground, Foreground).
2. Fully Articulated Kinematics via CharacterRigV2 (walking, hopping, reaching, grasping, giving, receiving, chewing, dancing, waving).
3. Real Object Interactions (apple pickup from ground, splitting into halves, hand-to-hand pass, rhythmic bites).
4. Dynamic Environmental Particles (fluttering butterfly, drifting dandelion motes, leaves, sunbeams, golden sparkle bursts, musical notes).
5. Speech-Cadence Lip-Sync & Emotional Facial Nuance.
6. Cinematic Eased Camera System (wide, push-in, tracking pan, medium two-shot, pull-out).
7. High-Speed Deadlock-Free Rawvideo FFmpeg Pipe.
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
from cartoon.character_rig_v2 import CharacterRigV2

BG_W = 1920
BG_H = 1080


class SceneRendererV2:
    def __init__(self):
        self.rig = CharacterRigV2()
        self._load_scenic_assets()

    def _load_scenic_assets(self):
        # 1. Parallax Background Layers (6 Scenes x 3 Layers)
        self.bgs = {}
        for s in range(1, 7):
            sky_img = Image.open(os.path.join(BACKGROUNDS_DIR, f"scene{s}_sky.png")).convert("RGBA")
            mid_img = Image.open(os.path.join(BACKGROUNDS_DIR, f"scene{s}_mid.png")).convert("RGBA")
            fg_img = Image.open(os.path.join(BACKGROUNDS_DIR, f"scene{s}_fg.png")).convert("RGBA")
            self.bgs[s] = {"sky": sky_img, "mid": mid_img, "fg": fg_img}

        # 2. Props & Environmental Sprites
        self.props = {
            "apple_whole": Image.open(os.path.join(PROPS_DIR, "apple_whole.png")).convert("RGBA"),
            "apple_half_chintu": Image.open(os.path.join(PROPS_DIR, "apple_half_chintu.png")).convert("RGBA"),
            "apple_half_golu": Image.open(os.path.join(PROPS_DIR, "apple_half_golu.png")).convert("RGBA"),
            "apple_bitten_chintu": Image.open(os.path.join(PROPS_DIR, "apple_bitten_chintu.png")).convert("RGBA"),
            "apple_bitten_golu": Image.open(os.path.join(PROPS_DIR, "apple_bitten_golu.png")).convert("RGBA"),
            "butterfly_1": Image.open(os.path.join(PROPS_DIR, "butterfly_frame1.png")).convert("RGBA"),
            "butterfly_2": Image.open(os.path.join(PROPS_DIR, "butterfly_frame2.png")).convert("RGBA"),
            "dandelion": Image.open(os.path.join(PROPS_DIR, "dandelion_puff.png")).convert("RGBA"),
            "leaf": Image.open(os.path.join(PROPS_DIR, "leaf_particle.png")).convert("RGBA"),
            "sparkle": Image.open(os.path.join(PROPS_DIR, "sparkle_gold.png")).convert("RGBA"),
            "music_note": Image.open(os.path.join(PROPS_DIR, "music_note.png")).convert("RGBA"),
            "sunbeam": Image.open(os.path.join(PROPS_DIR, "sunbeam.png")).convert("RGBA"),
        }

    def render_frame(self, t, timing_metadata):
        # ---------------------------------------------------------------------
        # 1. Determine Active Scene and Speech State
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

        # Default Camera (World Space)
        cam_x, cam_y, zoom = 240, 240, 1.0

        c_im = None
        g_im = None
        c_world_x, c_world_y = 0, 0
        g_world_x, g_world_y = 0, 0
        ground_apple = None
        butterfly_pos = None

        # ---------------------------------------------------------------------
        # 2. Scene Choreography, Kinematics, and Object Interactions
        # ---------------------------------------------------------------------
        if active_scene == 1:
            # SCENE 1: FOREST MEADOW - Hook
            # Camera: Smooth cinematic push-in
            s_dur = 5.85
            s_prog = min(1.0, max(0.0, t / s_dur))
            zoom = 1.0 + s_prog * 0.14
            cam_x = int(140 + s_prog * 120)
            cam_y = int(220 + s_prog * 35)

            # Chintu hops across meadow with dynamic squash & stretch
            c_world_x = int(80 + s_prog * 520)
            c_world_y = 280
            c_im = self.rig.render_chintu(
                t, action="hop", facing=1, scale=0.88, is_speaking=is_speech, brow_state="happy"
            )

            # Fluttering Butterfly in upper meadow
            bf_x = int(450 + math.sin(t * 2.2) * 140 + s_prog * 200)
            bf_y = int(180 + math.cos(t * 3.5) * 45)
            butterfly_pos = (bf_x, bf_y)

        elif active_scene == 2:
            # SCENE 2: THE GREAT OAK TREE - Discovery of the Apple
            s_start, s_dur = 5.85, 8.25
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))
            zoom = 1.15
            cam_x = 360
            cam_y = 250

            # Apple resting under tree on right
            apple_ground_x, apple_ground_y = 740, 525

            if s_prog < 0.35:
                # Phase 1: Walking toward tree (Alternating leg walk cycle)
                w_prog = s_prog / 0.35
                c_world_x = int(320 + w_prog * 290)
                c_world_y = 275
                c_im = self.rig.render_chintu(
                    t, action="walk", facing=1, scale=0.88, is_speaking=is_speech,
                    brow_state="curious", eye_state="open"
                )
                ground_apple = (apple_ground_x, apple_ground_y)

            elif s_prog < 0.60:
                # Phase 2: Crouch & Reach down to grasp apple
                r_prog = (s_prog - 0.35) / 0.25
                c_world_x = 610
                c_world_y = 275
                c_im = self.rig.render_chintu(
                    t, action="crouch_and_reach", action_progress=r_prog,
                    facing=1, scale=0.88, is_speaking=is_speech,
                    brow_state="happy", eye_state="look_down"
                )
                # Apple on ground until fingers touch and lift
                if r_prog < 0.70:
                    ground_apple = (apple_ground_x, apple_ground_y)
                else:
                    # Attached to hand lifting up
                    pass

            else:
                # Phase 3: Proudly holding apple aloft with joyful smile
                c_world_x = 615
                c_world_y = 270
                c_im = self.rig.render_chintu(
                    t, action="hold_up", held_item="apple_whole",
                    facing=1, scale=0.88, is_speaking=is_speech,
                    brow_state="happy", eye_state="wide", mouth_state="smile"
                )

            # Butterfly flutters near tree canopy
            bf_x = int(820 + math.sin(t * 2.0) * 80)
            bf_y = int(220 + math.cos(t * 3.0) * 35)
            butterfly_pos = (bf_x, bf_y)

        elif active_scene == 3:
            # SCENE 3: THE WOODLAND TRAIL - Conflict / Golu Arrives Hungry
            s_start, s_dur = 14.1, 6.78
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))
            zoom = 1.14
            cam_x = 340
            cam_y = 240

            # Chintu holding apple on left, looking toward arriving friend
            c_world_x, c_world_y = 350, 270
            c_im = self.rig.render_chintu(
                t, action="idle", held_item="apple_whole",
                facing=1, scale=0.86, is_speaking=is_speech,
                brow_state="curious", eye_state="look_right"
            )

            # Golu Bear walks in down the trail holding his rumbling tummy
            g_world_x = int(1040 - s_prog * 270)
            g_world_y = 265
            g_im = self.rig.render_golu(
                t, action="walk_sad", facing=-1, scale=0.90, is_speaking=False,
                brow_state="sad", eye_state="sad", mouth_state="sad"
            )

        elif active_scene == 4:
            # SCENE 4: SUNLIT CLEARING - The WOW Moment / Sharing the Apple
            s_start, s_dur = 20.88, 7.09
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))
            zoom = 1.25  # Close-up emotional emphasis
            cam_x = 360
            cam_y = 235

            g_world_x, g_world_y = 740, 260

            if s_prog < 0.28:
                # Phase 1: Chintu steps forward to offer
                step_p = s_prog / 0.28
                c_world_x = int(360 + step_p * 80)
                c_world_y = 265
                c_im = self.rig.render_chintu(
                    t, action="give", action_progress=step_p,
                    held_item="apple_half_chintu", facing=1, scale=0.90, is_speaking=is_speech,
                    brow_state="happy", eye_state="happy", mouth_state="smile"
                )
                g_im = self.rig.render_golu(
                    t, action="idle", facing=-1, scale=0.92, is_speaking=False,
                    brow_state="sad", eye_state="sad", mouth_state="sad"
                )

            elif s_prog < 0.65:
                # Phase 2: SNAP & SHARE - Golden Sparkles & Surprise
                share_p = (s_prog - 0.28) / 0.37
                c_world_x = 440
                c_world_y = 265
                c_im = self.rig.render_chintu(
                    t, action="give", action_progress=1.0,
                    held_item="apple_half_chintu", facing=1, scale=0.90, is_speaking=is_speech,
                    brow_state="happy", eye_state="happy", mouth_state="smile"
                )
                g_im = self.rig.render_golu(
                    t, action="receive", action_progress=share_p,
                    held_item="apple_half_golu" if share_p > 0.40 else None,
                    facing=-1, scale=0.92, is_speaking=False
                )

            else:
                # Phase 3: Both holding their halves, overjoyed
                c_world_x = 440
                c_world_y = 265
                c_im = self.rig.render_chintu(
                    t, action="idle", held_item="apple_half_chintu",
                    facing=1, scale=0.90, is_speaking=is_speech,
                    brow_state="happy", eye_state="happy", mouth_state="smile"
                )
                g_im = self.rig.render_golu(
                    t, action="idle", held_item="apple_half_golu",
                    facing=-1, scale=0.92, is_speaking=False,
                    brow_state="happy", eye_state="happy", mouth_state="smile"
                )

        elif active_scene == 5:
            # SCENE 5: PLAYFUL PICNIC GLADE - Celebration & Munching
            s_start, s_dur = 27.97, 4.33
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))
            zoom = 1.18
            cam_x = 340
            cam_y = 230

            c_world_x, c_world_y = 430, 260
            g_world_x, g_world_y = 750, 255

            if s_prog < 0.60:
                # Munching and taking delicious crunchy bites
                c_im = self.rig.render_chintu(
                    t, action="munch", held_item="apple_bitten_chintu",
                    facing=1, scale=0.88, is_speaking=is_speech, brow_state="happy"
                )
                g_im = self.rig.render_golu(
                    t, action="munch", held_item="apple_bitten_golu",
                    facing=-1, scale=0.90, is_speaking=False, brow_state="happy"
                )
            else:
                # Dancing with joyful bounce
                c_im = self.rig.render_chintu(
                    t, action="hop", held_item="apple_bitten_chintu",
                    facing=1, scale=0.88, is_speaking=is_speech, brow_state="happy"
                )
                g_im = self.rig.render_golu(
                    t, action="dance", held_item="apple_bitten_golu",
                    facing=-1, scale=0.90, is_speaking=False, brow_state="happy"
                )

        else:
            # SCENE 6: GOLDEN SUNSET OUTLOOK - Moral Lesson & Outro Wave
            s_start, s_dur = 32.3, 6.64
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))
            # Smooth cinematic pull-out camera
            zoom = max(1.02, 1.20 - s_prog * 0.16)
            cam_x = int(340 - s_prog * 100)
            cam_y = int(230 - s_prog * 25)

            c_world_x, c_world_y = 490, 275
            g_world_x, g_world_y = 730, 270

            c_im = self.rig.render_chintu(
                t, action="wave", facing=1, scale=0.86, is_speaking=is_speech,
                brow_state="happy", eye_state="happy", mouth_state="smile"
            )
            g_im = self.rig.render_golu(
                t, action="wave", facing=-1, scale=0.88, is_speaking=False,
                brow_state="happy", eye_state="happy", mouth_state="smile"
            )

        # ---------------------------------------------------------------------
        # 3. MULTI-LAYER PARALLAX COMPOSITING
        # ---------------------------------------------------------------------
        cur_bg = self.bgs[active_scene]
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

        # Viewport dimensions
        crop_w = int(WIDTH / zoom)
        crop_h = int(HEIGHT / zoom)

        # Layer 1: Sky (Distant - Parallax Factor 0.20)
        sky_cam_x = int(cam_x * 0.20)
        sky_cam_y = int(cam_y * 0.20)
        sky_cx = max(0, min(BG_W - crop_w, sky_cam_x))
        sky_cy = max(0, min(BG_H - crop_h, sky_cam_y))
        sky_cropped = cur_bg["sky"].crop((sky_cx, sky_cy, sky_cx + crop_w, sky_cy + crop_h))
        sky_scaled = sky_cropped.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        frame.alpha_composite(sky_scaled, (0, 0))

        # Sunbeam Overlay in Scene 4
        if active_scene == 4:
            sb = self.props["sunbeam"]
            sb_pulse = int(45 + math.sin(t * 3.0) * 15)
            frame.alpha_composite(sb, (180, 0))

        # Layer 2: Midground (Hills, Trees, Path - Parallax Factor 0.65)
        mid_cam_x = int(cam_x * 0.65)
        mid_cam_y = int(cam_y * 0.65)
        mid_cx = max(0, min(BG_W - crop_w, mid_cam_x))
        mid_cy = max(0, min(BG_H - crop_h, mid_cam_y))
        mid_cropped = cur_bg["mid"].crop((mid_cx, mid_cy, mid_cx + crop_w, mid_cy + crop_h))
        mid_scaled = mid_cropped.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        frame.alpha_composite(mid_scaled, (0, 0))

        # Ground Apple (Scene 2 before pickup)
        if ground_apple:
            gax, gay = ground_apple
            ga_scr_x = int((gax - cam_x) * zoom)
            ga_scr_y = int((gay - cam_y) * zoom)
            ap_sc = self.props["apple_whole"].resize((int(125 * zoom), int(125 * zoom)), Image.Resampling.LANCZOS)
            frame.alpha_composite(ap_sc, (ga_scr_x, ga_scr_y))

        # Layer 3: Character Action Plane (Parallax Factor 1.0)
        if c_im:
            cx_scr = int((c_world_x - cam_x) * zoom)
            cy_scr = int((c_world_y - cam_y) * zoom)
            frame.alpha_composite(c_im, (cx_scr, cy_scr))

        if g_im:
            gx_scr = int((g_world_x - cam_x) * zoom)
            gy_scr = int((g_world_y - cam_y) * zoom)
            frame.alpha_composite(g_im, (gx_scr, gy_scr))

        # Layer 4: Foreground (Grass, Leaves, Framing - Parallax Factor 1.35)
        fg_cam_x = int(cam_x * 1.35)
        fg_cam_y = int(cam_y * 1.35)
        fg_cx = max(0, min(BG_W - crop_w, fg_cam_x))
        fg_cy = max(0, min(BG_H - crop_h, fg_cam_y))
        fg_cropped = cur_bg["fg"].crop((fg_cx, fg_cy, fg_cx + crop_w, fg_cy + crop_h))
        fg_scaled = fg_cropped.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        frame.alpha_composite(fg_scaled, (0, 0))

        # ---------------------------------------------------------------------
        # 4. ENVIRONMENTAL PARTICLES & ATMOSPHERIC EFFECTS
        # ---------------------------------------------------------------------
        # A. Fluttering Butterfly (Scenes 1 & 2)
        if butterfly_pos:
            bfx, bfy = butterfly_pos
            bf_scr_x = int((bfx - cam_x) * zoom)
            bf_scr_y = int((bfy - cam_y) * zoom)
            bf_frame = self.props["butterfly_1"] if int(t * 8.0) % 2 == 0 else self.props["butterfly_2"]
            bf_scaled = bf_frame.resize((int(70 * zoom), int(70 * zoom)), Image.Resampling.LANCZOS)
            frame.alpha_composite(bf_scaled, (bf_scr_x, bf_scr_y))

        # B. Dandelion Puff Particles drifting in wind (Scenes 1, 3, 4)
        if active_scene in [1, 3, 4]:
            dp = self.props["dandelion"]
            for d_i, (init_x, init_y, speed) in enumerate([(120, 240, 45), (480, 180, 55), (850, 280, 40), (1200, 200, 50)]):
                cur_x = int((init_x + t * speed) % WIDTH)
                cur_y = int(init_y + math.sin(t * 2.0 + d_i) * 30)
                frame.alpha_composite(dp, (cur_x, cur_y))

        # C. Golden Starburst Sparkles on Apple Sharing (Scene 4)
        if active_scene == 4:
            s_prog = (t - 20.88) / 7.09
            if 0.28 <= s_prog <= 0.85:
                sp = self.props["sparkle"]
                sparkle_cx = int((590 - cam_x) * zoom)
                sparkle_cy = int((380 - cam_y) * zoom)
                for s_i, (ox, oy, sz, spd) in enumerate([(0, 0, 95, 8.0), (-55, -35, 65, -6.0), (60, -25, 75, 7.0), (-30, 45, 55, 9.0), (45, 40, 60, -8.0)]):
                    pulse = 0.8 + 0.3 * math.sin(t * spd + s_i)
                    cur_sz = int(sz * pulse)
                    sp_rot = sp.rotate(t * spd * 15.0, resample=Image.Resampling.BICUBIC)
                    sp_sc = sp_rot.resize((cur_sz, cur_sz), Image.Resampling.LANCZOS)
                    frame.alpha_composite(sp_sc, (sparkle_cx + ox - cur_sz // 2, sparkle_cy + oy - cur_sz // 2))

        # D. Floating Musical Notes in Celebration (Scene 5)
        if active_scene == 5:
            mn = self.props["music_note"]
            for n_i, (base_x, spd, y_phase) in enumerate([(480, 60, 0), (640, 50, 70), (820, 65, 30), (560, 55, 110)]):
                ny = int(520 - ((t * spd + y_phase) % 320))
                nx = int(base_x + math.sin(t * 3.0 + n_i) * 28)
                frame.alpha_composite(mn, (nx, ny))

        return frame.convert("RGB")

    def render_animation_video(self, timing_metadata, audio_path, srt_path, output_video_path):
        """Pipes all raw RGB24 frames into FFmpeg for high-speed H.264/AAC encoding."""
        total_duration = timing_metadata[-1]["end_time"] + 0.5
        total_frames = int(total_duration * FPS)

        print(f"🎬 [V2] Rendering {total_frames} frames ({total_duration:.2f}s) at {FPS} FPS...", flush=True)

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

        ffmpeg_log = os.path.join(OUTPUT_DIR, "ffmpeg_render_v2.log")
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
        print(f"✅ Cartoon Video V2 successfully rendered: {output_video_path}", flush=True)
        print(f"   Size: {file_size:,} bytes | Elapsed: {elapsed:.2f}s ({total_frames / elapsed:.1f} fps)", flush=True)
        return output_video_path


if __name__ == "__main__":
    timing_file = os.path.join(AUDIO_DIR, "timing_metadata.json")
    with open(timing_file, "r", encoding="utf-8") as f:
        timing_meta = json.load(f)

    audio_file = os.path.join(AUDIO_DIR, "final_master_audio_v2.wav")
    srt_file = os.path.join(OUTPUT_DIR, "demo_subtitles.srt")
    out_file = os.path.join(OUTPUT_DIR, "demo_v2_chintu_shares.mp4")

    renderer = SceneRendererV2()
    renderer.render_animation_video(timing_meta, audio_file, srt_file, out_file)
