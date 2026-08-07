# AI TTV Workflow

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

- 接收手动输入的文案或提取后的文本
- 提供 AI 辅助改写与翻译入口
- 使用 Edge TTS 生成语音
- 生成与音频匹配的 SRT 字幕
- 配置头像、字体、作者信息、背景音乐与视频参数
- 使用 FFmpeg 完成音视频合成和封面生成
- 在桌面界面中预览结果并管理任务状态

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
- FFmpeg（需加入 `PATH`）
- Google Chrome（仅在启用浏览器辅助功能时需要）

```bash
git clone https://github.com/toki-plus/ai-ttv-workflow.git
cd ai-ttv-workflow
python -m venv venv
```

激活虚拟环境后：

```bash
pip install -r requirements.txt
python main.py
```

## 使用边界

- AI 生成或改写的内容应由用户审核后再发布。
- 浏览器自动化依赖第三方页面结构，页面变更可能影响相关功能。
- 用户应确保输入文本、音视频素材和发布内容拥有合法使用权。
- 当前版本尚未建立完整的自动化测试与 CI。

## 项目价值

本项目展示了对内容生产流程的拆解、服务模块边界设计，以及将人工确认点保留在自动化流程中的产品思考。

## License

See [LICENSE](./LICENSE).
