#!/usr/bin/env python3
"""客观轨：ffprobe 规格 + 音轨确认 + LUFS 响度 → summary.json"""
import json, subprocess, re
from pathlib import Path

SRC = Path("/Users/admin/Downloads/gpt5.6-sol vs gpt5.5")
OUT = Path(__file__).parent / "summary.json"

results = []
for d in sorted(SRC.iterdir()):
    if not d.is_dir():
        continue
    for v in ("a", "b"):
        f = d / f"{v}.mp4"
        if not f.exists():
            continue
        probe = json.loads(subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(f)],
            capture_output=True, text=True).stdout)
        vstreams = [s for s in probe["streams"] if s["codec_type"] == "video"]
        astreams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
        lufs = None
        if astreams:
            out = subprocess.run(
                ["ffmpeg", "-nostats", "-i", str(f), "-map", "a:0",
                 "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                capture_output=True, text=True).stderr
            m = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", out)
            lufs = float(m.group(1)) if m else None
        vs = vstreams[0]
        w, h = vs["width"], vs["height"]
        results.append({
            "topic": d.name, "video": v, "path": str(f),
            "playable": True,
            "duration_sec": round(float(probe["format"]["duration"]), 2),
            "resolution": f"{w}x{h}",
            "aspect_ratio": round(w / h, 4),
            "fps": eval(vs.get("avg_frame_rate", "0/1")) if vs.get("avg_frame_rate") != "0/0" else None,
            "video_codec": vs["codec_name"],
            "bitrate_kbps": round(int(probe["format"]["bit_rate"]) / 1000),
            "size_mb": round(int(probe["format"]["size"]) / 1e6, 1),
            "has_audio_track": bool(astreams),
            "audio_codec": astreams[0]["codec_name"] if astreams else None,
            "integrated_lufs": lufs,
        })
        print(d.name, v, "ok")

OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(f"wrote {OUT} ({len(results)} videos)")
