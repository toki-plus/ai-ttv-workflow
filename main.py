import sys
import multiprocessing
from PyQt5.QtWidgets import QApplication
from core.ui.main_window import VideoWorkflowApp
from core.config import Config

def main():
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    app.setStyleSheet(Config.STYLESHEET)
    window = VideoWorkflowApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()