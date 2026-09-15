import os
import sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import AUDIO_DIR, MUSIC_VOLUME, SFX_VOLUME

def mix_cartoon_audio(narration_path, output_mixed_path, sfx_events=None):
    if sfx_events is None:
        sfx_events = []

    sr, voice_data = wavfile.read(narration_path)
    voice_samples = voice_data.astype(np.float32) / 32768.0
    total_samples = len(voice_samples)

    music_path = os.path.join(AUDIO_DIR, "cartoon_music.wav")
    if os.path.exists(music_path):
        msr, mdata = wavfile.read(music_path)
        m_samples = mdata.astype(np.float32) / 32768.0
        if len(m_samples) < total_samples:
            repeats = int(np.ceil(total_samples / len(m_samples)))
            m_samples = np.tile(m_samples, (repeats, 1))
        music_layer = m_samples[:total_samples] * MUSIC_VOLUME
    else:
        music_layer = np.zeros_like(voice_samples)

    sfx_layer = np.zeros_like(voice_samples)
    for t_sec, sfx_name in sfx_events:
        sfx_file = os.path.join(AUDIO_DIR, f"{sfx_name}.wav")
        if os.path.exists(sfx_file):
            _, sdata = wavfile.read(sfx_file)
            s_samples = sdata.astype(np.float32) / 32768.0
            start_s = int(t_sec * sr)
            end_s = min(total_samples, start_s + len(s_samples))
            if end_s > start_s:
                sfx_layer[start_s:end_s] += s_samples[:end_s - start_s] * SFX_VOLUME

    mixed = voice_samples + music_layer + sfx_layer

    peak = np.max(np.abs(mixed))
    if peak > 0.96:
        mixed = mixed * (0.95 / peak)

    mixed_int16 = (mixed * 32767.0).clip(-32768, 32767).astype(np.int16)
    wavfile.write(output_mixed_path, sr, mixed_int16)
    return output_mixed_path
