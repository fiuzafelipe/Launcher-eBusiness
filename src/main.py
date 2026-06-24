import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

# A MÁGICA DEFINITIVA: Usar o User-Agent do Firefox!
# Isso impede que o Google procure por APIs exclusivas do Chrome e nos bloqueie.
global_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0"

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-blink-features=AutomationControlled "
    f"--user-agent=\"{global_ua}\""
)

# Caminhos do sistema
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

PROJECT_ROOT = os.path.dirname(current_dir)
os.environ["PROJECT_ROOT"] = PROJECT_ROOT 

def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("FiuzaStandaloneHub")
    app.setOrganizationName("FiuzaTechnology")
    
    from ui.main_window import StandaloneHub
    window = StandaloneHub()
    window.show() 
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()