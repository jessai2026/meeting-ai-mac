#!/bin/bash
# 把中文纪要翻成英文 + 用 Kokoro 朗读
# 用法：./translate-read.sh <纪要.md>
set -e

if [ -z "$1" ]; then
    echo "用法: $0 <中文文件.md/txt>"
    echo "示例: $0 ~/meeting-ai/output/会议_summary.md"
    exit 1
fi

INPUT="$1"
STEM=$(basename "$INPUT" | sed 's/\.[^.]*$//')
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EN_FILE="$HOME/meeting-ai/output/${STEM}_en_${TIMESTAMP}.txt"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌐 翻译为英文 + 英文朗读"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: 用本地 Qwen 翻译
echo "[1/2] 翻译为英文..."
PROMPT="Translate the following Chinese meeting summary into natural, professional English. Keep the structure (headings, bullet points). Output ONLY the English translation, no explanation.

Chinese content:
---
$(cat "$INPUT")
---"

ollama run qwen2.5:14b "$PROMPT" > "$EN_FILE"
echo "   ✓ 英文译稿：$EN_FILE"
echo ""

# Step 2: 朗读
echo "[2/2] 调用 Kokoro 英文朗读..."
~/meeting-ai/scripts/read.sh "$EN_FILE" --engine kokoro

echo ""
echo "✅ 完成！MP3 在 ~/meeting-ai/output/"
