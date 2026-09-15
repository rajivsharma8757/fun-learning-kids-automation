"""
voice_engine_v3.py
------------------
Synthesizes high-clarity, continuous Hindi Edge-TTS narration for
"Mimi's Magic Toy Train" (मीमी और जादुई रेलगाड़ी).
Includes exponential backoff retries, audio decoding, exact timing extraction,
and master voice track assembly (normalized to -1.0 dBFS with zero clipping).
"""

import os
import sys
import json
import time
import subprocess
import numpy as np
import scipy.io.wavfile as wavfile

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import CARTOON_DIR, VOICE_NARRATOR

AUDIO_V3_DIR = os.path.join(CARTOON_DIR, "assets_v3", "audio")

SCENE_SCRIPTS_V3 = [
    {
        "scene_id": 1,
        "speaker": "narrator",
        "text_hi": "मीमी अपने प्यारे कमरे में खेल रही थी, तभी उसे एक सुंदर छोटी रेलगाड़ी दिखी!",
        "text_en": "Mimi was playing in her lovely room, when she spotted a cute little toy train!"
    },
    {
        "scene_id": 2,
        "speaker": "narrator",
        "text_hi": "मीमी ने झुककर रेलगाड़ी को उठाया। वाह! कितने प्यारे पहिए और घंटी!",
        "text_en": "Mimi gently picked up the train. Wow! Such cute wheels and a little bell!"
    },
    {
        "scene_id": 3,
        "speaker": "narrator",
        "text_hi": "उसने रेलगाड़ी को लकड़ी की पटरी पर रखा। अब शुरू होगा असली मज़ा!",
        "text_en": "She placed the train on the wooden track. Now the real fun begins!"
    },
    {
        "scene_id": 4,
        "speaker": "narrator",
        "text_hi": "छुक-छुक, चूं-चूं! रेलगाड़ी दौड़ने लगी! मीमी खुशी से तालियाँ बजाने लगी!",
        "text_en": "Chug-chug, choo-choo! The train started rolling! Mimi clapped with delight!"
    },
    {
        "scene_id": 5,
        "speaker": "narrator",
        "text_hi": "रेलगाड़ी पुल से गुजरी और मीमी हँसते हुए उसके पीछे चलने लगी!",
        "text_en": "The train crossed the bridge and Mimi happily followed behind it!"
    },
    {
        "scene_id": 6,
        "speaker": "narrator",
        "text_hi": "सावधानी से खेलने से खिलौने खुश रहते हैं! फन लर्निंग किड्स के साथ सीखते रहिए!",
        "text_en": "Playing with care keeps toys happy! Keep learning with Fun Learning Kids!"
    }
]


def synthesize_segment(text, out_mp3, voice=VOICE_NARRATOR, max_retries=6):
    """Synthesizes text via edge-tts with cheerful +15% rate and retries."""
    for attempt in range(1, max_retries + 1):
        try:
            cmd = [
                sys.executable, "-m", "edge_tts",
                "--voice", voice,
                "--rate=+15%",
                "--text", text,
                "--write-media", out_mp3
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)
            if res.returncode == 0 and os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 1000:
                return True
        except Exception as e:
            pass
        time.sleep(1.5 * attempt)
    raise RuntimeError(f"Failed to synthesize TTS segment after {max_retries} attempts.")


def mp3_to_wav(mp3_path, wav_path):
    """Converts MP3 to 48kHz stereo WAV via FFmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", mp3_path,
        "-ar", "48000", "-ac", "2",
        wav_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def build_voice_master_v3():
    print("🎙️ Synthesizing Hindi Edge-TTS Narration for Version 3...", flush=True)
    os.makedirs(AUDIO_V3_DIR, exist_ok=True)

    timing_metadata = []
    current_time = 0.0
    sr = 48000
    all_audio_arrays = []

    for item in SCENE_SCRIPTS_V3:
        sid = item["scene_id"]
        mp3_f = os.path.join(AUDIO_V3_DIR, f"seg_{sid}.mp3")
        wav_f = os.path.join(AUDIO_V3_DIR, f"seg_{sid}.wav")

        print(f"  Synthesizing Scene {sid}: {item['text_hi'][:30]}...", flush=True)
        synthesize_segment(item["text_hi"], mp3_f)
        mp3_to_wav(mp3_f, wav_f)

        rate, data = wavfile.read(wav_f)
        data_f = data.astype(np.float32) / 32768.0
        seg_dur = len(data_f) / float(rate)

        start_t = current_time
        end_t = round(start_t + seg_dur, 3)

        timing_metadata.append({
            "scene_id": sid,
            "speaker": item["speaker"],
            "text_hi": item["text_hi"],
            "text_en": item["text_en"],
            "start_time": round(start_t, 3),
            "end_time": end_t,
            "duration": round(seg_dur, 3)
        })

        all_audio_arrays.append(data_f)

        # 0.25s breathing pause between scenes
        pause_samples = int(0.25 * sr)
        pause_data = np.zeros((pause_samples, 2), dtype=np.float32)
        all_audio_arrays.append(pause_data)
        current_time = end_t + 0.25

    # Assemble master narration track
    master_voice = np.concatenate(all_audio_arrays, axis=0)

    # Normalize to -1.0 dBFS Peak (0.891)
    peak = np.max(np.abs(master_voice))
    target_peak = 0.891
    if peak > 0:
        master_voice = master_voice * (target_peak / peak)

    master_wav_path = os.path.join(AUDIO_V3_DIR, "narration_master.wav")
    out_16 = np.clip(master_voice * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(master_wav_path, sr, out_16)

    timing_json_path = os.path.join(AUDIO_V3_DIR, "timing_metadata.json")
    with open(timing_json_path, "w", encoding="utf-8") as f:
        json.dump(timing_metadata, f, ensure_ascii=False, indent=2)

    total_dur = len(master_voice) / float(sr)
    final_peak = np.max(np.abs(master_voice))
    print(f"✅ Master Voice V3 built: {master_wav_path}", flush=True)
    print(f"   Duration: {total_dur:.2f}s | Peak: {final_peak:.3f} | Timing saved to {timing_json_path}", flush=True)
    return timing_metadata, master_wav_path


if __name__ == "__main__":
    build_voice_master_v3()
