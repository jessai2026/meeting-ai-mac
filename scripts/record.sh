#!/bin/bash
# 一键录音脚本（需要先按 BlackHole配置指南.md 配置好聚合设备）
# 用法：./record.sh [输出文件名（不含扩展名）]
set -e

OUTPUT_DIR="$HOME/meeting-ai/recordings"
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NAME="${1:-meeting_$TIMESTAMP}"
OUTPUT="$OUTPUT_DIR/${NAME}.wav"

# 检测聚合设备（用 ffmpeg 录音）
echo "================================"
echo "  录音工具（按 Ctrl+C 停止）"
echo "================================"
echo "输出文件: $OUTPUT"
echo ""

# 检查是否有 ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "错误：未找到 ffmpeg，请运行：brew install ffmpeg"
    exit 1
fi

echo "开始录音... 按 Ctrl+C 停止"
echo ""

# 用 ffmpeg 录制（自动选择默认输入设备）
# 如果聚合设备设为系统默认输入，就会录到两路声音
ffmpeg -f avfoundation -i ":0" \
       -ar 44100 -ac 2 \
       "$OUTPUT" \
       2>&1 | grep -E "(Duration|size=|Press)" || true

echo ""
echo "录音已保存：$OUTPUT"
echo ""
echo "下一步 - 转录此录音："
echo "  cd ~/meeting-ai/scripts"
echo "  ./transcribe.sh \"$OUTPUT\""
echo ""
echo "或直接全流程处理："
echo "  ./meeting.sh \"$OUTPUT\""
