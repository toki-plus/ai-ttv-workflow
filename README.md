# AI TTV Workflow

[简体中文](./README.md) | [English](./README_en.md)

面向内容团队的文本到视频生产工作流原型。

项目将文案处理、语音合成、字幕生成、画面配置和视频渲染整合在一个桌面应用中，用于验证如何减少短视频生产中的重复操作，同时保留人工编辑和确认环节。

## 项目背景

将一段文案制作成可发布视频，通常需要在多个工具之间反复传递文本、音频、字幕和素材。流程割裂会增加文件管理成本，也容易造成内容版本不一致。

AI TTV Workflow 将这些步骤组织成可视化流水线，使用户能够在同一个界面中完成输入、编辑、生成与预览。

## 目标用户

- 需要批量制作知识类或口播类内容的运营团队
- 希望验证文本转视频流程的产品与技术人员
- 需要可重复字幕、配音和封面配置的内容创作者

## 主要能力

- **文案获取与加工**：接收手动输入的文案，或粘贴视频分享链接自动提取文本；提供 AI 辅助改写与翻译入口，翻译支持数十种语言，改写结果始终交由用户编辑确认
- **语音合成与参数调校**：使用 Edge TTS 生成覆盖多语言、多发音人的自然语音，支持语速、音调、音量微调以匹配内容情绪
- **字幕同步生成**：在生成音频的同时输出与时间轴对齐的 SRT 字幕，无需二次对轴
- **品牌视觉配置**：配置圆形头像、字体、作者信息、背景音乐与视频参数；自动生成适用于短视频平台的 9:16 竖屏封面
- **渲染与硬件加速**：使用 FFmpeg 完成音视频合成、字幕嵌入和封面生成，支持 NVIDIA NVENC GPU 加速以缩短渲染时间
- **桌面任务管理**：在 PyQt5 界面中预览结果、管理任务状态；浏览器辅助功能首次使用时自动下载匹配当前 Chrome 版本的驱动，免去手工配置

## 📸 软件截图

<p align="center">
  <a href="https://www.bilibili.com/video/BV1mzhXzsEJ1" target="_blank">
    <img src="./assets/images/cover_demo.png" alt="演示视频封面" width="800"/>
  </a>
  <br>
  <em>演示视频封面（点击图片跳转观看完整演示）。</em>
</p>
<p align="center">
  <img src="./assets/images/cover_software.png" alt="软件主界面" width="800"/>
  <br>
  <em>软件主界面：工作流的每个步骤从上到下一目了然。</em>
</p>
<p align="center">
  <img src="./assets/images/cover_video.jpg" alt="生成的封面示例" width="300"/>
  <br>
  <em>自动生成的 9:16 竖屏封面示例。</em>
</p>

## 工作流

```text
Text input
    -> Review and editing
    -> Speech synthesis
    -> Subtitle generation
    -> Visual configuration
    -> FFmpeg rendering
    -> Preview and export
```

## 代码结构

- `core/app_controller.py`：应用流程编排
- `core/services/`：文本、语音和视频服务
- `core/ui/`：桌面界面与预览组件
- `core/utils/`：任务进程、数据与驱动管理
- `main.py`：应用入口

主要技术：Python、PyQt5、Edge TTS、Selenium、FFmpeg、Pillow。

## 快速开始

### 环境要求

- Python 3.8+
- FFmpeg（需加入 `PATH`，可用 `ffmpeg -version` 验证）
- Google Chrome（仅在启用浏览器辅助功能时需要）

### 安装与启动

1. 克隆仓库并创建虚拟环境：

```bash
git clone https://github.com/toki-plus/ai-ttv-workflow.git
cd ai-ttv-workflow
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行程序：

```bash
python main.py
```

首次使用浏览器辅助功能时，程序会自动下载匹配当前 Chrome 版本的 `chromedriver`。界面从上到下的布局即为推荐工作流：获取或输入文案 → 编辑润色 → 选择声音并调整语速/音调/音量 → 生成音频与字幕 → 配置头像、字体、BGM 等参数（有 NVIDIA 显卡可开启 GPU 加速）→ 生成视频与封面。

## 使用边界

- AI 生成或改写的内容应由用户审核后再发布。
- 浏览器自动化依赖第三方页面结构，页面变更可能影响相关功能。
- 用户应确保输入文本、音视频素材和发布内容拥有合法使用权。
- 当前版本尚未建立完整的自动化测试与 CI。

## 项目价值

本项目展示了对内容生产流程的拆解、服务模块边界设计，以及将人工确认点保留在自动化流程中的产品思考：文案编辑、声音选择、参数配置等环节均保留人工决策入口，自动化只负责重复性的传递与渲染。

## 📂 更多项目

- [video-mover](https://github.com/toki-plus/video-mover) — 多平台内容分发自动化流水线：素材处理、文案生成、定时调度与多平台适配
- [ai-highlight-clip](https://github.com/toki-plus/ai-highlight-clip) — 长视频智能初筛：Whisper 转写 + LLM 评分 + 人工终审，分钟级定位高光片段
- [ai-video-workflow](https://github.com/toki-plus/ai-video-workflow) — 多模型 AIGC 视频生成流水线：文生图、图生视频、文生音乐的异步编排
- [ai-mixed-cut](https://github.com/toki-plus/ai-mixed-cut) — 素材库结构化与脚本重组的视频再创作工作流
- [ai-trader-for-mt4](https://github.com/toki-plus/ai-trader-for-mt4) — LLM×MT4 受控执行框架：工具约束、风控规则、状态管理与异步桥接
- [ai-trader-for-mt5](https://github.com/toki-plus/ai-trader-for-mt5) — 面向 MT5 的 AI 交易助手与 EA 工程化框架
- [auto-usps-tracker](https://github.com/toki-plus/auto-usps-tracker) — 跨境电商批量物流追踪与 Excel 报告自动化
- [AB-Video-Deduplicator](https://github.com/toki-plus/AB-Video-Deduplicator) — 基于高帧率抽帧混合的视频再创作实验工具
- [netease-downloader](https://github.com/toki-plus/netease-downloader) — 网易云音乐下载桌面应用：扫码登录、下载队列、ID3 元数据写入

## License

See [LICENSE](./LICENSE).
