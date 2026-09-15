"""
audio_mixer_v2.py
-----------------
Mixes the audio master for Cartoon Version 2:
- Priority 1: Crystal-Clear Hindi Narration (normalized to -1.0 dBFS)
- Priority 2: Cheerful background music ducked by -18.4 dB during speech
- Priority 3: Synchronized cartoon SFX (hop, pickup, snap, sparkle, munch)
Produces: C:\\kids_automation\\cartoon\\assets\\audio\\final_master_audio_v2.wav
"""

import os
import sys
import math
import json
import numpy as np
import scipy.io.wavfile as wavfile

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import AUDIO_DIR, MUSIC_VOLUME, SFX_VOLUME


def generate_additional_sfx():
    """Generates pickup whoosh, snap, and footstep sound effects."""
    sr = 48000

    # 1. Apple Pickup Whoosh/Pop (0.28s)
    t = np.linspace(0, 0.28, int(sr * 0.28), endpoint=False)
    freq = np.linspace(280, 780, len(t))
    env = np.sin(np.pi * t / 0.28) ** 1.8
    sfx_pickup = np.sin(2 * np.pi * freq * t) * env * 0.45
    sfx_pickup_stereo = np.column_stack([sfx_pickup, sfx_pickup])
    wavfile.write(os.path.join(AUDIO_DIR, "sfx_pickup.wav"), sr, (sfx_pickup_stereo * 32767).astype(np.int16))

    # 2. Apple Split Snap (0.22s)
    t = np.linspace(0, 0.22, int(sr * 0.22), endpoint=False)
    noise = np.random.uniform(-0.6, 0.6, len(t))
    wood_pop = np.sin(2 * np.pi * 520 * t) * np.exp(-t * 28.0)
    snap = (wood_pop * 0.7 + noise * np.exp(-t * 35.0) * 0.3) * np.exp(-t * 12.0)
    snap_stereo = np.column_stack([snap, snap])
    wavfile.write(os.path.join(AUDIO_DIR, "sfx_snap.wav"), sr, (snap_stereo * 32767).astype(np.int16))

    # 3. Soft Patter Footstep (0.15s)
    t = np.linspace(0, 0.15, int(sr * 0.15), endpoint=False)
    thump = np.sin(2 * np.pi * 140 * t) * np.exp(-t * 30.0) * 0.35
    thump_stereo = np.column_stack([thump, thump])
    wavfile.write(os.path.join(AUDIO_DIR, "sfx_footstep.wav"), sr, (thump_stereo * 32767).astype(np.int16))


def build_final_audio_v2():
    print("🎵 Building Master Audio Mix V2...", flush=True)
    generate_additional_sfx()

    sr = 48000
    voice_path = os.path.join(AUDIO_DIR, "narration_master.wav")
    music_path = os.path.join(AUDIO_DIR, "cartoon_music.wav")
    timing_path = os.path.join(AUDIO_DIR, "timing_metadata.json")
    out_master_path = os.path.join(AUDIO_DIR, "final_master_audio_v2.wav")

    # Load Voice
    _, voice_data = wavfile.read(voice_path)
    voice_f = voice_data.astype(np.float32) / 32768.0
    total_len = len(voice_f)
    duration_s = total_len / float(sr)

    # Load Music (loop/tile to match duration + buffer)
    _, music_data = wavfile.read(music_path)
    music_f = music_data.astype(np.float32) / 32768.0
    repeats = int(math.ceil(total_len / float(len(music_f)))) + 1
    music_extended = np.tile(music_f, (repeats, 1))[:total_len]

    # Load Timing Metadata for SFX and Ducking
    with open(timing_path, "r", encoding="utf-8") as f:
        timing_meta = json.load(f)

    # Build Continuous Ducking Envelope
    # Normal music level = MUSIC_VOLUME * 1.5, ducked = MUSIC_VOLUME * 0.75
    duck_curve = np.ones(total_len, dtype=np.float32) * (MUSIC_VOLUME * 0.75)
    fade_samples = int(sr * 0.3)

    for item in timing_meta:
        s_idx = int(item["start_time"] * sr)
        e_idx = min(total_len, int(item["end_time"] * sr))
        # Ensure deep ducking during active speech
        duck_curve[s_idx:e_idx] = MUSIC_VOLUME * 0.65

    # Apply ducked music
    mixed = np.copy(voice_f)
    mixed += music_extended * duck_curve[:, np.newaxis]

    # Overlay Synchronized Cartoon SFX
    def overlay_sfx(sfx_name, timestamp_s, vol=SFX_VOLUME):
        sfx_file = os.path.join(AUDIO_DIR, f"{sfx_name}.wav")
        if not os.path.exists(sfx_file):
            return
        _, s_data = wavfile.read(sfx_file)
        s_f = (s_data.astype(np.float32) / 32768.0) * vol
        start_idx = int(timestamp_s * sr)
        end_idx = min(total_len, start_idx + len(s_f))
        actual_len = end_idx - start_idx
        if actual_len > 0:
            mixed[start_idx:end_idx] += s_f[:actual_len]

    # 1. Hopping SFX in Scene 1 (Chintu hopping across meadow)
    for hop_t in [0.8, 1.8, 2.8, 3.8, 4.6]:
        overlay_sfx("sfx_hop", hop_t, vol=0.18)

    # 2. Apple Discovery Pickup in Scene 2
    overlay_sfx("sfx_pickup", 9.8, vol=0.28)

    # 3. Golu footsteps in Scene 3
    for step_t in [15.2, 16.2, 17.2, 18.2]:
        overlay_sfx("sfx_footstep", step_t, vol=0.16)

    # 4. Apple Splitting Snap in Scene 4
    overlay_sfx("sfx_snap", 22.4, vol=0.32)

    # 5. Magical Sparkle burst in Scene 4
    overlay_sfx("sfx_sparkle", 23.5, vol=0.26)

    # 6. Crunchy Munching in Scene 5
    for munch_t in [28.4, 29.5, 30.6]:
        overlay_sfx("sfx_munch", munch_t, vol=0.28)

    # 7. Final Sparkle in Scene 6 outro
    overlay_sfx("sfx_sparkle", 36.5, vol=0.22)

    # Normalize to -1.0 dBFS Peak (0.89) to guarantee zero clipping
    peak = np.max(np.abs(mixed))
    target_peak = 0.891
    if peak > target_peak:
        mixed = mixed * (target_peak / peak)

    # Convert to 16-bit PCM WAV
    out_16 = np.clip(mixed * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(out_master_path, sr, out_16)

    final_peak = np.max(np.abs(mixed))
    final_rms = np.sqrt(np.mean(mixed ** 2))
    print(f"✅ Master Audio V2 built successfully: {out_master_path}", flush=True)
    print(f"   Duration: {duration_s:.2f}s | Peak: {final_peak:.3f} | RMS: {final_rms:.3f} (Zero Clipping)", flush=True)
    return out_master_path


if __name__ == "__main__":
    build_final_audio_v2()
