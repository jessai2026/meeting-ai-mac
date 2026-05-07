#!/usr/bin/env python3
"""
转录脚本：将音频/视频文件转录为逐字稿
- 无 HF 令牌：高精度转录，无说话人区分
- 有 HF 令牌：转录 + 区分谁说了什么（Speaker 1、Speaker 2…）
用法：python transcribe.py <音频文件> [--hf-token TOKEN] [--lang zh]
"""
import sys
import os
import argparse
import warnings
warnings.filterwarnings("ignore")  # 屏蔽 torchcodec 等无关警告

from datetime import datetime
from pathlib import Path

def fmt_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

def fmt_srt(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    parser = argparse.ArgumentParser(description="会议音频转录工具")
    parser.add_argument("audio", help="音频或视频文件路径（支持 mp4/m4a/wav/mp3/mov）")
    parser.add_argument("--hf-token", help="HuggingFace 令牌（开启说话人区分）", default=os.environ.get("HF_TOKEN"))
    parser.add_argument("--lang", help="语言：zh（中文）、en（英文），留空自动检测", default=None)
    parser.add_argument("--model", default="large-v3",
                        choices=["tiny","base","small","medium","large-v2","large-v3"],
                        help="Whisper 模型大小（默认 large-v3，首次运行自动下载约 1.5GB）")
    parser.add_argument("--output-dir", default=str(Path.home() / "meeting-ai/output"))
    args = parser.parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        print(f"错误：文件不存在：{audio_path}", file=sys.stderr); sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    device = "cpu"
    compute_type = "int8"

    has_diarization = bool(args.hf_token)
    mode = "转录 + 说话人区分" if has_diarization else "仅转录（无说话人区分）"
    print(f"模式：{mode}", flush=True)
    print(f"[1/4] 加载 Whisper {args.model}（首次使用会自动下载模型文件）...", flush=True)

    import whisperx

    model = whisperx.load_model(args.model, device=device, compute_type=compute_type,
                                language=args.lang)

    print(f"[2/4] 转录中：{audio_path.name} ...", flush=True)
    audio = whisperx.load_audio(str(audio_path))
    result = model.transcribe(audio, batch_size=8, language=args.lang)
    lang = result.get("language", args.lang or "zh")
    print(f"      检测语言：{lang}，片段数：{len(result['segments'])}", flush=True)

    print(f"[3/4] 时间戳对齐...", flush=True)
    try:
        model_a, metadata = whisperx.load_align_model(language_code=lang, device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device=device,
                                return_char_alignments=False)
    except Exception as e:
        print(f"      对齐跳过（{e}）", flush=True)

    if has_diarization:
        print(f"[4/4] 说话人区分中（首次使用需下载 pyannote 模型）...", flush=True)
        try:
            diarize_model = whisperx.DiarizationPipeline(use_auth_token=args.hf_token, device=device)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            print(f"      说话人区分完成", flush=True)
        except Exception as e:
            print(f"      说话人区分失败：{e}", flush=True)
            print(f"      提示：请运行 ~/meeting-ai/scripts/setup-hf-token.sh 检查令牌配置", flush=True)
    else:
        print(f"[4/4] 跳过说话人区分（未提供 HF 令牌）", flush=True)
        print(f"      如需区分说话人，运行：~/meeting-ai/scripts/setup-hf-token.sh", flush=True)

    # 每场会议一个文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = audio_path.stem
    meeting_dir = output_dir / f"{stem}_{timestamp}"
    meeting_dir.mkdir(parents=True, exist_ok=True)
    out_txt = meeting_dir / "1-逐字稿.txt"
    out_srt = meeting_dir / "1-字幕.srt"

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(f"# 逐字稿 — {audio_path.name}\n")
        f.write(f"# 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        current_speaker = None
        for seg in result["segments"]:
            sp = seg.get("speaker", "").strip()
            text = seg["text"].strip()
            ts = fmt_time(seg["start"])
            if sp and sp != current_speaker:
                current_speaker = sp
                f.write(f"\n【{sp}】\n")
            f.write(f"[{ts}] {text}\n")

    with open(out_srt, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result["segments"], 1):
            sp = seg.get("speaker", "")
            label = f"[{sp}] " if sp else ""
            f.write(f"{i}\n{fmt_srt(seg['start'])} --> {fmt_srt(seg['end'])}\n{label}{seg['text'].strip()}\n\n")

    print(f"\n✓ 转录完成！")
    print(f"  逐字稿：{out_txt}")
    print(f"  字幕：  {out_srt}")

if __name__ == "__main__":
    main()
