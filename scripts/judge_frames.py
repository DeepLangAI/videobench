#!/usr/bin/env python3
"""抽帧评估：把一个目录下的帧图按时间顺序发给多模态模型（默认 claude-sonnet-5）。
网关配置沿用 video-triage 的 config.json。仅标准库。

用法: python3 judge_frames.py --frames <dir> --prompt-file <path> [--model claude-sonnet-5] [--fps 2]
"""
import argparse, base64, json, sys, urllib.request
from pathlib import Path

CONFIG = json.loads((Path.home() / ".claude/skills/video-triage/scripts/config.json").read_text())

ap = argparse.ArgumentParser()
ap.add_argument("--frames", required=True)
ap.add_argument("--prompt-file", required=True)
ap.add_argument("--model", default="claude-sonnet-5")
ap.add_argument("--fps", default="2")
a = ap.parse_args()

frames = sorted(Path(a.frames).glob("*.jpg"))
if not frames:
    sys.exit(f"no frames in {a.frames}")
prompt = Path(a.prompt_file).read_text()

content = [{"type": "text", "text":
    f"以下是同一条视频按 {a.fps} fps 均匀抽取的 {len(frames)} 帧，按时间顺序排列，"
    f"文件名即时间戳（如 f03.50s.jpg = 3.5秒处）。你看不到帧与帧之间的运动过程，"
    f"评动效流畅度时请基于相邻帧的位移/形变推断并适当保守。\n\n" + prompt}]
for f in frames:
    b64 = base64.b64encode(f.read_bytes()).decode()
    content.append({"type": "text", "text": f"[{f.stem[1:]}]"})
    content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

req = urllib.request.Request(
    CONFIG["base_url"].rstrip("/") + "/v1/chat/completions",
    data=json.dumps({"model": a.model, "max_tokens": 4000,
                     "messages": [{"role": "user", "content": content}]}).encode(),
    headers={"Authorization": f"Bearer {CONFIG['api_key']}", "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.load(r)
except urllib.error.HTTPError as e:
    sys.stderr.write(e.read().decode()); sys.exit(1)

print(resp["choices"][0]["message"]["content"])
u = resp.get("usage", {})
sys.stderr.write(f"\n[usage] prompt={u.get('prompt_tokens')} completion={u.get('completion_tokens')}\n")
