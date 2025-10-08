import os
import shutil
import platform
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional

from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl, pyqtSlot
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QComboBox, QLabel, QSlider, QCheckBox,
    QFileDialog, QStatusBar, QGroupBox, QFormLayout, QMessageBox,
    QLineEdit
)
from PIL import Image

try:
    from selenium import webdriver
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from ..config import Config
from ..utils.data_manager import DataManager
from ..app_controller import AppController
from .video_preview import VideoPreviewDialog
from .custom_widgets import PlainTextEdit

class VideoWorkflowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.voices: List[Dict] = []
        self.translations: Dict[str, str] = {}
        self.last_audio_file: Optional[str] = None
        self.last_srt_file: Optional[str] = None
        self.last_video_file: Optional[str] = None
        self.config: Dict = {}
        self.player = QMediaPlayer()

        self.controller = AppController(self)

        self.ffmpeg_available = shutil.which('ffmpeg') is not None
        self.selenium_available = SELENIUM_AVAILABLE

        self._init_window()
        self._ensure_assets_dirs()
        self._init_ui()
        self._load_and_apply_config()
        self._connect_signals()
        self.controller.start_app()

    def _init_window(self):
        self.setWindowTitle(f"{Config.APP_NAME}")
        self.setGeometry(500, 250, 950, 900)

    def _ensure_assets_dirs(self):
        for path in [Config.IMAGES_DIR, Config.FONTS_DIR, Config.MUSICS_DIR, Config.OUTPUT_DIR]:
            os.makedirs(path, exist_ok=True)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        top_half_layout = QHBoxLayout()
        left_col_layout = QVBoxLayout()

        extract_group = QGroupBox("1. 提取抖音视频文案（可选）")
        extract_layout = QFormLayout()
        extract_layout.setContentsMargins(15, 25, 15, 15)
        extract_layout.setSpacing(10)
        self.douyin_link_edit = QLineEdit()
        self.douyin_link_edit.setPlaceholderText("在此处粘贴抖音视频分享链接...")
        self.login_button = QPushButton("登录豆包")
        self.extract_button = QPushButton("提取文案")
        link_btn_layout = QHBoxLayout()
        link_btn_layout.setContentsMargins(0, 0, 0, 0)
        link_btn_layout.setSpacing(10)
        link_btn_layout.addWidget(self.douyin_link_edit)
        link_btn_layout.addWidget(self.login_button)
        link_btn_layout.addWidget(self.extract_button)
        extract_layout.addRow("视频分享链接:", link_btn_layout)
        extract_group.setLayout(extract_layout)
        left_col_layout.addWidget(extract_group)

        input_group = QGroupBox("2. 输入文本")
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(15, 25, 15, 15)
        input_layout.setSpacing(10)
        self.text_edit = PlainTextEdit()
        self.text_edit.setPlaceholderText("提取出的文案将显示在这里，您也可以手动输入或编辑...")
        text_buttons_layout = QHBoxLayout()
        self.original_button = QPushButton("一键原创")
        self.translate_button = QPushButton("一键翻译")
        self.translate_lang_combo = QComboBox()
        self.load_file_button = QPushButton("从文件加载...")
        text_buttons_layout.addWidget(self.original_button)
        text_buttons_layout.addWidget(self.translate_button)
        text_buttons_layout.addWidget(self.translate_lang_combo, 1)
        text_buttons_layout.addStretch()
        text_buttons_layout.addWidget(self.load_file_button)
        input_layout.addWidget(self.text_edit)
        input_layout.addLayout(text_buttons_layout)
        input_group.setLayout(input_layout)
        left_col_layout.addWidget(input_group)

        top_half_layout.addLayout(left_col_layout, 2)

        right_col_layout = QVBoxLayout()
        voice_group = QGroupBox("3. 选择语音")
        voice_layout = QFormLayout()
        voice_layout.setContentsMargins(15, 25, 15, 15)
        voice_layout.setSpacing(10)
        self.lang_combo = QComboBox()
        self.gender_combo = QComboBox()
        self.voice_combo = QComboBox()
        self.voice_combo.setEnabled(False)
        voice_layout.addRow("语言:", self.lang_combo)
        voice_layout.addRow("性别:", self.gender_combo)
        voice_layout.addRow("语音:", self.voice_combo)
        voice_group.setLayout(voice_layout)
        right_col_layout.addWidget(voice_group)

        controls_group = QGroupBox("4. 调整参数")
        controls_layout = QFormLayout()
        controls_layout.setContentsMargins(15, 25, 15, 15)
        controls_layout.setSpacing(10)
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(-100, 100)
        self.rate_label = QLabel("+0%")
        self.rate_label.setObjectName("rate_label")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(-100, 100)
        self.volume_label = QLabel("+0%")
        self.volume_label.setObjectName("volume_label")
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setRange(-50, 50)
        self.pitch_label = QLabel("+0Hz")
        self.pitch_label.setObjectName("pitch_label")
        controls_layout.addRow("语速:", self._create_slider_box(self.rate_slider, self.rate_label))
        controls_layout.addRow("音量:", self._create_slider_box(self.volume_slider, self.volume_label))
        controls_layout.addRow("音调:", self._create_slider_box(self.pitch_slider, self.pitch_label))
        controls_group.setLayout(controls_layout)
        right_col_layout.addWidget(controls_group)
        right_col_layout.addStretch()

        top_half_layout.addLayout(right_col_layout, 1)
        main_layout.addLayout(top_half_layout)

        output_group = QGroupBox("5. 输出设置")
        output_layout = QHBoxLayout()
        output_layout.setContentsMargins(15, 25, 15, 15)
        output_layout.setSpacing(10)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择或输入音视频文件保存目录...")
        self.select_dir_button = QPushButton("选择目录")
        self.open_dir_button = QPushButton("打开目录")
        output_layout.addWidget(QLabel("保存路径:"))
        output_layout.addWidget(self.output_path_edit, 1)
        output_layout.addWidget(self.select_dir_button)
        output_layout.addWidget(self.open_dir_button)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        action_group = QGroupBox("6. 生成音频")
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(15, 15, 15, 15)
        self.srt_checkbox = QCheckBox("生成字幕(.srt)")
        self.generate_button = QPushButton("生成音频")
        self.generate_button.setObjectName("generate_button")
        self.generate_button.setEnabled(False)
        self.playback_button = QPushButton("播放")
        self.playback_button.setEnabled(False)
        self.pause_button = QPushButton("暂停播放")
        self.pause_button.setEnabled(False)
        action_layout.addWidget(self.srt_checkbox)
        action_layout.addStretch()
        action_layout.addWidget(self.generate_button)
        action_layout.addWidget(self.playback_button)
        action_layout.addWidget(self.pause_button)
        action_group.setLayout(action_layout)
        main_layout.addWidget(action_group)

        self.video_group = QGroupBox("7. 生成视频")
        video_main_layout = QVBoxLayout()
        video_main_layout.setContentsMargins(15, 25, 15, 15)
        video_main_layout.setSpacing(10)
        params_grid = QGridLayout()
        params_grid.setSpacing(10)
        params_grid.setColumnStretch(1, 1)
        params_grid.setColumnStretch(3, 1)

        self.avatar_edit = QLineEdit()
        self.avatar_edit.setPlaceholderText("请选择或拖入头像图片文件")
        self.avatar_button = QPushButton("选择图片")
        params_grid.addWidget(QLabel("头像图片:"), 0, 0, Qt.AlignRight)
        params_grid.addLayout(self._create_file_input_layout(self.avatar_edit, self.avatar_button), 0, 1, 1, 3)

        self.font_edit = QLineEdit()
        self.font_edit.setPlaceholderText("请选择或拖入字幕字体文件 (.ttf, .otf)")
        self.font_button = QPushButton("选择字体")
        params_grid.addWidget(QLabel("显示字体:"), 1, 0, Qt.AlignRight)
        params_grid.addLayout(self._create_file_input_layout(self.font_edit, self.font_button), 1, 1, 1, 3)

        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("例如：@颜趣空间")
        self.cover_title_edit = QLineEdit()
        self.cover_title_edit.setPlaceholderText("例如：顶级思维")
        params_grid.addWidget(QLabel("作者名称:"), 2, 0, Qt.AlignRight)
        params_grid.addWidget(self.author_edit, 2, 1)
        params_grid.addWidget(QLabel("封面标题:"), 2, 2, Qt.AlignRight)
        params_grid.addWidget(self.cover_title_edit, 2, 3)

        self.subtext_edit = QLineEdit()
        self.subtext_edit.setPlaceholderText("例如：主观分享，仅供参考")
        self.cover_subtitle_edit = QLineEdit()
        self.cover_subtitle_edit.setPlaceholderText("例如：建立体系让你脱胎换骨")
        params_grid.addWidget(QLabel("右上角文字:"), 3, 0, Qt.AlignRight)
        params_grid.addWidget(self.subtext_edit, 3, 1)
        params_grid.addWidget(QLabel("封面副标题:"), 3, 2, Qt.AlignRight)
        params_grid.addWidget(self.cover_subtitle_edit, 3, 3)

        self.audio_edit = QLineEdit()
        self.audio_edit.setPlaceholderText("生成音频后将自动填充，也可手动选择")
        self.audio_button = QPushButton("选择音频")
        params_grid.addWidget(QLabel("音频文件:"), 4, 0, Qt.AlignRight)
        params_grid.addLayout(self._create_file_input_layout(self.audio_edit, self.audio_button), 4, 1, 1, 3)

        self.srt_edit = QLineEdit()
        self.srt_edit.setPlaceholderText("生成字幕后将自动填充，也可手动选择")
        self.srt_button = QPushButton("选择字幕")
        params_grid.addWidget(QLabel("字幕文件:"), 5, 0, Qt.AlignRight)
        params_grid.addLayout(self._create_file_input_layout(self.srt_edit, self.srt_button), 5, 1, 1, 3)

        self.bgm_edit = QLineEdit()
        self.bgm_edit.setPlaceholderText("可选项，选择一个背景音乐文件")
        self.bgm_button = QPushButton("选择BGM")
        params_grid.addWidget(QLabel("背景音乐:"), 6, 0, Qt.AlignRight)
        params_grid.addLayout(self._create_file_input_layout(self.bgm_edit, self.bgm_button), 6, 1, 1, 3)

        video_action_layout = QHBoxLayout()
        self.gpu_checkbox = QCheckBox("开启GPU加速")
        self.gpu_checkbox.setToolTip("需要正确安装NVIDIA驱动和支持NVENC的FFmpeg版本")
        self.generate_video_button = QPushButton("生成视频")
        self.generate_video_button.setObjectName("generate_video_button")
        self.preview_video_button = QPushButton("预览视频")
        self.preview_video_button.setEnabled(False)
        video_action_layout.addWidget(self.gpu_checkbox)
        video_action_layout.addStretch()
        video_action_layout.addWidget(self.generate_video_button)
        video_action_layout.addWidget(self.preview_video_button)

        video_main_layout.addLayout(params_grid)
        video_main_layout.addLayout(video_action_layout)
        self.video_group.setLayout(video_main_layout)

        main_layout.addWidget(self.video_group, 1)
        main_layout.addStretch()

        if not self.ffmpeg_available:
            self.video_group.setEnabled(False)
            self.video_group.setTitle("7. 生成视频 (FFmpeg未找到)")
        if not self.selenium_available:
            extract_group.setEnabled(False)
            extract_group.setTitle("1. 提取文案 (Selenium未安装)")
            self.original_button.setEnabled(False)
            self.translate_button.setEnabled(False)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _connect_signals(self):
        self.login_button.clicked.connect(self.controller.on_login_clicked)
        self.extract_button.clicked.connect(lambda: self.controller.on_doubao_action_clicked('extract'))
        self.original_button.clicked.connect(lambda: self.controller.on_doubao_action_clicked('original'))
        self.translate_button.clicked.connect(lambda: self.controller.on_doubao_action_clicked('translate'))
        self.load_file_button.clicked.connect(self.load_text_from_file)

        self.lang_combo.currentIndexChanged.connect(self._filter_voices)
        self.gender_combo.currentIndexChanged.connect(self._filter_voices)

        self.rate_slider.valueChanged.connect(lambda v: self.rate_label.setText(f"{v:+}%"))
        self.volume_slider.valueChanged.connect(lambda v: self.volume_label.setText(f"{v:+}%"))
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(f"{v:+}Hz"))

        self.select_dir_button.clicked.connect(self.select_output_directory)
        self.open_dir_button.clicked.connect(self.open_output_directory)

        self.generate_button.clicked.connect(self.controller.on_generate_audio_clicked)
        self.playback_button.clicked.connect(self.play_last_audio)
        self.pause_button.clicked.connect(self.pause_audio)
        self.player.stateChanged.connect(self.on_player_state_changed)

        self.avatar_button.clicked.connect(lambda: self.select_asset_file('avatar'))
        self.font_button.clicked.connect(lambda: self.select_asset_file('font'))
        self.audio_button.clicked.connect(lambda: self.select_external_file('audio'))
        self.srt_button.clicked.connect(lambda: self.select_external_file('srt'))
        self.bgm_button.clicked.connect(lambda: self.select_external_file('bgm'))

        self.generate_video_button.clicked.connect(self.controller.on_generate_video_clicked)
        self.preview_video_button.clicked.connect(self.show_video_preview)

    def _create_slider_box(self, slider: QSlider, label: QLabel) -> QWidget:
        box = QWidget()
        layout = QHBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(slider)
        layout.addWidget(label)
        return box

    def _create_file_input_layout(self, line_edit: QLineEdit, button: QPushButton) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        return layout

    def _load_and_apply_config(self):
        self.config = DataManager.load_json(Config.CONFIG_FILE) or {}
        self.update_status("已加载上次的配置。" if self.config else "未找到配置文件，将使用默认设置。", 3000)
        self.rate_slider.setValue(self.config.get("rate", 0))
        self.volume_slider.setValue(self.config.get("volume", 0))
        self.pitch_slider.setValue(self.config.get("pitch", 0))
        self.srt_checkbox.setChecked(self.config.get("generate_srt", True))
        self.output_path_edit.setText(self.config.get("output_path", Config.OUTPUT_DIR))
        self.avatar_edit.setText(os.path.abspath(self.config.get("avatar_path", Config.DEFAULT_AVATAR_PATH)))
        self.font_edit.setText(os.path.abspath(self.config.get("font_path", Config.DEFAULT_FONT_PATH)))

        if not os.path.exists(self.avatar_edit.text()) and "avatar.png" in self.avatar_edit.text():
            try:
                Image.new('RGB', (100, 100), 'gray').save(self.avatar_edit.text())
            except Exception as e:
                print(f"创建默认头像失败: {e}")

        self.author_edit.setText(self.config.get("author_name", "@颜趣空间"))
        self.subtext_edit.setText(self.config.get("sub_text", "主观分享，仅供参考"))
        self.cover_title_edit.setText(self.config.get("cover_title", "顶级思维"))
        self.cover_subtitle_edit.setText(self.config.get("cover_subtitle", "建立体系让你脱胎换骨"))
        bgm_path = self.config.get("bgm_path", Config.DEFAULT_BGM_PATH if os.path.exists(Config.DEFAULT_BGM_PATH) else "")
        self.bgm_edit.setText(os.path.abspath(bgm_path) if bgm_path else "")
        self.gpu_checkbox.setChecked(self.config.get("use_gpu", False))

    def _save_config(self):
        config_data = {
            "language": self.lang_combo.currentData(), "gender": self.gender_combo.currentData(), "voice": self.voice_combo.currentData(),
            "rate": self.rate_slider.value(), "volume": self.volume_slider.value(), "pitch": self.pitch_slider.value(),
            "generate_srt": self.srt_checkbox.isChecked(), "output_path": self.output_path_edit.text(),
            "avatar_path": self.avatar_edit.text(), "font_path": self.font_edit.text(), "author_name": self.author_edit.text(),
            "sub_text": self.subtext_edit.text(), "cover_title": self.cover_title_edit.text(), "cover_subtitle": self.cover_subtitle_edit.text(),
            "bgm_path": self.bgm_edit.text(), "use_gpu": self.gpu_checkbox.isChecked(),
        }
        if not DataManager.save_json(config_data, Config.CONFIG_FILE):
            self.update_status("保存配置失败", 5000)

    def set_ui_enabled(self, enabled: bool):
        self.generate_button.setEnabled(enabled and self.voice_combo.count() > 0)
        self.generate_video_button.setEnabled(enabled and self.ffmpeg_available)
        self.preview_video_button.setEnabled(enabled and self.last_video_file is not None)

        if self.selenium_available:
            self.login_button.setEnabled(enabled)
            self.extract_button.setEnabled(enabled)
            self.original_button.setEnabled(enabled)
            self.translate_button.setEnabled(enabled)

        if not enabled:
            self.playback_button.setEnabled(False)
            self.pause_button.setEnabled(False)
        else:
            self.on_player_state_changed(self.player.state())

    @pyqtSlot(list)
    def on_voices_loaded(self, voices: List[Dict]):
        self.voices = sorted(voices, key=lambda v: v['ShortName'])
        self._create_and_load_translation_map()

        self.lang_combo.clear()
        self.gender_combo.clear()
        self.translate_lang_combo.clear()

        all_langs = sorted(list(set(v['Locale'].split('-')[0] for v in self.voices)))
        all_genders = sorted(list(set(v['Gender'] for v in self.voices)))

        self.lang_combo.addItem(self.translations.get("all", "全部"), "all")
        for lang_code in all_langs:
            self.lang_combo.addItem(self.translations.get(lang_code, lang_code), lang_code)
            self.translate_lang_combo.addItem(self.translations.get(lang_code, lang_code), lang_code)

        self.gender_combo.addItem(self.translations.get("all", "全部"), "all")
        for gender_key in all_genders:
            self.gender_combo.addItem(self.translations.get(gender_key, gender_key), gender_key)

        self.voice_combo.setEnabled(True)
        self.generate_button.setEnabled(True)
        self.update_status("语音列表加载完成。", 5000)
        self._apply_voice_config()

    @pyqtSlot(str)
    def on_task_error(self, error_msg: str):
        self.set_ui_enabled(True)
        self.update_status(f"错误: {error_msg}", 10000)
        QMessageBox.critical(self, "错误", str(error_msg))

    def get_tts_parameters(self) -> Optional[Dict]:
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入文本！")
            return None

        voice = self.voice_combo.currentData()
        if not voice:
            QMessageBox.warning(self, "警告", "请选择一个语音！")
            return None

        output_dir = self.output_path_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择或输入一个有效的保存目录！")
            return None

        return {
            "text": text, "voice": voice, "output_dir": output_dir,
            "rate": f"{self.rate_slider.value():+}%", "volume": f"{self.volume_slider.value():+}%",
            "pitch": f"{self.pitch_slider.value():+}Hz", "generate_srt": self.srt_checkbox.isChecked()
        }

    def get_video_parameters(self) -> Optional[Dict]:
        params = {
            'avatar': self.avatar_edit.text(), 'font': self.font_edit.text(), 'audio': self.audio_edit.text(),
            'srt': self.srt_edit.text(), 'author': self.author_edit.text(), 'subtext': self.subtext_edit.text(),
            'cover_title': self.cover_title_edit.text(), 'cover_subtitle': self.cover_subtitle_edit.text(),
            'bgm': self.bgm_edit.text(), 'use_gpu': self.gpu_checkbox.isChecked()
        }

        required_fields = ['avatar', 'font', 'audio', 'srt']
        for key, value in params.items():
            if key in required_fields and not value:
                QMessageBox.warning(self, "参数缺失", f"请为视频生成提供 '{key}' 的有效值！")
                return None
            if key in required_fields and not os.path.exists(value):
                QMessageBox.warning(self, "文件不存在", f"视频生成所需文件不存在：\n'{value}'")
                return None

        output_dir = self.output_path_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择或输入一个有效的保存目录！")
            return None

        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "错误", f"创建输出目录 '{output_dir}' 失败:\n{e}")
            return None

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        params['video_output'] = os.path.abspath(os.path.join(output_dir, f"video_{timestamp}.mp4"))
        return params

    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择保存目录", self.output_path_edit.text() or Config.PROJECT_ROOT)
        if directory:
            self.output_path_edit.setText(directory)
            self.update_status(f"保存路径已更新为: {directory}", 3000)

    def open_output_directory(self):
        self._open_file_in_system(self.output_path_edit.text().strip())

    def select_asset_file(self, asset_type: str):
        lookup = {
            'avatar': ("选择头像图片", "图片文件 (*.png *.jpg *.jpeg)", self.avatar_edit),
            'font': ("选择字体文件", "字体文件 (*.ttf *.otf)", self.font_edit)
        }
        title, file_filter, line_edit = lookup[asset_type]
        start_dir = Config.ASSETS_DIR
        current_path = line_edit.text()
        if current_path:
            potential_dir = os.path.dirname(current_path)
            if os.path.isdir(potential_dir):
                start_dir = potential_dir

        file_path, _ = QFileDialog.getOpenFileName(self, title, start_dir, file_filter)
        if file_path:
            abs_path = os.path.abspath(file_path)
            line_edit.setText(abs_path)
            asset_name = title.replace("选择", "")
            self.update_status(f"已选择新的{asset_name}文件。", 3000)

    def select_external_file(self, file_type: str):
        lookup = {
            'audio': ("选择音频文件", "音频文件 (*.mp3 *.wav *.m4a)", self.audio_edit),
            'srt': ("选择字幕文件", "字幕文件 (*.srt)", self.srt_edit),
            'bgm': ("选择背景音乐", "音频文件 (*.mp3 *.wav *.m4a)", self.bgm_edit)
        }
        if file_type not in lookup: return
        title, file_filter, line_edit = lookup[file_type]
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if file_path:
            line_edit.setText(file_path)

    def update_audio_player_source(self):
        if self.last_audio_file:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.last_audio_file)))

    def play_last_audio(self):
        if self.last_audio_file and self.player.state() != QMediaPlayer.PlayingState:
            self.player.play()

    def pause_audio(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()

    def on_player_state_changed(self, state: QMediaPlayer.State):
        is_playing = state == QMediaPlayer.PlayingState
        self.playback_button.setEnabled(not is_playing and self.last_audio_file is not None)
        self.pause_button.setEnabled(is_playing)

    def _open_file_in_system(self, path: str):
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "路径无效", f"路径 '{path}' 不存在或无效。")
            return
        try:
            real_path = os.path.realpath(path)
            if platform.system() == "Windows":
                os.startfile(real_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", real_path])
            else:
                subprocess.run(["xdg-open", real_path])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开路径 '{path}':\n{e}")

    def show_video_preview(self):
        if self.last_video_file and os.path.exists(self.last_video_file):
            VideoPreviewDialog(self.last_video_file, self).exec_()
        else:
            QMessageBox.warning(self, "无法预览", "未找到可预览的视频文件。请先生成一个视频。")

    def _filter_voices(self):
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        selected_lang, selected_gender = self.lang_combo.currentData(), self.gender_combo.currentData()

        filtered = [
            v for v in self.voices
            if (selected_lang == "all" or v['Locale'].startswith(selected_lang)) and
               (selected_gender == "all" or v['Gender'] == selected_gender)
        ]

        for voice in filtered:
            gender_cn = self.translations.get(voice['Gender'], voice['Gender'])
            self.voice_combo.addItem(f"{voice['ShortName']} ({gender_cn}, {voice['Locale']})", voice['ShortName'])

        self.voice_combo.blockSignals(False)

    def _apply_voice_config(self):
        for combo, key in [(self.lang_combo, "language"), (self.gender_combo, "gender")]:
            combo.blockSignals(True)
            value_to_set = self.config.get(key, "all")
            index = combo.findData(value_to_set)
            if index > -1:
                combo.setCurrentIndex(index)
            combo.blockSignals(False)

        self._filter_voices()

        voice_to_set = self.config.get("voice")
        if voice_to_set:
            index = self.voice_combo.findData(voice_to_set)
            if index > -1:
                self.voice_combo.setCurrentIndex(index)

    def load_text_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "从文件加载文本", "", "文本文件 (*.txt);;所有文件 (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.text_edit.setText(f.read())
                self.update_status(f"已从 {os.path.basename(file_path)} 加载文本", 5000)
            except Exception as e:
                self.on_task_error(f"无法读取文件: {e}")

    @pyqtSlot(str)
    def update_status(self, message: str, timeout: int = 0):
        self.status_bar.showMessage(message, timeout)

    def _create_and_load_translation_map(self):
        translations = DataManager.load_json(Config.TRANSLATE_FILE)
        if translations:
            self.translations = translations
            return

        lang_map = { "af": "南非荷兰语", "sq": "阿尔巴尼亚语", "am": "阿姆哈拉语", "ar": "阿拉伯语", "az": "阿塞拜疆语", "bn": "孟加拉语", "bs": "波斯尼亚语", "bg": "保加利亚语", "my": "缅甸语", "ca": "加泰罗尼亚语", "zh": "中文", "hr": "克罗地亚语", "cs": "捷克语", "da": "丹麦语", "nl": "荷兰语", "en": "英语", "et": "爱沙尼亚语", "fil": "菲律宾语", "fi": "芬兰语", "fr": "法语", "gl": "加利西亚语", "ka": "格鲁地亚语", "de": "德语", "el": "希腊语", "gu": "古吉拉特语", "he": "希伯来语", "hi": "印地语", "hu": "匈牙利语", "is": "冰岛语", "id": "印度尼西亚语", "iu": "因纽特语", "ga": "爱尔兰语", "it": "意大利语", "ja": "日语", "jv": "爪哇语", "kn": "卡纳达语", "kk": "哈萨克语", "km": "高棉语", "ko": "韩语", "lo": "老挝语", "lv": "拉脱维亚语", "lt": "立陶宛语", "mk": "马其顿语", "ms": "马来语", "ml": "马拉雅拉姆语", "mt": "马耳他语", "mr": "马拉地语", "mn": "蒙古语", "ne": "尼泊尔语", "nb": "挪威语", "ps": "普什图语", "fa": "波斯语", "pl": "波兰语", "pt": "葡萄牙语", "ro": "罗马尼亚语", "ru": "俄语", "sr": "塞尔维亚语", "si": "僧伽罗语", "sk": "斯洛伐克语", "sl": "斯洛文尼亚语", "so": "索马里语", "es": "西班牙语", "su": "巽他语", "sw": "斯瓦希里语", "sv": "瑞典语", "ta": "泰米尔语", "te": "泰卢固语", "th": "泰语", "tr": "土耳其语", "uk": "乌克兰语", "ur": "乌尔都语", "uz": "乌兹别克语", "vi": "越南语", "cy": "威尔士语", "zu": "祖鲁语" }
        self.translations = {"all": "全部", "Male": "男", "Female": "女", **lang_map}
        DataManager.save_json(self.translations, Config.TRANSLATE_FILE)

    def closeEvent(self, event):
        self._save_config()
        self.controller.stop_app()
        self.player.stop()

        super().closeEvent(event)
