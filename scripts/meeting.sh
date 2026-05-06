#!/bin/bash
# 全流程一键脚本：转录 → 去口水词 → 摘要 → （可选）朗读
# 用法：./meeting.sh <音频文件> [--hf-token TOKEN] [--read]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WHISPER_PY="$HOME/meeting-ai/whisper-env/bin/python"

HF_TOKEN=""
DO_READ=false
AUDIO_FILE=""
EXTRA_ARGS=()

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --hf-token) HF_TOKEN="$2"; shift 2 ;;
        --read) DO_READ=true; shift ;;
        -*) EXTRA_ARGS+=("$1" "$2"); shift 2 ;;
        *) AUDIO_FILE="$1"; shift ;;
    esac
done

if [ -z "$AUDIO_FILE" ]; then
    echo "用法: $0 <音频/视频文件> [--hf-token TOKEN] [--read]"
    echo "  --hf-token  HuggingFace 令牌（说话人区分，可选）"
    echo "  --read      完成后自动朗读摘要"
    echo ""
    echo "示例: $0 zoom_recording.mp4 --hf-token hf_xxx"
    exit 1
fi

START=$(date +%s)
echo ""
echo "╔══════════════════════════════════════╗"
echo "║       会议 AI 全流程处理工具         ║"
echo "╚══════════════════════════════════════╝"
echo "文件: $AUDIO_FILE"
echo ""

# Step 1: 转录
TRANSCRIPT_ARGS=("$AUDIO_FILE")
[ -n "$HF_TOKEN" ] && TRANSCRIPT_ARGS+=(--hf-token "$HF_TOKEN")
TRANSCRIPT_ARGS+=("${EXTRA_ARGS[@]}")

echo "── 步骤 1/3：转录 ─────────────────────"
TRANSCRIPT_OUT=$("$WHISPER_PY" "$SCRIPT_DIR/transcribe.py" "${TRANSCRIPT_ARGS[@]}" | grep "逐字稿：" | sed 's/.*逐字稿：//')

if [ -z "$TRANSCRIPT_OUT" ]; then
    # 找最新的输出文件
    TRANSCRIPT_OUT=$(ls -t "$HOME/meeting-ai/output/"*.txt 2>/dev/null | head -1)
fi

echo ""
echo "── 步骤 2/3：整理 & 摘要 ──────────────"
"$WHISPER_PY" "$SCRIPT_DIR/summarize.py" "$TRANSCRIPT_OUT"

SUMMARY_OUT=$(ls -t "$HOME/meeting-ai/output/"*_summary_*.md 2>/dev/null | head -1)

if $DO_READ && [ -n "$SUMMARY_OUT" ]; then
    echo ""
    echo "── 步骤 3/3：朗读摘要 ─────────────────"
    # 用系统 say 命令朗读摘要（去掉 markdown 符号）
    SUMMARY_TEXT=$(cat "$SUMMARY_OUT" | sed 's/#//g; s/✅//g; s/⚠️//g; s/\*\*//g; s/---//g')
    say -v Tingting "$SUMMARY_TEXT" &
    SAY_PID=$!
    echo "正在朗读摘要（按 Ctrl+C 停止）..."
    wait $SAY_PID 2>/dev/null || true
fi

END=$(date +%s)
ELAPSED=$((END - START))
echo ""
echo "══════════════════════════════════════"
echo "完成！总耗时：${ELAPSED}秒"
echo "输出目录：$HOME/meeting-ai/output/"
echo "══════════════════════════════════════"
