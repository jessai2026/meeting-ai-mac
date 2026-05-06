#!/bin/bash
# 快速转录（GPU 加速版）
# 用法：./transcribe_fast.sh <音频文件> [--lang zh] [--model large-v3-turbo]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV="$HOME/meeting-ai/whisper-env/bin/python"

if [ -z "$1" ]; then
    echo "用法: $0 <音频文件> [--lang zh] [--model large-v3-turbo]"
    echo "  --model 默认 large-v3-turbo（最快，质量接近 large-v3）"
    echo "          可选：tiny/base/small/medium/large-v2/large-v3/large-v3-turbo"
    echo ""
    echo "示例: $0 ~/Desktop/会议.mp4"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ⚡ 快速转录（MLX GPU 加速）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

"$ENV" "$SCRIPT_DIR/transcribe_fast.py" "$@"
