import os

class Config:
    APP_NAME = "颜趣AI视频创作工作流"

    PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(PACKAGE_DIR)

    ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
    IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
    FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
    MUSICS_DIR = os.path.join(ASSETS_DIR, "musics")
    OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
    DOUBAO_USER_DATA_DIR = os.path.join(PROJECT_ROOT, "doubao_user_data")

    VOICES_CACHE_FILE = os.path.join(PROJECT_ROOT, "voices.json")
    CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")
    TRANSLATE_FILE = os.path.join(PROJECT_ROOT, "translate.json")

    DEFAULT_AVATAR_PATH = os.path.join(IMAGES_DIR, "avatar.png")
    DEFAULT_FONT_PATH = os.path.join(FONTS_DIR, "Alimama DongFangDaKai.ttf")
    DEFAULT_BGM_PATH = os.path.join(MUSICS_DIR, "bgm.mp3")

    STYLESHEET = """
    QWidget {
        background-color: #1A1D2A;
        color: #D0D0D0;
        font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
        font-size: 10pt;
    }
    QGroupBox {
        background-color: #24283B;
        border: 1px solid #25F4EE;
        border-radius: 8px;
        margin-top: 1em;
    }
    QGroupBox::title {
        color: #25F4EE;
        font-weight: bold;
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 10px;
        background-color: #24283B;
        border-radius: 4px;
    }
    QLabel {
        color: #E0E0E0;
        background-color: transparent;
    }
    QLabel#rate_label, QLabel#volume_label, QLabel#pitch_label {
        color: #25F4EE;
        font-weight: bold;
    }
    QPushButton {
        background-color: #3B3F51;
        color: #FFFFFF;
        border: 1px solid #25F4EE;
        border-radius: 5px;
        padding: 8px 16px;
        font-weight: bold;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #FE2C55;
        border-color: #FE2C55;
    }
    QPushButton:pressed {
        background-color: #D92349;
    }
    QPushButton:disabled {
        background-color: #4A4E60;
        color: #888888;
        border-color: #555555;
    }
    QPushButton#generate_button, QPushButton#generate_video_button, QPushButton#PrimaryButton {
        background-color: #FE2C55;
        border-color: #FE2C55;
    }
    QPushButton#generate_button:hover, QPushButton#generate_video_button:hover, QPushButton#PrimaryButton:hover {
        background-color: #FF4D71;
    }
    QPushButton#generate_button:pressed, QPushButton#generate_video_button:pressed, QPushButton#PrimaryButton:pressed {
        background-color: #D92349;
    }
    QTextEdit, QLineEdit {
        background-color: #1A1D2A;
        color: #FFFFFF;
        border: 1px solid #4A4E60;
        border-radius: 5px;
        padding: 5px;
    }
    QTextEdit:focus, QLineEdit:focus {
        border: 1px solid #25F4EE;
    }
    QTextEdit::placeholder, QLineEdit::placeholder {
        color: #707070;
    }
    QComboBox {
        background-color: #3B3F51;
        border: 1px solid #25F4EE;
        border-radius: 5px;
        padding: 5px;
        min-width: 6em;
    }
    QComboBox:on {
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left-width: 1px;
        border-left-color: #25F4EE;
        border-left-style: solid;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }
    QComboBox QAbstractItemView {
        background-color: #1A1D2A;
        border: 1px solid #25F4EE;
        border-radius: 5px;
        color: #D0D0D0;
        selection-background-color: #FE2C55;
        selection-color: #FFFFFF;
    }
    QSlider::groove:horizontal {
        border: 1px solid #3B3F51;
        height: 4px;
        background: #3B3F51;
        margin: 2px 0;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #25F4EE;
        border: 1px solid #25F4EE;
        width: 16px;
        height: 16px;
        margin: -8px 0;
        border-radius: 8px;
    }
    QSlider::handle:horizontal:hover {
        background: #97FEFA;
        border: 1px solid #97FEFA;
    }
    QCheckBox {
        spacing: 5px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 2px solid #25F4EE;
        border-radius: 3px;
        background-color: transparent;
    }
    QCheckBox::indicator:hover {
        border-color: #97FEFA;
    }
    QCheckBox::indicator:checked {
        background-color: #FE2C55;
        border-color: #FE2C55;
    }
    QStatusBar {
        background-color: #1A1D2A;
        border-top: 1px solid #25F4EE;
    }
    QStatusBar::item {
        border: none;
    }
    QScrollBar:vertical, QScrollBar:horizontal {
        border: none;
        background-color: #24283B;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
        background-color: #4A4E60;
        border-radius: 5px;
        min-height: 20px;
        min-width: 20px;
    }
    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
        background-color: #25F4EE;
    }
    QScrollBar::add-line, QScrollBar::sub-line {
        border: none;
        background: none;
        height: 0;
        width: 0;
    }
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
        background: none;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
    QMenuBar {
        background-color: #1A1D2A;
        border-bottom: 1px solid #25F4EE;
        spacing: 10px;
    }
    QMenuBar::item {
        background-color: transparent;
        color: #D0D0D0;
        padding: 6px 12px;
        border-radius: 5px;
    }
    QMenuBar::item:selected, QMenuBar::item:hover {
        background-color: #3B3F51;
        color: #FFFFFF;
    }
    QMenu {
        background-color: #24283B;
        border: 1px solid #4A4E60;
        border-radius: 5px;
        padding: 5px;
    }
    QMenu::item {
        color: #D0D0D0;
        padding: 8px 25px;
        margin: 2px 0;
        border-radius: 4px;
        border: 1px solid transparent;
    }
    QMenu::item:selected {
        background-color: #FE2C55;
        color: #FFFFFF;
    }
    QMenu::item:disabled {
        color: #707070;
        background-color: transparent;
    }
    QMenu::separator {
        height: 1px;
        background-color: #4A4E60;
        margin: 5px 0px;
    }
    QMessageBox {
        background-color: #24283B;
    }
    QMessageBox QLabel {
        color: #FFFFFF;
        background-color: transparent;
    }

    """
