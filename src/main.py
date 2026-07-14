import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

current_dir = os.path.dirname(os.path.abspath(__file__))

if current_dir not in sys.path:
    sys.path.append(current_dir)

PROJECT_ROOT = os.path.dirname(current_dir)

os.environ["PROJECT_ROOT"] = PROJECT_ROOT

def main():

    QApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts
    )

    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--disable-popup-blocking "
        "--enable-features=NetworkServiceInProcess "
        "--enable-gpu " 
        "--ignore-gpu-blocklist "
        "--enable-media-stream" 
    )

    app = QApplication(sys.argv)

    app.setApplicationName(
        "Fiuza Standalone Hub v1.0"
    )

    app.setOrganizationName(
        "FiuzaTechnology"
    )

    from ui.main_window import StandaloneHub

    window = StandaloneHub()

    window.show()

    sys.exit(
        app.exec()
    )

if __name__ == "__main__":
    main()