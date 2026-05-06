#!/bin/bash
# 配置 HuggingFace 令牌（说话人区分功能必需）
echo ""
echo "═══════════════════════════════════════════════"
echo "  配置 HuggingFace 令牌（说话人区分功能）"
echo "═══════════════════════════════════════════════"
echo ""
echo "步骤："
echo "1. 打开浏览器访问：https://huggingface.co/join"
echo "   注册一个免费账号（或已有账号直接登录）"
echo ""
echo "2. 访问以下两个模型页面，点击 'Agree' 接受使用条款："
echo "   · https://huggingface.co/pyannote/speaker-diarization-3.1"
echo "   · https://huggingface.co/pyannote/segmentation-3.0"
echo ""
echo "3. 创建访问令牌："
echo "   · 访问：https://huggingface.co/settings/tokens"
echo "   · 点击 'New token'，选择 'Read' 权限"
echo "   · 复制令牌（格式：hf_xxxxxxxxxxxxxxxxxx）"
echo ""
echo "4. 将令牌保存到配置文件（这样不用每次输入）："
echo "   echo 'HF_TOKEN=hf_你的令牌' >> ~/.zshrc"
echo "   source ~/.zshrc"
echo ""
read -p "现在输入你的 HF 令牌（直接回车跳过）: " TOKEN

if [ -n "$TOKEN" ]; then
    # 写入 zshrc
    if grep -q "HF_TOKEN=" ~/.zshrc 2>/dev/null; then
        sed -i '' "s|export HF_TOKEN=.*|export HF_TOKEN=$TOKEN|" ~/.zshrc
    else
        echo "export HF_TOKEN=$TOKEN" >> ~/.zshrc
    fi
    source ~/.zshrc
    echo ""
    echo "✅ 令牌已保存！之后运行："
    echo "   ./transcribe.sh 文件.mp4 --hf-token \$HF_TOKEN"
    echo "   # 或使用全流程："
    echo "   ./meeting.sh 文件.mp4 --hf-token \$HF_TOKEN"
else
    echo "已跳过。没有 HF 令牌时，转录依然正常工作，但说话人无法区分。"
fi
