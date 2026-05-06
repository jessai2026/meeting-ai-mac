#!/bin/bash
# 会议摘要一键脚本
# 用法：./summarize.sh <逐字稿.txt> [--model qwen2.5:32b]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV="$HOME/meeting-ai/whisper-env/bin/python"

if [ -z "$1" ]; then
    echo "用法: $0 <逐字稿文件.txt> [--model qwen2.5:32b] [--skip-clean]"
    echo "示例: $0 ~/meeting-ai/output/meeting_20260507.txt"
    exit 1
fi

echo "================================"
echo "  会议摘要工具（Ollama / qwen14b-32k）"
echo "================================"

"$ENV" "$SCRIPT_DIR/summarize.py" "$@"
