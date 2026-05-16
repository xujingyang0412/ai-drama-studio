# 🎬 AI Drama Studio

**一句话生成完整短剧，从剧本到成片全自动化**

AI Drama Studio 是一个开源的 AI 短剧生成工具，输入一句话描述，自动生成完整短剧视频。

## ✨ 功能特性

- 🎭 **AI剧本生成** - 输入主题/关键词，自动生成完整剧本
- 🎬 **智能分镜** - 自动将剧本拆分为镜头，生成分镜脚本
- 🖼️ **画面生成** - 根据分镜自动生成匹配的画面/图片
- 🗣️ **AI配音** - 多角色语音合成，自动匹配角色声线
- ✂️ **自动剪辑** - 智能拼接、转场、字幕、背景音乐
- 📱 **多平台输出** - 支持抖音/快手/YouTube Shorts 等竖屏格式

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/ai-drama-tools/ai-drama-studio.git
cd ai-drama-studio
pip install -r requirements.txt
```

### 使用

```bash
# 基础模式：一句话生成短剧
python main.py --prompt "一个程序员穿越到古代，用现代知识改变命运"

# 指定时长
python main.py --prompt "霸道总裁爱上女程序员" --duration 60

# 指定风格
python main.py --prompt "悬疑：办公室里的秘密" --style suspense

# 批量生成
python main.py --batch scripts.txt --output ./output
```

## 📋 工作流程

```
用户输入(一句话) 
  → AI生成剧本 
  → 智能分镜拆分 
  → AI生成画面 
  → AI语音合成 
  → 自动剪辑合成 
  → 输出成片(MP4)
```

## 🛠️ 技术栈

- Python 3.10+
- OpenAI / DeepSeek / 通义千问 (剧本生成)
- Stable Diffusion / DALL-E / 通义万相 (画面生成)
- Edge-TTS / Azure TTS (语音合成)
- FFmpeg (视频剪辑)
- Rich (终端UI)

## 💰 商业模式

| 版本 | 价格 | 功能 |
|------|------|------|
| 免费版 | ¥0 | 每天3次，含水印 |
| 基础版 | ¥29/月 | 每天20次，无水印 |
| 专业版 | ¥99/月 | 无限次，批量生成，API |
| 企业版 | ¥499/月 | 私有部署，定制功能 |

## 📊 市场分析

- 短视频市场：2025年预计突破 **1万亿**
- AI视频生成年增长率：**35%+**
- 竞品：huobao-drama (11.6k stars)，short-video-factory (3.9k stars)
- 差异化：更轻量、更易用、支持更多平台

## 📁 项目结构

```
ai-drama-studio/
├── main.py              # 主入口
├── config.py            # 配置管理
├── requirements.txt     # 依赖
├── core/
│   ├── __init__.py
│   ├── script_gen.py    # 剧本生成
│   ├── image_gen.py     # 画面生成
│   ├── voice_gen.py     # 语音合成
│   ├── video_edit.py    # 视频剪辑
│   └── pipeline.py      # 完整流水线
└── README.md
```

## 📄 License

MIT License - 自由使用，商业友好

---

⭐ 觉得有用请给个 Star！
