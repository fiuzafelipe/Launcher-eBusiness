import os
import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QGridLayout, QVBoxLayout, QHBoxLayout, QToolButton, 
                             QPushButton, QSpacerItem, QSizePolicy, QDialog, 
                             QLineEdit, QLabel, QCheckBox, QFormLayout, QComboBox,
                             QFileDialog, QColorDialog)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtCore import QUrl, QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QBrush, QColor

try:
    from core.remote_tools import launch_remote_tool
except ModuleNotFoundError:
    import core.remote_tools as remote_tools
    launch_remote_tool = remote_tools.launch_remote_tool

current_dir = os.path.dirname(os.path.abspath(__file__))

class StandaloneHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fiuza Standalone Hub v1.0")
        self.resize(1280, 720)
        
        self.config_file = os.path.join(current_dir, "core", "config.json")
        self.storage_path = os.path.join(current_dir, "core", "storage")
        
        self.default_buttons = [
            {"label": "Contako", "url": "https://atendimento.contako.com.br/"},
            {"label": "Tickets", "url": "https://raphanet.confirm8.com/tickets"},
            {"label": "Confirm8", "url": "https://raphanet.confirm8.com/tickets/new"},
            {"label": "WhatsApp", "url": "https://web.whatsapp.com/"},
            {"label": "Ticket Socin", "url": "https://socin.movidesk.com/"},
            {"label": "Ticket Skyone", "url": "https://console.skyone.cloud/"},
            {"label": "Google Keep", "url": "https://keep.google.com/"},
            {"label": "AnyDesk / Remoto", "url": "remote://anydesk"}
        ]
        
        self.presets = {
            "Padrão (preto/branco)": {"theme": "#242120", "accent": "#d9d9d9"},
            "Verde": {"theme": "#0f2419", "accent": "#12d97c"},
            "Vermelho": {"theme": "#270d0d", "accent": "#d91e10"},
            "Azul Claro": {"theme": "#0d2721", "accent": "#0dd9a6"},
            "Azul Escuro": {"theme": "#0d0d27", "accent": "#0d0dd9"},
            "Laranja": {"theme": "#271a0c", "accent": "#d9790c"},
            "Amarelo": {"theme": "#27270c", "accent": "#d9d90c"},
            "Roxo Claro": {"theme": "#270d27", "accent": "#d90ccf"},
            "Rosa": {"theme": "#270d14", "accent": "#d90c3c"},
            "Branco": {"theme": "#d6dcd1", "accent": "#ffffff"}
        }
        
        self.buttons_list = []
        self.auto_save = False
        self.opened_tabs_urls = []
        self.zoom_settings = {}  # Dicionário para salvar os níveis de zoom por URL
        self.current_page = 0
        self.items_per_page = 8
        
        self.accent_color = self.presets["Padrão (preto/branco)"]["accent"]       
        self.theme_base_color = self.presets["Padrão (preto/branco)"]["theme"]   
        self.background_image_path = "" 

        self.load_settings()

        self.profile = QWebEngineProfile("PersistentProfile", self)
        self.profile.setPersistentStoragePath(self.storage_path)
        self.profile.setCachePath(self.storage_path)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.track_tabs)
        self.main_layout.addWidget(self.tabs)
        
        self.apply_styles()
        self.create_home_tab()
        self.restore_tabs()

    def apply_styles(self):
        accent = self.accent_color
        main_bg = self.theme_base_color
        
        c_theme = QColor(main_bg)
        is_light_theme = c_theme.lightness() > 128
        
        text_color = "#07080a" if is_light_theme else "#ffffff"
        tab_text_color = "#232a38" if is_light_theme else "#8a909d"
        
        if is_light_theme:
            top_bar_bg = QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(30, c_theme.lightness() - 12)).name()
            tab_inactive_bg = QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(40, c_theme.lightness() - 20)).name()
        else:
            top_bar_bg = QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(5, c_theme.lightness() - 8)).name()
            tab_inactive_bg = QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(10, c_theme.lightness() + 6)).name()

        c_accent = QColor(accent)
        bg_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.08)"
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.35)"
        
        card_text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {top_bar_bg}; }}
            
            /* Grade Separadora Superior */
            QTabWidget::pane {{ border-top: 2px solid {accent}; background: {main_bg}; }}
            QTabBar {{ background-color: {top_bar_bg}; border-bottom: 1px solid rgba(0,0,0,0.2); qproperty-drawBase: 0; }}
            
            QTabBar::tab {{ 
                background: {tab_inactive_bg}; 
                color: {tab_text_color}; 
                padding: 8px 24px 14px 24px; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px; 
                margin-right: 3px; 
                margin-top: 6px; 
                border: 1px solid rgba(0,0,0,0.15); 
                border-bottom: none; 
                font-family: 'Segoe UI'; 
                font-weight: 500; 
                font-size: 12px; 
            }}
            QTabBar::tab:selected {{ 
                background: {main_bg}; 
                color: {accent}; 
                font-weight: bold; 
                border: 1px solid {accent}; 
                border-bottom: 4px solid {main_bg}; 
                margin-top: 2px; 
                padding-bottom: 16px; 
            }}
            QTabBar::close-button {{ subcontrol-position: right; margin-bottom: 4px; }}
            QTabBar::tab:hover:!selected {{ color: {accent}; background: {bg_dark_tint}; }}
            
            QWidget#HomeTab {{ background-color: {main_bg}; }}
            
            /* Painel Central Superior (Borda Preta Fixa) */
            QPushButton#btn_ops {{ background-color: {bg_dark_tint}; border: 1px solid #000000; color: {text_color}; font-weight: bold; border-radius: 6px; font-size: 13px; font-family: 'Segoe UI'; letter-spacing: 1.5px; }}
            QPushButton#btn_ops:hover {{ background-color: {accent}; color: #07080a; }}
            
            QPushButton#btn_config_menu {{ background-color: {bg_dark_tint}; border: 1px solid #000000; color: {text_color}; font-weight: bold; border-radius: 6px; font-size: 13px; font-family: 'Segoe UI'; letter-spacing: 0.5px; }}
            QPushButton#btn_config_menu:hover {{ background-color: {hover_dark_tint}; border-color: {accent}; color: {accent}; }}
            
            /* Botões de Paginação (< >) */
            QPushButton#btn_nav {{ 
                background-color: {accent}; 
                border: 1px solid #000000; 
                color: {card_text_color}; 
                font-weight: bold; 
                font-size: 15px; 
                border-radius: 5px; 
            }}
            QPushButton#btn_nav:hover {{ 
                background-color: {hover_dark_tint}; 
                color: {accent}; 
                border-color: {accent}; 
            }}
            QPushButton#btn_nav:disabled {{ 
                border: 1px solid rgba(0,0,0,0.1); 
                color: rgba(120, 120, 120, 0.5); 
                background-color: rgba(0, 0, 0, 0.15); 
            }}
        """)

    def create_home_tab(self):
        if hasattr(self, 'home_widget') and self.home_widget:
            self.tabs.removeTab(0)
            self.home_widget.deleteLater()

        self.home_widget = QWidget()
        self.home_widget.setObjectName("HomeTab")
        
        if self.background_image_path and os.path.exists(self.background_image_path):
            self.apply_background_image()
        else:
            self.home_widget.setStyleSheet(f"background-color: {self.theme_base_color};")

        home_vertical_layout = QVBoxLayout(self.home_widget)
        home_vertical_layout.setContentsMargins(40, 35, 40, 35)
        
        control_panel_layout = QVBoxLayout()
        control_panel_layout.setSpacing(10)
        
        btn_ops = QPushButton("STANDALONE HUB")
        btn_ops.setObjectName("btn_ops")
        btn_ops.setFixedSize(450, 42)
        
        btn_config_menu = QPushButton("CONFIGURAÇÕES  ⚙")
        btn_config_menu.setObjectName("btn_config_menu")
        btn_config_menu.setFixedSize(450, 42)
        btn_config_menu.clicked.connect(self.open_settings_dialog)
        
        control_panel_layout.addWidget(btn_ops, alignment=Qt.AlignmentFlag.AlignCenter)
        control_panel_layout.addWidget(btn_config_menu, alignment=Qt.AlignmentFlag.AlignCenter)
        home_vertical_layout.addLayout(control_panel_layout)
        
        home_vertical_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(25)
        
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = self.buttons_list[start_idx:end_idx]
        
        accent = self.accent_color
        c_accent = QColor(accent)
        card_text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"
        
        row, col = 0, 0
        for item in page_items:
            btn = QToolButton()
            btn.setText(item["label"])
            btn.setToolButtonStyle(btn.toolButtonStyle().ToolButtonTextUnderIcon)
            btn.setIconSize(QSize(56, 56))
            btn.setMinimumSize(QSize(220, 145))
            
            btn.setStyleSheet(f"""
                QToolButton {{
                    background-color: {accent};
                    border: 1px solid #000000;
                    border-radius: 12px;
                    color: {card_text_color};
                    font-size: 14px;
                    font-weight: 600;
                    font-family: 'Segoe UI';
                    padding: 12px;
                }}
                QToolButton:hover {{
                    background-color: {hover_dark_tint};
                    border: 1px solid {accent};
                    color: {accent};
                }}
            """)
            
            icon_name = f"{item['label'].lower()}.png"
            icon_path = os.path.join(os.path.dirname(current_dir), "assets", "icons", icon_name)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
            
            if item["url"].startswith("remote://"):
                tool = item["url"].split("//")[1]
                btn.clicked.connect(lambda checked, t=tool: launch_remote_tool(t))
            else:
                btn.clicked.connect(lambda checked, u=item["url"], t=item["label"]: self.open_web_tab(u, t))
            
            self.grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
                
        grid_container_hbox = QHBoxLayout()
        grid_container_hbox.addStretch()
        grid_container_hbox.addLayout(self.grid_layout)
        grid_container_hbox.addStretch()
        home_vertical_layout.addLayout(grid_container_hbox)
        
        home_vertical_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        
        nav_style = f"""
            QPushButton {{
                background-color: {accent};
                border: 1px solid #000000;
                color: {card_text_color};
                font-weight: bold;
                font-size: 15px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {hover_dark_tint};
                color: {accent};
                border-color: {accent};
            }}
            QPushButton:disabled {{
                border: 1px solid rgba(0,0,0,0.1);
                color: rgba(120, 120, 120, 0.5);
                background-color: rgba(0, 0, 0, 0.15);
            }}
        """
        
        btn_prev = QPushButton("<")
        btn_prev.setFixedSize(50, 40)
        btn_prev.setStyleSheet(nav_style)
        btn_prev.setEnabled(self.current_page > 0)
        btn_prev.clicked.connect(self.prev_page)
        
        label_color = "#07080a" if QColor(self.theme_base_color).lightness() > 128 else "#ffffff"
        page_label = QLabel(f"Página {self.current_page + 1}")
        page_label.setStyleSheet(f"color: {label_color}; font-weight: bold; font-size: 13px; font-family: 'Segoe UI';")
        
        max_pages = (len(self.buttons_list) - 1) // self.items_per_page
        btn_next = QPushButton(">")
        btn_next.setFixedSize(50, 40)
        btn_next.setStyleSheet(nav_style)
        btn_next.setEnabled(self.current_page < max_pages)
        btn_next.clicked.connect(self.next_page)
        
        nav_layout.addWidget(btn_prev)
        nav_layout.addWidget(page_label)
        nav_layout.addWidget(btn_next)
        nav_layout.addStretch()
        
        home_vertical_layout.addLayout(nav_layout)

        self.tabs.insertTab(0, self.home_widget, "Home")
        self.tabs.setCurrentIndex(0)

    def apply_background_image(self):
        pixmap = QPixmap(self.background_image_path)
        if not pixmap.isNull():
            base_bg = QPixmap(self.size())
            base_bg.fill(QColor(self.theme_base_color))
            
            from PyQt6.QtGui import QPainter
            painter = QPainter(base_bg)
            painter.drawPixmap(0, 0, self.width(), self.height(), pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            
            c_theme = QColor(self.theme_base_color)
            if c_theme.lightness() > 128:
                painter.fillRect(0, 0, self.width(), self.height(), QColor(255, 255, 255, 200)) 
            else:
                painter.fillRect(0, 0, self.width(), self.height(), QColor(c_theme.red(), c_theme.green(), c_theme.blue(), 215)) 
            painter.end()
            
            palette = self.home_widget.palette()
            palette.setBrush(QPalette.ColorRole.Window, QBrush(base_bg))
            self.home_widget.setPalette(palette)
            self.home_widget.setAutoFillBackground(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.background_image_path and hasattr(self, 'home_widget'):
            self.apply_background_image()

    def next_page(self):
        self.current_page += 1
        self.create_home_tab()

    def prev_page(self):
        self.current_page -= 1
        self.create_home_tab()

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("CONFIGURAÇÕES DO SISTEMA")
        dialog.setFixedWidth(380)
        dialog.setStyleSheet("""
            QDialog { background-color: #11141a; border: 1px solid #1c212d; }
            QLabel { color: #a0a5b5; font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton { background-color: #161b24; border: 1px solid #232a38; color: #ffffff; font-family: 'Segoe UI'; font-weight: 600; padding: 12px; border-radius: 6px; font-size: 13px; text-align: left; padding-left: 15px; }
            QPushButton:hover { background-color: #1f2633; border-color: #45a29e; }
            QPushButton#btn_danger { color: #ff5252; border-color: #3d1c1c; }
            QPushButton#btn_danger:hover { background-color: #2b1313; border-color: #ff5252; }
            QCheckBox { color: #c5c6c7; font-family: 'Segoe UI'; font-size: 13px; font-weight: 500; padding-top: 10px; }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 25, 20, 25)
        
        btn_toolbox = QPushButton("＋  Configurar Toolbox (Adicionar Botão)")
        btn_toolbox.clicked.connect(lambda: [dialog.accept(), self.open_toolbox_dialog()])
        
        btn_delete_toolbox = QPushButton("🗙  Deletar Toolbox (Remover Botão)")
        btn_delete_toolbox.clicked.connect(lambda: [dialog.accept(), self.open_delete_toolbox_dialog()])
        
        btn_presets = QPushButton("🎨  Temas Pré-definidos (Paletas)")
        btn_presets.clicked.connect(lambda: [dialog.accept(), self.open_presets_dialog()])
        
        btn_color = QPushButton("🎨  Alterar Cor de Destaque (Cards e Detalhes)")
        btn_color.clicked.connect(lambda: [dialog.accept(), self.open_color_picker()])
        
        btn_theme = QPushButton("🎭  Alterar Tema (Claro / Escuro Geral)")
        btn_theme.clicked.connect(lambda: [dialog.accept(), self.open_theme_picker()])
        
        btn_bg_image = QPushButton("🖼️  Imagem de Fundo (Wallpaper)")
        btn_bg_image.clicked.connect(lambda: [dialog.accept(), self.open_background_dialog()])
        
        btn_save_man = QPushButton("💾  Salvar Customização")
        btn_save_man.clicked.connect(lambda: [self.save_settings(), dialog.accept()])
        
        btn_reset = QPushButton("🔄  Restaurar Configurações Iniciais (Reset)")
        btn_reset.setObjectName("btn_danger")
        btn_reset.clicked.connect(lambda: [self.reset_to_defaults(), dialog.accept()])
        
        self.chk_auto = QCheckBox("Salvar automaticamente a sessão")
        self.chk_auto.setChecked(self.auto_save)
        self.chk_auto.stateChanged.connect(self.toggle_autosave)
        
        layout.addWidget(btn_toolbox)
        layout.addWidget(btn_delete_toolbox)
        layout.addWidget(btn_presets)
        layout.addWidget(btn_color)
        layout.addWidget(btn_theme)
        layout.addWidget(btn_bg_image)
        layout.addWidget(btn_save_man)
        layout.addWidget(btn_reset)
        layout.addWidget(self.chk_auto)
        
        dialog.exec()

    def open_presets_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Selecionar Tema Pré-definido")
        dialog.setFixedWidth(380)
        dialog.setStyleSheet("""
            QDialog { background-color: #11141a; }
            QLabel { color: #a0a5b5; font-family: 'Segoe UI'; font-size: 13px; }
            QComboBox { background-color: #161b24; border: 1px solid #232a38; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton { font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; text-align: center; }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("Escolha uma das 10 paletas prontas abaixo:"))
        
        combo = QComboBox()
        combo.addItems(list(self.presets.keys()))
        layout.addWidget(combo)
        
        btn_box = QHBoxLayout()
        btn_apply = QPushButton("Aplicar Tema")
        btn_apply.setStyleSheet(f"background-color: {self.accent_color}; color: #07080a;")
        btn_back = QPushButton("Cancelar")
        btn_back.setStyleSheet("background-color: #161b24; border: 1px solid #232a38; color: #fff;")
        
        btn_apply.clicked.connect(lambda: self.apply_preset_theme(combo.currentText(), dialog))
        btn_back.clicked.connect(dialog.reject)
        
        btn_box.addWidget(btn_apply)
        btn_box.addWidget(btn_back)
        layout.addLayout(btn_box)
        
        dialog.exec()

    def apply_preset_theme(self, preset_name, dialog):
        if preset_name in self.presets:
            selected = self.presets[preset_name]
            self.theme_base_color = selected["theme"]
            self.accent_color = selected["accent"]
            
            self.apply_styles()
            self.create_home_tab()
            
            if self.auto_save:
                self.save_settings()
            dialog.accept()

    def open_color_picker(self):
        color = QColorDialog.getColor(QColor(self.accent_color), self, "Escolha sua Cor de Destaque")
        if color.isValid():
            self.accent_color = color.name()
            self.apply_styles()
            self.create_home_tab()
            if self.auto_save:
                self.save_settings()

    def open_theme_picker(self):
        color = QColorDialog.getColor(QColor(self.theme_base_color), self, "Escolha a Cor do Fundo Geral")
        if color.isValid():
            self.theme_base_color = color.name()
            self.apply_styles()
            self.create_home_tab()
            if self.auto_save:
                self.save_settings()

    def open_background_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurar Imagem de Fundo")
        dialog.setFixedWidth(360)
        dialog.setStyleSheet("background-color: #11141a; color: #fff;")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("Personalize o fundo do seu Standalone Hub:"))
        
        btn_add = QPushButton("Adicionar Imagem")
        btn_add.setStyleSheet("background-color: #161b24; color: white; padding: 10px; border-radius: 6px;")
        btn_add.clicked.connect(lambda: self.select_background_image(dialog))
        
        btn_del = QPushButton("Excluir Imagem")
        btn_del.setStyleSheet("background-color: #ff5252; color: white; padding: 10px; border-radius: 6px;")
        btn_del.clicked.connect(lambda: self.remove_background_image(dialog))
        
        layout.addWidget(btn_add)
        layout.addWidget(btn_del)
        dialog.exec()

    def select_background_image(self, dialog):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem de Fundo", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.background_image_path = file_path
            self.apply_background_image()
            if self.auto_save:
                self.save_settings()
            dialog.accept()

    def remove_background_image(self, dialog):
        self.background_image_path = ""
        self.home_widget.setAutoFillBackground(False)
        self.create_home_tab()
        if self.auto_save:
            self.save_settings()
        dialog.accept()

    def open_toolbox_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar ao Toolbox")
        dialog.setFixedWidth(420)
        dialog.setStyleSheet("""
            QDialog { background-color: #11141a; }
            QLabel { color: #a0a5b5; font-family: 'Segoe UI'; font-size: 12px; font-weight: 500; }
            QLineEdit { background-color: #161b24; border: 1px solid #232a38; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; }
            QLineEdit:focus { border: 1px solid #45a29e; }
            QPushButton { font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }
        """)
        
        form_layout = QFormLayout(dialog)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        input_name = QLineEdit()
        input_url = QLineEdit()
        
        form_layout.addRow(QLabel("Nome do Botão (Nome do ícone em assets/icons):"), input_name)
        form_layout.addRow(QLabel("URL do Site de Acesso:"), input_url)
        
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Adicionar")
        btn_save.setStyleSheet(f"background-color: {self.accent_color}; color: #07080a; text-align: center; padding-left: 0;")
        btn_back = QPushButton("Cancelar")
        btn_back.setStyleSheet("background-color: #161b24; border: 1px solid #232a38; color: #fff; text-align: center; padding-left: 0;")
        
        btn_save.clicked.connect(lambda: self.add_toolbox_item(input_name.text(), input_url.text(), dialog))
        btn_back.clicked.connect(dialog.reject)
        
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_back)
        form_layout.addRow(btn_box)
        
        dialog.exec()

    def add_toolbox_item(self, name, url, dialog):
        if name.strip() and url.strip():
            self.buttons_list.append({"label": name, "url": url})
            if self.auto_save:
                self.save_settings()
            self.create_home_tab()
            dialog.accept()

    def open_delete_toolbox_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Remover Botão do Toolbox")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet("""
            QDialog { background-color: #11141a; }
            QLabel { color: #a0a5b5; font-family: 'Segoe UI'; font-size: 13px; }
            QComboBox { background-color: #161b24; border: 1px solid #232a38; border-radius: 6px; color: #fff; padding: 8px; font-family: 'Segoe UI'; }
            QPushButton { font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; text-align: center; padding-left: 0; }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("Selecione o botão que deseja excluir definitivamente:"))
        
        combo = QComboBox()
        for item in self.buttons_list:
            combo.addItem(item["label"])
        layout.addWidget(combo)
        
        btn_box = QHBoxLayout()
        btn_del = QPushButton("Deletar e Salvar")
        btn_del.setStyleSheet("background-color: #ff5252; color: #fff;")
        btn_back = QPushButton("Voltar")
        btn_back.setStyleSheet("background-color: #161b24; border: 1px solid #232a38; color: #fff;")
        
        btn_del.clicked.connect(lambda: self.delete_toolbox_item(combo.currentText(), dialog))
        btn_back.clicked.connect(dialog.reject)
        
        btn_box.addWidget(btn_del)
        btn_box.addWidget(btn_back)
        layout.addLayout(btn_box)
        
        dialog.exec()

    def delete_toolbox_item(self, target_label, dialog):
        self.buttons_list = [item for item in self.buttons_list if item["label"] != target_label]
        max_pages = max(0, (len(self.buttons_list) - 1) // self.items_per_page)
        if self.current_page > max_pages:
            self.current_page = max_pages
        self.save_settings()
        self.create_home_tab()
        dialog.accept()

    def toggle_autosave(self, state):
        self.auto_save = (state == 2)
        if self.auto_save:
            self.save_settings()

    def save_settings(self):
        # Captura os níveis de zoom atuais de todas as abas abertas antes de salvar
        self.track_zoom_levels()
        
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        data = {
            "auto_save": self.auto_save,
            "accent_color": self.accent_color,
            "theme_base_color": self.theme_base_color,
            "background_image_path": self.background_image_path,
            "buttons": self.buttons_list,
            "opened_tabs": self.opened_tabs_urls if self.auto_save else [],
            "zoom_settings": self.zoom_settings  # Salva o dicionário de zoom no JSON
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.auto_save = data.get("auto_save", False)
                    self.accent_color = data.get("accent_color", "#d9d9d9")
                    self.theme_base_color = data.get("theme_base_color", "#242120")
                    self.background_image_path = data.get("background_image_path", "")
                    self.buttons_list = data.get("buttons", self.default_buttons.copy())
                    self.opened_tabs_urls = data.get("opened_tabs", [])
                    self.zoom_settings = data.get("zoom_settings", {})  # Carrega as configurações de zoom
                    return
            except Exception:
                pass
        self.buttons_list = self.default_buttons.copy()
        self.zoom_settings = {}

    def reset_to_defaults(self):
        self.buttons_list = self.default_buttons.copy()
        self.accent_color = self.presets["Padrão (preto/branco)"]["accent"]
        self.theme_base_color = self.presets["Padrão (preto/branco)"]["theme"]
        self.background_image_path = ""
        self.current_page = 0
        self.auto_save = False
        self.opened_tabs_urls = []
        self.zoom_settings = {}
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        self.home_widget.setAutoFillBackground(False)
        self.apply_styles()
        self.create_home_tab()

    def open_web_tab(self, url, title):
        browser = QWebEngineView(self)
        browser.setPage(browser.page().__class__(self.profile, browser))
        browser.setUrl(QUrl(url))
        
        # CORREÇÃO AQUI: Conectamos ao zoomFactorChanged da PAGE interna da view
        browser.page().zoomFactorChanged.connect(lambda factor, b=browser: self.on_zoom_changed(b, factor))
        
        # Se houver um zoom salvo para essa URL, aplica imediatamente ao carregar
        if url in self.zoom_settings:
            browser.setZoomFactor(self.zoom_settings[url])
            
        index = self.tabs.addTab(browser, title)
        self.tabs.setCurrentIndex(index)
        self.track_tabs()

    # Atualiza o fator de zoom em tempo real e dispara o auto-save se ativo
    def on_zoom_changed(self, browser, factor):
        try:
            url = browser.url().toString()
            if url and url != "about:blank":
                self.zoom_settings[url] = factor
                if self.auto_save:
                    # Salva as configurações de forma segura sem loop
                    self.save_settings()
        except RuntimeError:
            # Previne erros caso o widget já esteja sendo destruído no encerramento da aba
            pass

    # Varre as abas ativas para garantir que o estado do zoom do momento seja capturado
    def track_zoom_levels(self):
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                url = widget.url().toString()
                if url and url != "about:blank":
                    self.zoom_settings[url] = widget.zoomFactor()

    def close_tab(self, index):
        if index != 0:
            widget = self.tabs.widget(index)
            if widget:
                widget.deleteLater()
            self.tabs.removeTab(index)
            self.track_tabs()

    def track_tabs(self):
        if not self.auto_save:
            return
        urls = []
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                urls.append({"label": self.tabs.tabText(i), "url": widget.url().toString()})
        self.opened_tabs_urls = urls
        self.save_settings()

    def restore_tabs(self):
        if self.auto_save and self.opened_tabs_urls:
            tabs_to_open = list(self.opened_tabs_urls)
            for t in tabs_to_open:
                self.open_web_tab(t["url"], t["label"])

    def closeEvent(self, event):
        if self.auto_save:
            self.track_tabs()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StandaloneHub()
    window.show()
    sys.exit(app.exec())