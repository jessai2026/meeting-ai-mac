#!/bin/bash
# 全流程一键脚本：转录 → 去口水词 → 摘要 →（可选）朗读
# 默认走 MLX GPU 加速版（M3 Max 上 1-2 分钟处理 16 分钟视频）
#
# 用法：
#   ./meeting.sh 文件.mp4                     # 默认快速模式
#   ./meeting.sh 文件.mp4 --slow              # 用 CPU 模式（更准但慢）
#   ./meeting.sh 文件.mp4 --hf-token $HF_TOKEN # 区分说话人（自动用 CPU 模式）
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WHISPER_PY="$HOME/meeting-ai/whisper-env/bin/python"

HF_TOKEN=""
DO_READ=false
USE_SLOW=false
AUDIO_FILE=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --hf-token) HF_TOKEN="$2"; shift 2 ;;
        --read) DO_READ=true; shift ;;
        --slow) USE_SLOW=true; shift ;;
        -*) EXTRA_ARGS+=("$1"); [ -n "$2" ] && [[ "$2" != -* ]] && EXTRA_ARGS+=("$2") && shift; shift ;;
        *) AUDIO_FILE="$1"; shift ;;
    esac
done

if [ -z "$AUDIO_FILE" ]; then
    echo "用法: $0 <音频/视频文件> [--hf-token TOKEN] [--slow] [--read]"
    echo "  --hf-token  HuggingFace 令牌（区分说话人，会自动切到 CPU 模式）"
    echo "  --slow      用 CPU 模式（更准但慢 5-10x）"
    echo "  --read      完成后用 macOS say 朗读纪要"
    exit 1
fi

# 有 HF 令牌时用 CPU 模式（要做说话人区分）
if [ -n "$HF_TOKEN" ]; then
    USE_SLOW=true
fi

START=$(date +%s)
echo ""
echo "╔══════════════════════════════════════╗"
echo "║       会议 AI 全流程处理工具         ║"
echo "╚══════════════════════════════════════╝"
echo "文件: $AUDIO_FILE"
if $USE_SLOW; then
    echo "模式: 🐢 完整模式 (CPU + 说话人区分)"
else
    echo "模式: ⚡ 快速模式 (MLX GPU 加速，约 5-10x)"
fi
echo ""

# Step 1: 转录
echo "── 步骤 1/2：转录 ─────────────────────"

if $USE_SLOW; then
    TRANSCRIPT_ARGS=("$AUDIO_FILE")
    [ -n "$HF_TOKEN" ] && TRANSCRIPT_ARGS+=(--hf-token "$HF_TOKEN")
    TRANSCRIPT_ARGS+=("${EXTRA_ARGS[@]}")
    "$WHISPER_PY" "$SCRIPT_DIR/transcribe.py" "${TRANSCRIPT_ARGS[@]}"
else
    "$WHISPER_PY" "$SCRIPT_DIR/transcribe_fast.py" "$AUDIO_FILE" "${EXTRA_ARGS[@]}"
fi

# 找最新生成的逐字稿（新结构：output/会议名_时间戳/1-逐字稿.txt）
TRANSCRIPT_OUT=$(ls -t "$HOME/meeting-ai/output/"*/1-逐字稿.txt 2>/dev/null | head -1)
# 兼容旧的扁平结构
if [ -z "$TRANSCRIPT_OUT" ]; then
    TRANSCRIPT_OUT=$(ls -t "$HOME/meeting-ai/output/"*.txt 2>/dev/null | grep -v "_clean_" | grep -v "_summary_" | head -1)
fi

if [ -z "$TRANSCRIPT_OUT" ] || [ ! -f "$TRANSCRIPT_OUT" ]; then
    echo "❌ 找不到生成的逐字稿"
    exit 1
fi

echo ""
echo "── 步骤 2/2：整理 + 摘要 ──────────────"
"$WHISPER_PY" "$SCRIPT_DIR/summarize.py" "$TRANSCRIPT_OUT"

SUMMARY_OUT=$(ls -t "$HOME/meeting-ai/output/"*/3-纪要.md 2>/dev/null | head -1)
[ -z "$SUMMARY_OUT" ] && SUMMARY_OUT=$(ls -t "$HOME/meeting-ai/output/"*_summary_*.md 2>/dev/null | head -1)

if $DO_READ && [ -n "$SUMMARY_OUT" ]; then
    echo ""
    echo "── 朗读纪要 ─────────────────"
    SUMMARY_TEXT=$(cat "$SUMMARY_OUT" | sed 's/#//g; s/✅//g; s/⚠️//g; s/\*\*//g; s/---//g')
    say -v Tingting "$SUMMARY_TEXT" &
    echo "正在朗读（按 Ctrl+C 停止）..."
    wait $! 2>/dev/null || true
fi

END=$(date +%s)
ELAPSED=$((END - START))
echo ""
echo "══════════════════════════════════════"
echo "✅ 完成！总耗时：${ELAPSED}秒"
echo "📂 输出目录：$HOME/meeting-ai/output/"
echo "══════════════════════════════════════"
