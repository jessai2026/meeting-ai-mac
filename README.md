# 🎙️ Meeting AI · 本地会议处理工作流

> Mac 上完全免费、全本地、跨平台的会议处理流水线
> **录音 → 转录 → 区分说话人 → 去口水词 → 生成纪要 → 多角色朗读**

适配任意会议软件（Zoom、腾讯会议、飞书会议、Google Meet…），数据不出本地。

## ✨ 特性

- ⚡ **GPU 加速转录** — MLX 框架原生用 Apple Silicon GPU，M3 Max 上 1 小时视频 4 分钟搞定
- 🎯 **跨软件录制** — 通过 BlackHole 虚拟音频驱动，捕获任意会议软件的声音
- 🗣️ **说话人区分** — pyannote 自动标注「张三说了什么、李四说了什么」
- 🤖 **AI 去口水词 + 摘要** — 本地 Ollama + Qwen2.5 模型，私密快速
- 🎧 **多角色朗读** — 把会议纪要做成 MP3，路上听
- 🖱️ **拖拽 App** — 不想敲命令？拖文件到桌面 App 自动跑全流程
- 🔒 **完全本地** — 音频、文字、模型全部在你电脑上，不上传任何地方

## ⚡ 性能基准（M3 Max 36GB）

| 模式 | 16 分钟视频 | 1 小时视频 | 说话人区分 |
|------|-----------|----------|----------|
| ⚡ MLX GPU（默认）| ~1.5 分钟 | ~5 分钟 | ❌ |
| 🐢 CPU 完整版 | ~8 分钟 | ~30 分钟 | ✅ |

> 默认走 MLX 加速，加 `--hf-token` 自动切到完整模式

## 📋 硬件要求

| 配置 | 推荐 | 最低 |
|------|------|------|
| 芯片 | Apple Silicon (M1/M2/M3/M4) | Intel Mac 也可用，但慢 |
| 内存 | 16GB+ | 8GB（用 7B 小模型） |
| 磁盘 | 30GB 空闲 | 15GB（不装大模型） |
| macOS | 13+ | 12+ |

实测 M3 Max 36GB：1 小时会议处理约 20 分钟。

## 🚀 快速开始

### 一键安装（推荐）

```bash
git clone https://github.com/jessai2026/meeting-ai-mac.git ~/meeting-ai
cd ~/meeting-ai
./install.sh
```

`install.sh` 会自动：
- 装 Homebrew、ffmpeg、BlackHole（如缺）
- 创建 Python 3.11 隔离环境
- 装 WhisperX、faster-whisper、pyannote、Kokoro TTS
- 拉取 Ollama + qwen2.5:14b 模型
- 生成桌面拖拽 App

### 手动配置（一次性）

1. **音频路由**：见 [BlackHole配置指南.md](BlackHole配置指南.md)
2. **HuggingFace 令牌**（区分说话人需要）：`./scripts/setup-hf-token.sh`

## 💡 使用方式

### 方式 1：拖拽 App（最简单）

```
任意视频 / 录音文件 → 拖到桌面「会议AI.app」图标 → 等结果
```

输出自动打开 `~/meeting-ai/output/`：
- `xxx.txt` — 带时间戳的逐字稿（含说话人标签）
- `xxx.srt` — SRT 字幕，可挂在视频上
- `xxx_clean.txt` — 去口水词的干净版
- `xxx_summary.md` — 结构化纪要（议题/决策/待办）

### 方式 2：命令行（适合自动化）

```bash
cd ~/meeting-ai/scripts

# 全流程：转录 + 整理 + 摘要
./meeting.sh ~/Downloads/会议.mp4 --hf-token $HF_TOKEN

# 仅转录
./transcribe.sh 文件.mp4 --lang zh

# 已有逐字稿，仅摘要
./summarize.sh 逐字稿.txt

# 多角色朗读（生成 MP3）
./read.sh 逐字稿.txt
```

## 🏗️ 架构

```
┌─ 录音 ──────────────┐
│  BlackHole (系统音频) │
│  + 麦克风             │
│  → m4a / mp4          │
└──────────┬───────────┘
           ↓
┌─ 转录 ──────────────────────────────┐
│  WhisperX + faster-whisper (large-v3) │
│  pyannote (说话人区分)                 │
│  → 带说话人标签的逐字稿                 │
└──────────┬─────────────────────────┘
           ↓
┌─ 整理 ──────────────┐
│  Ollama + Qwen2.5:14b │
│  → 去口水词版          │
│  → 结构化会议纪要      │
└──────────┬───────────┘
           ↓
┌─ 朗读（可选）─────────┐
│  macOS say (中文)     │
│  Kokoro TTS (英文)     │
│  → MP3 音频            │
└──────────────────────┘
```

## 📁 项目结构

```
meeting-ai/
├── scripts/                  # 核心脚本
│   ├── meeting.sh           # ⭐ 全流程一键
│   ├── transcribe.sh        # 转录
│   ├── summarize.sh         # 整理 + 摘要
│   ├── read.sh              # 多角色朗读
│   ├── record.sh            # 命令行录音
│   ├── setup-hf-token.sh    # 配置 HuggingFace 令牌
│   ├── transcribe.py        # 转录 Python 实现
│   ├── summarize.py         # 摘要 Python 实现
│   └── read_transcript.py   # 朗读 Python 实现
├── desktop-app/             # macOS 拖拽 App 源码
│   └── meeting-ai-app.applescript
├── install.sh               # 一键安装脚本
├── BlackHole配置指南.md      # 音频路由配置
├── 安装汇总报告.md           # 详细安装记录
└── README.md
```

## 🔧 已知坑位

| 问题 | 解决 |
|------|------|
| 大模型下载慢 | 国内用阿里云镜像：见 install.sh 注释 |
| pyannote 启动有警告 | 是 torchcodec 的警告，不影响功能 |
| say 命令读不动长文本 | 脚本已自动按 800 字分块 |
| macOS 升级后 BlackHole 失效 | `brew reinstall blackhole-2ch` |
| Whisper 首次启动卡住 | 在下模型，等 5-10 分钟 |

## 🛠️ 技术栈

| 模块 | 工具 | 用途 |
|------|------|------|
| 系统音频捕获 | [BlackHole](https://github.com/ExistentialAudio/BlackHole) | 虚拟音频驱动 |
| 语音转文字 | [WhisperX](https://github.com/m-bain/whisperX) | Whisper 增强版 |
| 语音引擎 | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | CTranslate2 优化 |
| 说话人区分 | [pyannote.audio](https://github.com/pyannote/pyannote-audio) | 说话人嵌入 |
| 本地大模型 | [Ollama](https://ollama.com) | 模型运行时 |
| 摘要模型 | [Qwen2.5:14b](https://qwenlm.github.io/blog/qwen2.5/) | 阿里通义千问 |
| 中文 TTS | macOS `say` | 系统内置 |
| 英文 TTS | [Kokoro](https://github.com/hexgrad/kokoro) | 高质量轻量 TTS |
| Python 包管理 | [uv](https://github.com/astral-sh/uv) | 比 pip 快 100x |

## 📝 License

MIT

## 🤝 致谢

Inspired by:
- 飞书妙记的产品体验
- m-bain/whisperX 的工程实现
- 隐私本地化运动 (privacy-first local AI)

---

**问题反馈**：开 [Issue](https://github.com/jessai2026/meeting-ai-mac/issues) 或者 PR 直接来。
