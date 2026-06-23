import sys
import os
from PyQt6.QtWidgets import QApplication

# 1. Isso garante que o Python reconheça a pasta 'src' como a raiz do projeto.
# Evita problemas de "ModuleNotFoundError" ao importar arquivos de outras pastas.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 2. Agora puxamos a sua janela principal direto da pasta UI
from ui.main_window import StandaloneHub

def main():
    # Inicializa o motor do aplicativo
    app = QApplication(sys.argv)
    
    # Cria e exibe o seu Hub
    window = StandaloneHub()
    
    # Trava o programa rodando até você fechá-lo no 'X'
    sys.exit(app.exec())

if __name__ == "__main__":
    main()