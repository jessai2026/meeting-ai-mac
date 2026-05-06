#!/bin/bash
# 会议转录一键脚本
# 用法：./transcribe.sh <音频/视频文件> [--hf-token 你的HF令牌]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV="$HOME/meeting-ai/whisper-env/bin/python"

if [ -z "$1" ]; then
    echo "用法: $0 <音频文件> [--hf-token TOKEN] [--lang zh] [--model large-v3]"
    echo "示例: $0 meeting.mp4 --hf-token hf_xxxxx"
    exit 1
fi

echo "================================"
echo "  会议转录工具（WhisperX）"
echo "================================"

"$ENV" "$SCRIPT_DIR/transcribe.py" "$@"
