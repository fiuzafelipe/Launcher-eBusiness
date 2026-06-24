import sys
import os

# Configuração global do ambiente do Chromium (antes de qualquer import do PyQt6)
global_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-blink-features=AutomationControlled "
    f"--user-agent=\"{global_ua}\" "
)

from PyQt6.QtWidgets import QApplication

# Garante que o Python encontre o diretório 'src' independentemente de onde o script é chamado
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Define a raiz do projeto (uma pasta acima de src/) para ajudar na busca de assets posteriormente
PROJECT_ROOT = os.path.dirname(current_dir)
os.environ["PROJECT_ROOT"] = PROJECT_ROOT 

from ui.main_window import StandaloneHub

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FiuzaStandaloneHub")
    app.setOrganizationName("FiuzaTechnology")
    
    # Instancia a janela principal
    window = StandaloneHub()
    
    # Exibe a janela de forma explícita (ajuste se preferir showMaximized() ou showFullScreen())
    window.show() 
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()