#!/bin/bash
# Meeting AI · 一键安装脚本
# 适配：Apple Silicon Mac (M1/M2/M3/M4) + macOS 13+
set -e

INSTALL_DIR="$HOME/meeting-ai"
USE_CN_MIRROR="${USE_CN_MIRROR:-auto}"  # auto / yes / no

# 颜色
G='\033[0;32m'  # green
Y='\033[0;33m'  # yellow
R='\033[0;31m'  # red
B='\033[0;34m'  # blue
N='\033[0m'

log()  { echo -e "${G}▸${N} $1"; }
warn() { echo -e "${Y}⚠${N} $1"; }
err()  { echo -e "${R}✗${N} $1"; exit 1; }
header() { echo ""; echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"; echo -e "${B}  $1${N}"; echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"; }

# 自动检测国内网络
detect_mirror() {
    if [ "$USE_CN_MIRROR" = "auto" ]; then
        if curl -sm 3 https://pypi.org -o /dev/null; then
            USE_CN_MIRROR="no"
        else
            USE_CN_MIRROR="yes"
            log "检测到 PyPI 访问慢，自动启用阿里云镜像"
        fi
    fi
    if [ "$USE_CN_MIRROR" = "yes" ]; then
        PIP_MIRROR="--index-url https://mirrors.aliyun.com/pypi/simple/"
    else
        PIP_MIRROR=""
    fi
}

header "Meeting AI 一键安装"
echo "目标目录：$INSTALL_DIR"

# 1. Homebrew
header "[1/8] 检查 Homebrew"
if ! command -v brew &>/dev/null; then
    log "安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    log "Homebrew 已就绪：$(brew --version | head -1)"
fi

# 2. 系统依赖
header "[2/8] 安装系统依赖"
for pkg in ffmpeg uv ollama blackhole-2ch; do
    if brew list --formula | grep -q "^${pkg}$" || brew list --cask | grep -q "^${pkg}$"; then
        log "$pkg 已就绪"
    else
        log "安装 $pkg..."
        brew install "$pkg" || warn "$pkg 安装失败，可能需要手动处理"
    fi
done

# 3. 创建目录
header "[3/8] 准备工作目录"
mkdir -p "$INSTALL_DIR"/{recordings,output,models}
log "目录已创建"

# 4. Python 3.11 + 虚拟环境
header "[4/8] 创建 Python 环境"
cd "$INSTALL_DIR"
detect_mirror

uv python install 3.11 2>&1 | tail -1
[ ! -d whisper-env ] && uv venv whisper-env --python 3.11
[ ! -d tts-env ] && uv venv tts-env --python 3.11
log "whisper-env / tts-env 已创建"

# 5. 装 PyTorch
header "[5/8] 安装 PyTorch（约 700MB）"
log "→ whisper-env"
uv pip install --python whisper-env/bin/python $PIP_MIRROR torch torchaudio 2>&1 | tail -2
log "→ tts-env"
uv pip install --python tts-env/bin/python $PIP_MIRROR torch torchaudio 2>&1 | tail -2

# 6. 装转录工具
header "[6/8] 安装转录工具（WhisperX + pyannote）"
uv pip install --python whisper-env/bin/python $PIP_MIRROR \
    faster-whisper pyannote.audio pandas 2>&1 | tail -3
# whisperx 部分镜像没有，用官方源
uv pip install --python whisper-env/bin/python --retries 5 \
    whisperx 2>&1 | tail -3
log "WhisperX 完成"

# 7. 装朗读工具
header "[7/8] 安装朗读工具（Kokoro TTS）"
uv pip install --python tts-env/bin/python $PIP_MIRROR \
    kokoro-onnx soundfile 2>&1 | tail -3
log "Kokoro 完成"

# 8. 拉取 LLM 模型
header "[8/8] 拉取 Qwen2.5:14b 模型（9GB，可能较慢）"
if ollama list 2>/dev/null | grep -q "qwen2.5:14b"; then
    log "qwen2.5:14b 已存在"
else
    log "开始下载（在后台进行，可继续配置其他）..."
    ollama pull qwen2.5:14b
fi

# 9. 桌面 App
header "[额外] 生成桌面拖拽 App"
if [ -f desktop-app/meeting-ai-app.applescript ]; then
    osacompile -o "$HOME/Desktop/会议AI.app" desktop-app/meeting-ai-app.applescript 2>&1 | tail -2 || true
    log "拖拽 App 已生成：~/Desktop/会议AI.app"
fi

# 10. 脚本权限
chmod +x "$INSTALL_DIR/scripts/"*.sh
log "脚本可执行权限已设置"

# 完成
header "✅ 安装完成！"
cat <<EOF

接下来要做的事：

1. 配置音频路由（5 分钟）
   见：$INSTALL_DIR/BlackHole配置指南.md

2. 申请 HuggingFace 令牌（区分说话人）
   $INSTALL_DIR/scripts/setup-hf-token.sh

3. 试一下！
   方式 A：拖任意视频文件到桌面「会议AI.app」
   方式 B：cd $INSTALL_DIR/scripts && ./meeting.sh 录音.mp4

详细教程：$INSTALL_DIR/README.md

EOF
