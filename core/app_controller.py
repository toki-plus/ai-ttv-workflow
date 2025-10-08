import os
import re
import json
from datetime import datetime
from typing import Callable, Any, Optional

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QMessageBox

from .utils.chromedriver_downloader import ChromedriverDownloader
from .utils.process_worker import ProcessWorker
from .services.tts_service import TTSService, TaskSignals, AsyncioRunner
from .services.doubao_service import DoubaoProvider
from .services.video_service import VideoCreationService

class AppController(QObject):
    def __init__(self, view: 'VideoWorkflowApp'):
        super().__init__()
        self.view = view
        self.worker: Optional[ProcessWorker] = None
        self.chromedriver_downloader = ChromedriverDownloader(status_callback=self.view.update_status, error_callback=self.view.on_task_error)

        self.async_runner = AsyncioRunner()
        self.async_runner.start()

        self.task_signals = TaskSignals()
        self.tts_service = TTSService(self.async_runner, self.task_signals)

        self.task_signals.voices_ready.connect(self.view.on_voices_loaded)
        self.task_signals.voices_error.connect(self.view.on_task_error)
        self.task_signals.tts_finished.connect(self.on_tts_finished)
        self.task_signals.tts_error.connect(self.view.on_task_error)
        self.task_signals.task_progress.connect(self.view.update_status)

    def start_app(self):
        self.tts_service.fetch_voices()

    def stop_app(self):
        self.async_runner.stop_loop()

    def _execute_process_task(self, task_id: str, target_func: Callable, *args, **kwargs):
        is_selenium_task = "doubao" in task_id
        if is_selenium_task:
            self.view.update_status("正在准备 ChromeDriver...")
            success, message = self.chromedriver_downloader.ensure_chromedriver()
            if not success:
                self.view.on_task_error(f"ChromeDriver 准备失败: {message}")
                return

            driver_path = os.path.join(self.view.config.PROJECT_ROOT, self.chromedriver_downloader.driver_filename)
            new_args = (driver_path, *args)
        else:
            new_args = args

        self.view.set_ui_enabled(False)
        self.worker = ProcessWorker(task_id, target_func, *new_args, **kwargs)
        self.worker.progress.connect(self.view.update_status)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.run()

    @pyqtSlot(str, str, object)
    def on_process_finished(self, task_id: str, status: str, result: Any):
        if status == 'success':
            if task_id == 'doubao_login':
                self.view.update_status("登录流程结束！您的登录信息已保存。", 5000)
                QMessageBox.information(self.view, "成功", "登录流程结束！您的登录信息已保存。")
            elif task_id.startswith('doubao_task_'):
                task_type = task_id.split('_')[-1]
                self.on_doubao_task_finished(task_type, result.get("text", ""))
            elif task_id == 'video_generation':
                self.on_video_finished(result)
        else:
            self.view.on_task_error(f"任务 '{task_id}' 失败: {result}")

        self.view.set_ui_enabled(True)
        self.worker = None

    @pyqtSlot()
    def on_login_clicked(self):
        if not self.view.selenium_available:
            QMessageBox.critical(self.view, "依赖缺失", "需要安装 Selenium 才能使用此功能。")
            return
        QMessageBox.information(self.view, "开始登录", "即将打开浏览器以登录「豆包」网站。\n\n请在打开的浏览器窗口中完成登录操作（如扫码）。\n\n登录成功后，请【手动关闭】该浏览器窗口以继续。您的登录状态会被保存。")
        self._execute_process_task('doubao_login', DoubaoProvider.login)

    @pyqtSlot(str)
    def on_doubao_action_clicked(self, task_type: str):
        if not self.view.selenium_available:
            QMessageBox.critical(self.view, "依赖缺失", "需要安装 Selenium 才能使用此功能。")
            return
        prompt_templates = {
            'extract': '1. 提取完整的视频文案，输出内容中禁止出现换行符和英文双引号，视频分享链接：【{link}】；\n\n2. 基于提取出的文案，严格按照以下JSON格式返回，禁止包含任何Markdown标记：{{"content": "这里是提取出的完整文案，禁止出现视频分享链接相关的信息", "cover_title": "这里是根据文案生成的4个字的封面主标题", "cover_subtitle": "这里是根据文案生成的10个字的封面副标题"}}\n\n3. 仅输出JSON内容。',
            'process': '1. 请对以下文案进行这项操作：“{instruction}”，输出内容中禁止出现换行符和英文双引号，原始文案是：【{text}】。\n\n2. 处理完成后，严格按照以下JSON格式返回，禁止包含任何Markdown标记：{{"content": "这里是处理后的文案", "cover_title": "这里是根据新文案生成的4个字的封面主标题", "cover_subtitle": "这里是根据新文案生成的10个字的封面副标题"}}\n\n3. 仅输出JSON内容。'
        }
        prompt = ""
        if task_type == 'extract':
            link = self.view.douyin_link_edit.text().strip()
            if not link: QMessageBox.warning(self.view, "警告", "请输入抖音视频分享链接！"); return
            prompt = prompt_templates['extract'].format(link=link)
            self.view.update_status("正在提取文案并生成标题...")
        else:
            text = self.view.text_edit.toPlainText().strip()
            if not text: QMessageBox.warning(self.view, "警告", "文本框内没有内容！"); return
            if task_type == 'original':
                instruction = "对文案进行深度去重和二创，使其更具原创性，风格保持不变"
                prompt = prompt_templates['process'].format(instruction=instruction, text=text)
                self.view.update_status("正在进行一键原创并生成新标题...")
            elif task_type == 'translate':
                lang_name = self.view.translate_lang_combo.currentText()
                if not lang_name: QMessageBox.warning(self.view, "警告", "请选择目标翻译语言！"); return
                instruction = f"将文案翻译成{lang_name}"
                prompt = prompt_templates['process'].format(instruction=instruction, text=text)
                self.view.update_status(f"正在翻译为 {lang_name} 并生成新标题...")
        if prompt: self._execute_process_task(f'doubao_task_{task_type}', DoubaoProvider.get_content, prompt_text=prompt)

    def on_doubao_task_finished(self, task_type: str, text: str):
        task_name_map = {'extract': '文案提取', 'original': '一键原创', 'translate': '一键翻译'}
        task_name = task_name_map.get(task_type, "操作")
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            self.view.text_edit.setText(text)
            QMessageBox.warning(self.view, "解析失败", f"{task_name}成功，但返回内容不是有效的JSON格式。\n\n原始结果已填充到文本框中，请检查。")
            self.view.update_status(f"{task_name}完成，但响应格式不正确。", 8000)
            return
        try:
            data = json.loads(json_match.group(0))
            self.view.text_edit.setText(data.get("content", ""))
            self.view.cover_title_edit.setText(data.get("cover_title", ""))
            self.view.cover_subtitle_edit.setText(data.get("cover_subtitle", ""))
            self.view.update_status(f"{task_name}成功！文案和标题已自动填充。", 5000)
            QMessageBox.information(self.view, "成功", f"{task_name}已成功，结果已自动填充到相应输入框。")
        except json.JSONDecodeError:
            self.view.text_edit.setText(text)
            QMessageBox.warning(self.view, "解析失败", f"{task_name}成功，但返回的JSON格式无效。\n\n原始结果已填充到文本框中，请检查。")
            self.view.update_status(f"{task_name}完成，但JSON解析失败。", 8000)

    @pyqtSlot()
    def on_generate_audio_clicked(self):
        params = self.view.get_tts_parameters()
        if not params: return
        try:
            os.makedirs(params['output_dir'], exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self.view, "错误", f"创建输出目录 '{params['output_dir']}' 失败:\n{e}")
            return
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        audio_path = os.path.abspath(os.path.join(params['output_dir'], f"audio_{timestamp}.mp3"))
        self.view.set_ui_enabled(False)
        self.tts_service.run_tts(params['text'], params['voice'], params['rate'], params['volume'], params['pitch'], params['generate_srt'], audio_path)

    @pyqtSlot(str, str)
    def on_tts_finished(self, audio_path: str, srt_path: str):
        self.view.last_audio_file = audio_path
        self.view.last_srt_file = srt_path
        self.view.audio_edit.setText(audio_path)
        if srt_path:
            self.view.srt_edit.setText(srt_path)
        self.view.update_audio_player_source()
        self.view.set_ui_enabled(True)
        output_directory = os.path.dirname(audio_path)
        msg = f"文件已成功保存到目录:\n{output_directory}\n\n音频: {os.path.basename(audio_path)}"
        if srt_path:
            msg += f"\n字幕: {os.path.basename(srt_path)}"
        self.view.update_status(f"生成完成！文件已保存到 '{os.path.basename(output_directory)}'。", 5000)
        QMessageBox.information(self.view, "生成成功", msg)

    @pyqtSlot()
    def on_generate_video_clicked(self):
        params = self.view.get_video_parameters()
        if not params: return
        self._execute_process_task('video_generation', VideoCreationService.run_generation_workflow, params=params)

    @pyqtSlot(str)
    def on_video_finished(self, video_path: str):
        self.view.last_video_file = video_path
        output_dir = os.path.dirname(video_path)
        msg = f"视频已成功生成！\n\n文件: {os.path.basename(video_path)}\n目录: {output_dir}"
        self.view.update_status("视频生成完成！", 5000)
        self.view.preview_video_button.setEnabled(True)
        QMessageBox.information(self.view, "生成成功", msg)