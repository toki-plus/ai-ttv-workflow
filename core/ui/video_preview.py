from typing import Optional

from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QDialog
)

from ..config import Config

class VideoPreviewDialog(QDialog):
    def __init__(self, video_path: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("视频预览")
        self.setStyleSheet(Config.STYLESHEET)
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)

        self.video_path = video_path
        self.main_window = parent

        self.player = QMediaPlayer(self, QMediaPlayer.VideoSurface)
        video_widget = QVideoWidget()

        self.play_button = QPushButton("播放")
        self.pause_button = QPushButton("暂停")
        self.pause_button.setEnabled(False)

        control_layout = QHBoxLayout()
        control_layout.addStretch()
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(video_widget)
        layout.addLayout(control_layout)

        self.player.setVideoOutput(video_widget)
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))

        self.play_button.clicked.connect(self.player.play)
        self.pause_button.clicked.connect(self.player.pause)
        self.player.stateChanged.connect(self.on_state_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)

    def on_state_changed(self, state):
        self.play_button.setEnabled(state != QMediaPlayer.PlayingState)
        self.pause_button.setEnabled(state == QMediaPlayer.PlayingState)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.InvalidMedia:
            self.player.stop()
            self.close()
            reply = QMessageBox.warning(
                self.main_window,
                "预览失败",
                "内置播放器无法加载视频文件。\n\n这通常是因为您的系统中缺少相应的视频解码器。\n\n是否尝试使用系统默认播放器打开该视频？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes and hasattr(self.main_window, '_open_file_in_system'):
                self.main_window._open_file_in_system(self.video_path)

    def closeEvent(self, event):
        self.player.stop()
        super().closeEvent(event)