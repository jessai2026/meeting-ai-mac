#!/usr/bin/env python3
"""
多角色朗读脚本：将逐字稿按说话人分配不同声音，生成音频文件
默认使用 macOS 内置中文声音（最快、最稳定）
可选使用 Kokoro TTS（更自然，但仅英文）

用法：
  python read_transcript.py 逐字稿.txt              # macOS 中文声音
  python read_transcript.py 逐字稿.txt --engine kokoro  # Kokoro（英文内容更佳）
"""
import sys
import re
import argparse
import subprocess
import tempfile
import os
from pathlib import Path
from datetime import datetime

# macOS 内置声音池（按角色顺序分配）
# 注意：macOS 26 移除了 Sinji/Meijia/Shanshan，统一改用 (Chinese (China mainland)) 这一组
MACOS_VOICES_ZH = [
    "Tingting",                                # 女声 - 普通话
    "Eddy (Chinese (China mainland))",         # 男声
    "Sandy (Chinese (China mainland))",        # 女声
    "Reed (Chinese (China mainland))",         # 男声
]
MACOS_VOICES_EN = ["Daniel", "Karen", "Moira", "Rishi"]

def parse_transcript(text):
    """解析逐字稿，返回 [(speaker, text), ...]"""
    segments = []
    current_speaker = "旁白"
    buffer = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^【(.+?)】\s*$", line)
        if m:
            if buffer:
                segments.append((current_speaker, " ".join(buffer)))
                buffer = []
            current_speaker = m.group(1)
        else:
            cleaned = re.sub(r"^\[\d+:\d+\]\s*", "", line)
            if cleaned:
                buffer.append(cleaned)
    if buffer:
        segments.append((current_speaker, " ".join(buffer)))
    return segments

def detect_lang(text):
    """简单检测：中文字符占比高就当中文"""
    chinese_chars = len(re.findall(r"[一-鿿]", text))
    return "zh" if chinese_chars > len(text) * 0.3 else "en"

def assign_voices(speakers, lang):
    pool = MACOS_VOICES_ZH if lang == "zh" else MACOS_VOICES_EN
    return {sp: pool[i % len(pool)] for i, sp in enumerate(sorted(set(speakers)))}

def say_segment(text, voice, output_aiff):
    """用 macOS say 生成音频片段（macOS 26 默认 AIFF 格式即可）"""
    cmd = ["say", "-v", voice, "-o", output_aiff, text]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"      say 失败: {r.stderr.strip()}", flush=True)
        return False
    return True

def kokoro_segment(text, voice_name, output_wav, model, voices):
    """用 Kokoro 生成音频片段（英文质量较好）"""
    try:
        import soundfile as sf
        samples, sample_rate = model.create(text, voice=voice_name, speed=1.0, lang="en-us")
        sf.write(output_wav, samples, sample_rate)
        return True
    except Exception as e:
        print(f"      Kokoro 失败：{e}，回退到 say", flush=True)
        return False

def merge_audio_files(file_list, output_path):
    list_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    for f in file_list:
        list_file.write(f"file '{f}'\n")
    list_file.close()
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", list_file.name, "-c:a", "libmp3lame", "-q:a", "2", str(output_path)],
        capture_output=True
    )
    os.unlink(list_file.name)

def main():
    parser = argparse.ArgumentParser(description="逐字稿多角色朗读")
    parser.add_argument("transcript", nargs="?", help="逐字稿文件路径")
    parser.add_argument("--engine", choices=["say", "kokoro"], default="say",
                        help="TTS 引擎：say（macOS内置，中英文均可）/ kokoro（英文更佳）")
    parser.add_argument("--output-dir", default=str(Path.home() / "meeting-ai/output"))
    parser.add_argument("--list-voices", action="store_true", help="列出可用声音")
    args = parser.parse_args()

    if args.list_voices:
        result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
        print("=== macOS 系统声音（中英文）===")
        for line in result.stdout.split("\n"):
            if "zh_CN" in line or "zh_TW" in line or "en_" in line:
                print(" ", line)
        return

    if not args.transcript:
        parser.print_help(); sys.exit(1)

    transcript_path = Path(args.transcript).expanduser().resolve()
    if not transcript_path.exists():
        print(f"错误：文件不存在：{transcript_path}", file=sys.stderr); sys.exit(1)

    base_output = Path(args.output_dir)
    base_output.mkdir(parents=True, exist_ok=True)

    # 智能放置：如果输入在某个会议子文件夹里，MP3 也放进同一文件夹
    if transcript_path.parent != base_output and transcript_path.parent.parent == base_output:
        output_dir = transcript_path.parent
    else:
        output_dir = base_output

    text = transcript_path.read_text(encoding="utf-8")
    segments = parse_transcript(text)
    if not segments:
        print("错误：未解析到说话人内容", file=sys.stderr); sys.exit(1)

    lang = detect_lang(text)
    speakers = [s[0] for s in segments]
    voice_map = assign_voices(speakers, lang)

    print(f"检测语言：{lang}，识别到 {len(set(speakers))} 个说话人，共 {len(segments)} 段")
    print("说话人 → 声音映射：")
    for sp, v in voice_map.items():
        print(f"  {sp}: {v}")

    # Kokoro 仅在英文且用户指定时使用
    use_kokoro = args.engine == "kokoro"
    kokoro_model = None
    kokoro_voices = None
    if use_kokoro:
        if lang == "zh":
            print("⚠️  内容是中文，Kokoro 中文支持有限，自动回退到 macOS say")
            use_kokoro = False
        else:
            try:
                from kokoro_onnx import Kokoro
                print("加载 Kokoro 模型（首次需下载约 300MB）...")
                kokoro_model = Kokoro("kokoro-v0_19.onnx", "voices.json")
            except Exception as e:
                print(f"Kokoro 加载失败：{e}，回退到 say")
                use_kokoro = False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = Path(tempfile.mkdtemp())
    audio_files = []

    print(f"\n生成音频中（共 {len(segments)} 段）...", flush=True)
    for i, (speaker, text_seg) in enumerate(segments):
        if not text_seg.strip():
            continue
        voice = voice_map.get(speaker, MACOS_VOICES_ZH[0])

        # macOS say 限制每次最多约 1000 字，分块
        chunks = [text_seg[j:j+800] for j in range(0, len(text_seg), 800)]
        for j, chunk in enumerate(chunks):
            aiff_path = str(tmp_dir / f"seg_{i:04d}_{j:02d}.aiff")
            if say_segment(chunk, voice, aiff_path):
                audio_files.append(aiff_path)

        if (i + 1) % 10 == 0:
            print(f"  已处理 {i+1}/{len(segments)} 段...", flush=True)

    if not audio_files:
        print("错误：没有生成任何音频", file=sys.stderr); sys.exit(1)

    # 在会议文件夹里用统一名字，否则用带时间戳的名字
    if output_dir != base_output:
        out_mp3 = output_dir / "4-朗读.mp3"
    else:
        out_mp3 = output_dir / f"{transcript_path.stem}_reading_{timestamp}.mp3"
    print(f"\n合并 {len(audio_files)} 个片段为 MP3 ...", flush=True)
    merge_audio_files(audio_files, out_mp3)

    for f in tmp_dir.glob("*"):
        f.unlink()
    tmp_dir.rmdir()

    # 文件大小
    size_mb = out_mp3.stat().st_size / 1024 / 1024
    print(f"\n✓ 朗读音频已生成：{out_mp3} ({size_mb:.1f} MB)")
    print("提示：双击文件用 QuickTime 或 Music 播放")

if __name__ == "__main__":
    main()
