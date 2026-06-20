import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QGridLayout, QVBoxLayout, QHBoxLayout, QToolButton, QLabel)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtCore import QUrl, QSize
from PyQt6.QtGui import QIcon

# Importa o módulo remoto que criamos
from core.remote import launch_remote_tool

class StandaloneHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fiuza Standalone Hub v1.0")
        self.resize(1200, 800)
        
        # Configura perfil persistente para salvar cookies (WhatsApp, etc)
        self.storage_path = os.path.join(os.getcwd(), "src", "core", "storage")
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
        
        # Inicia a aba Home (Grid)
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
        
        # Lista com os seus 7 botões solicitados: (Texto, URL)
        buttons_data = [
            ("Contako", "https://atendimento.contako.com.br/"),
            ("Tickets", "https://raphanet.confirm8.com/tickets"),
            ("Confirm8", "https://raphanet.confirm8.com/tickets/new"),
            ("WhatsApp", "https://web.whatsapp.com/"),
            ("Ticket Socin", "https://socin.movidesk.com/"),
            ("Ticket Skyone", "https://console.skyone.cloud/"),
            ("Google Keep", "https://keep.google.com/")
        ]
        
        # Renderiza os 7 botões organizados em um Grid dinâmico (por exemplo, 4 colunas)
        row, col = 0, 0
        for label, url in buttons_data:
            btn = QToolButton()
            btn.setText(label)
            btn.setToolButtonStyle(QToolButton.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setIconSize(QSize(64, 64))
            
            # TODO: Quando tiver suas imagens/ícones na pasta assets, descomente a linha abaixo:
            # btn.setIcon(QIcon(f"assets/{label.lower().replace(' ', '_')}.png"))
            
            btn.setMinimumSize(QSize(180, 140))
            
            # Conexão do clique passando a URL correta
            btn.clicked.connect(lambda checked, u=url, t=label: self.open_web_tab(u, t))
            
            grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 3:  # Máximo de 4 botões por linha, joga o resto para baixo
                col = 0
                row += 1
                
        # Adiciona um botão extra dedicado para Acesso Remoto no final do grid
        btn_remote = QToolButton()
        btn_remote.setText("AnyDesk / Remoto")
        btn_remote.setMinimumSize(QSize(180, 140))
        btn_remote.clicked.connect(lambda: launch_remote_tool("anydesk"))
        grid_layout.addWidget(btn_remote, row, col)

        self.tabs.addTab(self.home_widget, "Home")

    def open_web_tab(self, url, title):
        # Instancia a view utilizando o perfil persistente de cookies
        browser = QWebEngineView(self)
        browser.setPage(browser.page().__class__(self.profile, browser))
        browser.setUrl(QUrl(url))
        
        index = self.tabs.addTab(browser, title)
        self.tabs.setCurrentIndex(index)

    def close_tab(self, index):
        if index != 0:  # Impede fechar a aba Home principal
            widget = self.tabs.widget(index)
            if widget:
                widget.deleteLater()
            self.tabs.removeTab(index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StandaloneHub()
    window.show()
    sys.exit(app.exec())