# AI TTV Workflow

A text-to-video workflow prototype for content operations teams.

The project combines copy preparation, speech synthesis, subtitle generation, visual configuration, and video rendering in a desktop application. It explores how repetitive production steps can be reduced while keeping human review and approval in the process.

## Context

Producing a video from a written script often requires moving text, audio, subtitles, and assets across several tools. The fragmented workflow increases file-management overhead and creates inconsistent content versions.

AI TTV Workflow organizes these steps into a visual pipeline for input, editing, generation, and preview.

## Intended Users

- Operations teams producing knowledge or presenter-style videos
- Product and technical teams validating text-to-video workflows
- Creators who need repeatable voice, subtitle, cover, and layout settings

## Capabilities

- Accept manually entered or extracted text
- Provide AI-assisted rewriting and translation entry points
- Generate speech with Edge TTS
- Create SRT subtitles aligned with the generated audio
- Configure avatars, fonts, author information, background music, and video parameters
- Render audio, video, subtitles, and covers with FFmpeg
- Preview results and monitor task state in a desktop interface

## Workflow

```text
Text input
    -> Review and editing
    -> Speech synthesis
    -> Subtitle generation
    -> Visual configuration
    -> FFmpeg rendering
    -> Preview and export
```

## Code Structure

- `core/app_controller.py`: application orchestration
- `core/services/`: text, speech, and video services
- `core/ui/`: desktop interface and preview components
- `core/utils/`: process, data, and driver management
- `main.py`: application entry point

Core technologies: Python, PyQt5, Edge TTS, Selenium, FFmpeg, and Pillow.

## Quick Start

### Requirements

- Python 3.8+
- FFmpeg available on `PATH`
- Google Chrome when browser-assisted features are enabled

```bash
git clone https://github.com/toki-plus/ai-ttv-workflow.git
cd ai-ttv-workflow
python -m venv venv
```

After activating the virtual environment:

```bash
pip install -r requirements.txt
python main.py
```

## Responsible Use and Limitations

- AI-generated or rewritten content should be reviewed before publication.
- Browser automation depends on third-party page structures and may require maintenance.
- Users must have appropriate rights to all text, audio, video, and other media used in the workflow.
- The current version does not include comprehensive automated tests or CI.

## What This Project Demonstrates

The project demonstrates workflow decomposition, service boundaries, and a human-in-the-loop approach to content automation.

## License

See [LICENSE](./LICENSE).
