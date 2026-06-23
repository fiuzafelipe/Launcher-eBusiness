import sys
import os

# A MÁGICA DEFINITIVA NO NÚCLEO DO SISTEMA
# Injetando o User-Agent globalmente via variável de ambiente, nós garantimos que 
# até os Service Workers de segundo plano do Google usem a identidade correta,
# eliminando completamente o bug do re-login!
global_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-blink-features=AutomationControlled "
    f"--user-agent=\"{global_ua}\" "
)

from PyQt6.QtWidgets import QApplication

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from ui.main_window import StandaloneHub

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FiuzaStandaloneHub")
    app.setOrganizationName("FiuzaTechnology")
    
    window = StandaloneHub()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()