#!/usr/bin/env python3
"""
快速转录脚本：使用 Apple Silicon GPU (MLX) 加速
- M3 Max 上速度比 CPU 快 5-10 倍
- 16 分钟视频约 1-2 分钟出结果
- 不区分说话人（只追求速度）

用法：python transcribe_fast.py <音频文件> [--lang zh] [--model large-v3]
"""
import sys
import os
import argparse
import warnings
warnings.filterwarnings("ignore")

import time
from datetime import datetime
from pathlib import Path

# MLX-whisper 模型在 HuggingFace 的命名映射
MODEL_MAP = {
    "tiny":     "mlx-community/whisper-tiny-mlx",
    "base":     "mlx-community/whisper-base-mlx",
    "small":    "mlx-community/whisper-small-mlx",
    "medium":   "mlx-community/whisper-medium-mlx",
    "large-v2": "mlx-community/whisper-large-v2-mlx",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
}

def fmt_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

def fmt_srt(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    parser = argparse.ArgumentParser(description="快速转录（GPU 加速）")
    parser.add_argument("audio", help="音频/视频文件路径")
    parser.add_argument("--lang", default=None, help="语言：zh / en / 留空自动检测")
    parser.add_argument("--model", default="large-v3-turbo",
                        choices=list(MODEL_MAP.keys()),
                        help="默认 large-v3-turbo（精度接近 large-v3，速度快 8 倍）")
    parser.add_argument("--output-dir", default=str(Path.home() / "meeting-ai/output"))
    args = parser.parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        print(f"错误：文件不存在：{audio_path}", file=sys.stderr); sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"⚡ MLX 加速模式 (Apple Silicon GPU)", flush=True)
    print(f"   模型：{args.model}", flush=True)
    print(f"   语言：{args.lang or '自动检测'}", flush=True)
    print(f"")
    print(f"[1/2] 加载模型（首次会自动下载）...", flush=True)

    import mlx_whisper

    print(f"[2/2] 转录中：{audio_path.name} ...", flush=True)
    t0 = time.time()

    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=MODEL_MAP[args.model],
        language=args.lang,
        word_timestamps=False,
        verbose=False,
    )

    elapsed = time.time() - t0
    detected_lang = result.get("language", args.lang or "zh")
    segments = result.get("segments", [])
    print(f"   ✓ 完成！检测语言：{detected_lang}，{len(segments)} 个片段，耗时 {elapsed:.1f} 秒", flush=True)

    # 每场会议一个文件夹（与音频同名 + 时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = audio_path.stem
    meeting_dir = output_dir / f"{stem}_{timestamp}"
    meeting_dir.mkdir(parents=True, exist_ok=True)
    out_txt = meeting_dir / "1-逐字稿.txt"
    out_srt = meeting_dir / "1-字幕.srt"

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(f"# 逐字稿 — {audio_path.name}\n")
        f.write(f"# 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (MLX 加速)\n\n")
        for seg in segments:
            text = seg["text"].strip()
            ts = fmt_time(seg["start"])
            f.write(f"[{ts}] {text}\n")

    with open(out_srt, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n{fmt_srt(seg['start'])} --> {fmt_srt(seg['end'])}\n{seg['text'].strip()}\n\n")

    # 计算实时倍速
    audio_duration = segments[-1]["end"] if segments else 0
    speed_ratio = audio_duration / elapsed if elapsed > 0 else 0
    print(f"")
    print(f"📊 处理速度：{speed_ratio:.1f}x 实时（音频 {audio_duration:.0f}s / 处理 {elapsed:.1f}s）")
    print(f"")
    print(f"✓ 转录完成！")
    print(f"  逐字稿：{out_txt}")
    print(f"  字幕：  {out_srt}")

if __name__ == "__main__":
    main()
