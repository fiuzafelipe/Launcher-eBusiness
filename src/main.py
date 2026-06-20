import os
import sys

# ----------------------------------------------------------------------
# CORREÇÃO DEFINITIVA DE CAMINHO (sys.path)
# ----------------------------------------------------------------------
# Descobre o caminho absoluto da pasta 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QGridLayout, QVBoxLayout, QHBoxLayout, QToolButton, QLabel)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtCore import QUrl, QSize
from PyQt6.QtGui import QIcon

# IMPORTAÇÃO CORRIGIDA: Apontando para remote_tools (o nome real do seu arquivo)
try:
    from core.remote_tools import launch_remote_tool
except ModuleNotFoundError:
    import core.remote_tools as remote_tools
    launch_remote_tool = remote_tools.launch_remote_tool

class StandaloneHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fiuza Standalone Hub v1.0")
        self.resize(1200, 800)
        
        # Define a pasta de storage para cookies (WhatsApp, etc) dentro de core/storage
        self.storage_path = os.path.join(current_dir, "core", "storage")
        
        # Configura o perfil persistente do Chromium
        self.profile = QWebEngineProfile("PersistentProfile", self)
        self.profile.setPersistentStoragePath(self.storage_path)
        self.profile.setCachePath(self.storage_path)

        # Widget Central e Layout de Abas
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.main_layout.addWidget(self.tabs)
        
        # Estilização Moderna (Dark QSS)
        self.apply_styles()
        
        # Inicia a aba Home (Grid de Botões)
        self.create_home_tab()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0d0e12; }
            QTabWidget::pane { border: 1px solid #1f232a; background: #0d0e12; }
            QTabBar::tab { background: #1a1d24; color: #a0a5b5; padding: 10px 20px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
            QTabBar::tab:selected { background: #252932; color: #00f5d4; font-weight: bold; border-bottom: 2px solid #00f5d4; }
            QWidget#HomeTab { background-color: #0d0e12; }
            QToolButton { background-color: #1a1d24; border: 1px solid #2d3139; border-radius: 12px; color: #ffffff; font-size: 14px; font-weight: 500; padding: 15px; text-align: center; }
            QToolButton:hover { background-color: #252932; border: 1px solid #00f5d4; }
        """)

    def create_home_tab(self):
        self.home_widget = QWidget()
        self.home_widget.setObjectName("HomeTab")
        grid_layout = QGridLayout(self.home_widget)
        grid_layout.setSpacing(25)
        
        # Seus 7 links mapeados rigorosamente
        buttons_data = [
            ("Contako", "https://atendimento.contako.com.br/"),
            ("Tickets", "https://raphanet.confirm8.com/tickets"),
            ("Confirm8", "https://raphanet.confirm8.com/tickets/new"),
            ("WhatsApp", "https://web.whatsapp.com/"),
            ("Ticket Socin", "https://socin.movidesk.com/"),
            ("Ticket Skyone", "https://console.skyone.cloud/"),
            ("Google Keep", "https://keep.google.com/")
        ]
        
        row, col = 0, 0
        for label, url in buttons_data:
            btn = QToolButton()
            btn.setText(label)
            
            # CORREÇÃO DA SINTAXE DO ESTILO AQUI (PyQt6 nativo):
            btn.setToolButtonStyle(btn.toolButtonStyle().ToolButtonTextUnderIcon)
            
            btn.setIconSize(QSize(64, 64))
            btn.setMinimumSize(QSize(180, 140))
            btn.clicked.connect(lambda checked, u=url, t=label: self.open_web_tab(u, t))
            
            grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 3:  # Limite de 4 colunas por linha
                col = 0
                row += 1
                
        # Botão para o Acesso Remoto integrado
        btn_remote = QToolButton()
        btn_remote.setText("AnyDesk / Remoto")
        btn_remote.setToolButtonStyle(btn_remote.toolButtonStyle().ToolButtonTextUnderIcon)
        btn_remote.setMinimumSize(QSize(180, 140))
        btn_remote.clicked.connect(lambda: launch_remote_tool("anydesk"))
        grid_layout.addWidget(btn_remote, row, col)

        self.tabs.addTab(self.home_widget, "Home")

    def open_web_tab(self, url, title):
        browser = QWebEngineView(self)
        browser.setPage(browser.page().__class__(self.profile, browser))
        browser.setUrl(QUrl(url))
        
        index = self.tabs.addTab(browser, title)
        self.tabs.setCurrentIndex(index)

    def close_tab(self, index):
        if index != 0:
            widget = self.tabs.widget(index)
            if widget:
                widget.deleteLater()
            self.tabs.removeTab(index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StandaloneHub()
    window.show()
    sys.exit(app.exec())