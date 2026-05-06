#!/bin/bash
# 逐字稿多角色朗读脚本
# 用法：./read.sh <逐字稿.txt> [--ref-audio 张三:/path/a.wav,李四:/path/b.wav]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV="$HOME/meeting-ai/whisper-env/bin/python"

if [ -z "$1" ]; then
    echo "用法: $0 <逐字稿文件.txt> [--ref-audio 姓名:音频路径,...]"
    echo ""
    echo "示例（使用系统声音）:"
    echo "  $0 ~/meeting-ai/output/transcript.txt"
    echo ""
    echo "示例（使用声音克隆，需要 F5-TTS）:"
    echo "  $0 transcript.txt --ref-audio 张三:~/recordings/zhangsan_ref.wav"
    echo ""
    echo "查看可用系统声音:"
    echo "  $0 --list-voices"
    exit 1
fi

echo "================================"
echo "  逐字稿朗读工具"
echo "================================"

"$ENV" "$SCRIPT_DIR/read_transcript.py" "$@"
