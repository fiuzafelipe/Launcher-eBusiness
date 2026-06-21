import os
import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QGridLayout, QVBoxLayout, QHBoxLayout, QToolButton, 
                             QPushButton, QSpacerItem, QSizePolicy, QDialog, 
                             QLineEdit, QLabel, QCheckBox, QFormLayout, QComboBox,
                             QFileDialog, QColorDialog, QTabBar, QMessageBox, QScrollArea)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePermission, QWebEngineDownloadRequest, QWebEnginePage
from PyQt6.QtCore import QUrl, QSize, Qt, QMimeData, QPoint, QTimer, QEvent, QRect
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QBrush, QColor, QDrag, QAction, QCursor

# Otimizações de inicialização do motor Chromium
sys.argv.append("--disable-gpu-shader-disk-cache")
sys.argv.append("--process-per-site")      
sys.argv.append("--renderer-process-limit=6") 

current_dir = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
# SUBCLASSE PARA BOTÃO ARRASTÁVEL COM COMPORTAMENTO DE FAVORITO E EXCLUSÃO
# ==============================================================================
class DraggableToolButton(QToolButton):
    def __init__(self, item_data, item_index, parent_hub, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.item_index = item_index
        self.hub = parent_hub
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        
        self.internal_layout = QVBoxLayout(self)
        self.internal_layout.setContentsMargins(5, 5, 10, 10)
        self.internal_layout.addStretch()
        
        self.action_layout = QHBoxLayout()
        self.action_layout.setSpacing(10)
        
        self.btn_star = QPushButton()
        self.btn_star.setFixedSize(20, 20)
        self.btn_star.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_star_visual()
        self.btn_star.clicked.connect(self.toggle_favorite)
        
        self.btn_delete = QPushButton("✕")
        self.btn_delete.setFixedSize(20, 20)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet("""
            QPushButton { background: transparent; color: #ff5252; font-weight: bold; border: none; font-size: 14px; }
            QPushButton:hover { color: #ff0000; }
        """)
        self.btn_delete.clicked.connect(self.confirm_delete)
        
        self.action_layout.addWidget(self.btn_star)
        self.action_layout.addStretch()
        self.action_layout.addWidget(self.btn_delete)
        self.internal_layout.addLayout(self.action_layout)

    def update_star_visual(self):
        is_fav = self.item_data.get("favorite", False)
        color = "#ffeb3b" if is_fav else "rgba(150, 150, 150, 0.4)"
        self.btn_star.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {color}; border: none; font-size: 18px; }}
            QPushButton:hover {{ color: #ffeb3b; }}
        """)
        self.btn_star.setText("★" if is_fav else "☆")

    def toggle_favorite(self):
        self.item_data["favorite"] = not self.item_data.get("favorite", False)
        self.update_star_visual()
        self.hub.save_settings(force=True)
        self.hub.update_favorites_panel()

    def confirm_delete(self):
        reply = QMessageBox.question(
            self, "Confirmar Exclusão", 
            f"Deseja apagar o botão '{self.item_data['label']}'? SIM OU NÃO.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.hub.delete_button_by_data(self.item_data)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.__drag_start_pos = event.pos()
            self.__drag_occurred = False 
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.MouseButton.LeftButton:
            return
        if (event.pos() - self.__drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        
        self.__drag_occurred = True
        
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.item_index))
        drag.setMimeData(mime_data)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.pos())
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        try:
            source_index = int(event.mimeData().text())
            target_index = self.item_index
            if source_index != target_index:
                self.hub.reorder_buttons(source_index, target_index)
                event.acceptProposedAction()
        except ValueError:
            pass

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if getattr(self, '__drag_occurred', False):
                self.__drag_occurred = False
                event.accept()
                return 
            
            url = self.item_data["url"]
            label = self.item_data["label"]
            if url.startswith("remote://"):
                tool = url.split("//")[1]
                try:
                    launch_remote_tool(tool)
                except NameError:
                    pass
            else:
                self.hub.open_web_tab(url, label)
                
        super().mouseReleaseEvent(event)

# ==============================================================================
# SUBCLASSE DE QTABWIDGET ADAPTADA PARA CONTROLE DE ABAS REORDENÁVEIS
# ==============================================================================
class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)  
        self.tabBar().tabMoved.connect(self.handle_tab_moved)

    def handle_tab_moved(self, from_idx, to_idx):
        if from_idx == 0 or to_idx == 0:
            self.tabBar().tabMoved.disconnect(self.handle_tab_moved)
            self.tabBar().moveTab(to_idx, from_idx)
            self.tabBar().tabMoved.connect(self.handle_tab_moved)
            return
        window = self.window()
        if hasattr(window, 'track_tabs_after_move'):
            window.track_tabs_after_move()

# ==============================================================================
# CLASSE PRINCIPAL STANDALONE HUB
# ==============================================================================
class StandaloneHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fiuza Standalone Hub v1.0")
        self.resize(1280, 720)
        
        self.config_file = os.path.join(current_dir, "core", "config.json")
        self.storage_path = os.path.join(current_dir, "core", "storage")
        
        self.default_buttons = [
            {"label": "Contako", "url": "https://atendimento.contako.com.br/", "favorite": False},
            {"label": "Tickets", "url": "https://raphanet.confirm8.com/tickets", "favorite": False},
            {"label": "Confirm8", "url": "https://raphanet.confirm8.com/tickets/new", "favorite": False},
            {"label": "WhatsApp", "url": "https://web.whatsapp.com/", "favorite": False},
            {"label": "Ticket Socin", "url": "https://socin.movidesk.com/", "favorite": False},
            {"label": "Ticket Skyone", "url": "https://console.skyone.cloud/", "favorite": False},
            {"label": "Google Keep", "url": "https://keep.google.com/", "favorite": False},
            {"label": "AnyDesk / Remoto", "url": "remote://anydesk", "favorite": False}
        ]
        
        self.presets = {
            "Padrão (preto/branco)": {"theme": "#242120", "accent": "#d9d9d9"},
            "Verde": {"theme": "#0f2419", "accent": "#12d97c"},
            "Vermelho": {"theme": "#270d0d", "accent": "#d91e10"},
            "Azul Claro": {"theme": "#0d2721", "accent": "#0dd9a6"},
            "Azul Escuro": {"theme": "#0d0d27", "accent": "#0d0dd9"},
            "Laranja": {"theme": "#271a0c", "accent": "#d9790c"},
            "Amarelo": {"theme": "#27270c", "accent": "#d9d9d9"},
            "Roxo Claro": {"theme": "#270d27", "accent": "#d90ccf"},
            "Rosa": {"theme": "#270d14", "accent": "#d90c3c"},
            "Branco": {"theme": "#d6dcd1", "accent": "#ffffff"}
        }
        
        self.buttons_list = []
        self.auto_save = False          
        self.save_tabs_enabled = False  
        self.opened_tabs_urls = []
        self.zoom_settings = {}
        self.current_page = 0
        self.items_per_page = 8
        self.is_restoring = False  
        self.search_filter = ""
        
        self.accent_color = self.presets["Padrão (preto/branco)"]["accent"]       
        self.theme_base_color = self.presets["Padrão (preto/branco)"]["theme"]   
        self.background_image_path = "" 

        self.load_settings()

        self.profile = QWebEngineProfile("PersistentProfile", self)
        self.profile.setPersistentStoragePath(self.storage_path)
        self.profile.setCachePath(self.storage_path)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.profile.setHttpCacheMaximumSize(52428800) 
        self.profile.downloadRequested.connect(self.handle_download_request)
        
        modern_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        self.profile.setHttpUserAgent(modern_user_agent)
        self.profile.setHttpAcceptLanguage("pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.tabs = CustomTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.optimize_memory_without_reload)
        
        self.btn_direct_nav = QToolButton()
        self.btn_direct_nav.setText("🔗")
        self.btn_direct_nav.setToolTip("Navegar para URL Direta")
        self.btn_direct_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_direct_nav.setStyleSheet("QToolButton { background: transparent; border: none; font-size: 14px; color: white; padding: 4px; } QToolButton:hover { color: #12d97c; }")
        self.btn_direct_nav.clicked.connect(self.open_direct_nav_dialog)
        self.tabs.setCornerWidget(self.btn_direct_nav, Qt.Corner.TopLeftCorner)
        
        self.main_layout.addWidget(self.tabs)
        
        self.bottom_bar = QHBoxLayout()
        self.bottom_bar.setContentsMargins(15, 8, 15, 8)
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-family: 'Segoe UI'; font-weight: bold; font-size: 12px; min-height: 20px;")
        self.btn_save_session = QPushButton("Save")
        self.btn_save_session.setFixedSize(100, 30)
        self.btn_save_session.clicked.connect(self.trigger_save_tabs_button)
        
        self.bottom_bar.addWidget(self.lbl_status)
        self.bottom_bar.addStretch()
        self.bottom_bar.addWidget(self.btn_save_session)
        self.main_layout.addLayout(self.bottom_bar)
        
        self.create_favorites_panel_widget()
        
        self.apply_styles()
        self.create_home_tab()
        
        QTimer.singleShot(100, self.restore_tabs)
        self.update_save_tabs_button_visual()
        
        self.update_favorites_panel() 
        
        self.tabs.tabBar().setMouseTracking(True)
        self.tabs.tabBar().installEventFilter(self)

        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.setInterval(200)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position_for_favorites)
        self.mouse_check_timer.start()

    def optimize_memory_without_reload(self, index):
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                if i != index:
                    widget.setVisible(False)
                else:
                    widget.setVisible(True)
        import gc
        gc.collect()

    def open_direct_nav_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("NAVEGAR PARA WEBSITE")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet("QDialog { background-color: #11141a; border: 1px solid #232a38; } QLabel { color: #12d97c; font-family: 'Segoe UI'; font-weight: bold; } QLineEdit { background-color: #161b24; border: 1px solid #232a38; color: #fff; padding: 8px; border-radius: 4px; }")
        layout = QVBoxLayout(dialog)
        
        lbl = QLabel("DIGITE AQUI A URL DE ACESSO:")
        input_url = QLineEdit()
        input_url.setPlaceholderText("Exemplo: https://google.com.br")
        input_url.returnPressed.connect(dialog.accept)
        
        layout.addWidget(lbl)
        layout.addWidget(input_url)
        
        if dialog.exec() == QDialog.DialogCode.Accepted and input_url.text().strip():
            url = input_url.text().strip()
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            self.open_web_tab(url, "Navegação")

    def create_favorites_panel_widget(self):
        self.fav_panel_widget = QWidget(self)
        self.fav_panel_widget.setObjectName("FavPanelWidget")
        self.fav_panel_widget.setFixedHeight(48)
        self.fav_panel_widget.setVisible(False)
        
        self.fav_layout = QVBoxLayout(self.fav_panel_widget)
        self.fav_layout.setContentsMargins(15, 5, 15, 5)
        
        self.fav_scroll = QScrollArea()
        self.fav_scroll.setWidgetResizable(True)
        self.fav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.fav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.fav_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.fav_container = QWidget()
        self.fav_container.setStyleSheet("background: transparent;")
        self.fav_hbox = QHBoxLayout(self.fav_container)
        self.fav_hbox.setContentsMargins(0, 0, 0, 0)
        self.fav_hbox.setSpacing(15)
        
        self.fav_scroll.setWidget(self.fav_container)
        self.fav_layout.addWidget(self.fav_scroll)

    def update_favorites_panel(self):
        while self.fav_hbox.count():
            child = self.fav_hbox.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        fav_items = [b for b in self.buttons_list if b.get("favorite", False)]
        
        for item in fav_items:
            btn = QPushButton(item["label"])
            btn.setFixedSize(130, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({QColor(self.accent_color).red()}, {QColor(self.accent_color).green()}, {QColor(self.accent_color).blue()}, 0.35);
                    border: 1px solid rgba(0,0,0,0.4);
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 4px;
                    padding-left: 5px;
                    padding-right: 5px;
                }}
                QPushButton:hover {{
                    background-color: {self.accent_color};
                    color: #07080a;
                }}
            """)
            btn.clicked.connect(lambda checked, u=item["url"], l=item["label"]: self.open_web_tab(u, l))
            self.fav_hbox.addWidget(btn)
            
        self.fav_hbox.addStretch()

    def check_mouse_position_for_favorites(self):
        if not hasattr(self, 'home_widget') or not self.home_widget:
            return
            
        # AJUSTE: Só abre em Home
        if self.tabs.currentIndex() != 0:
            if self.fav_panel_widget.isVisible():
                self.fav_panel_widget.setVisible(False)
            return

        has_favs = any(b.get("favorite", False) for b in self.buttons_list)
        if not has_favs:
            if self.fav_panel_widget.isVisible():
                self.fav_panel_widget.setVisible(False)
            return
            
        global_cursor_pos = QCursor.pos()
        tab_bar = self.tabs.tabBar()
        if tab_bar.count() == 0:
            return
            
        tab_rect = tab_bar.tabRect(0)
        global_top_left = tab_bar.mapToGlobal(tab_rect.topLeft())
        global_bottom_right = tab_bar.mapToGlobal(tab_rect.bottomRight())
        
        home_tab_global_rect = QRect(global_top_left, global_bottom_right)
        
        fav_global_topleft = self.fav_panel_widget.mapToGlobal(QPoint(0,0))
        fav_global_rect = QRect(fav_global_topleft.x(), fav_global_topleft.y(), self.fav_panel_widget.width(), self.fav_panel_widget.height())
        
        if home_tab_global_rect.contains(global_cursor_pos) or (self.fav_panel_widget.isVisible() and fav_global_rect.contains(global_cursor_pos)):
            if not self.fav_panel_widget.isVisible():
                self.fav_panel_widget.setGeometry(0, tab_bar.height() + 2, self.width(), 48)
                self.fav_panel_widget.setVisible(True)
                self.fav_panel_widget.raise_()
        else:
            if self.fav_panel_widget.isVisible():
                self.fav_panel_widget.setVisible(False)

    def eventFilter(self, obj, event):
        if obj == self.tabs.tabBar():
            if event.type() == QEvent.Type.MouseMove:
                # AJUSTE: Proteção para não disparar em abas de sites!
                if self.tabs.currentIndex() == 0:
                    idx = self.tabs.tabBar().tabAt(event.pos())
                    if idx == 0:
                        has_favs = any(b.get("favorite", False) for b in self.buttons_list)
                        if has_favs and not self.fav_panel_widget.isVisible():
                            self.fav_panel_widget.setGeometry(0, self.tabs.tabBar().height() + 2, self.width(), 48)
                            self.fav_panel_widget.setVisible(True)
                            self.fav_panel_widget.raise_()
        return super().eventFilter(obj, event)

    def delete_button_by_data(self, item_data):
        self.buttons_list = [b for b in self.buttons_list if b != item_data]
        self.save_settings(force=True)
        self.create_home_tab()
        self.update_favorites_panel()

    def handle_download_request(self, download: QWebEngineDownloadRequest):
        suggested_path = download.downloadDirectory() + os.sep + download.downloadFileName()
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", suggested_path)
        if file_path:
            download.setDownloadDirectory(os.path.dirname(file_path))
            download.setDownloadFileName(os.path.basename(file_path))
            download.accept()
            self.lbl_status.setText(f"Baixando: {os.path.basename(file_path)}...")
            download.receivedBytesChanged.connect(lambda: self.update_download_progress(download))
        else:
            download.interrupt()

    def update_download_progress(self, download):
        if download.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress:
            total = download.totalBytes()
            received = download.receivedBytes()
            if total > 0:
                percent = int((received / total) * 100)
                self.lbl_status.setText(f"Baixando... {percent}%")
        elif download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self.lbl_status.setText("Download concluído com sucesso!")
            QTimer.singleShot(4000, lambda: self.lbl_status.setText("") if "concluído" in self.lbl_status.text() else None)

    def handle_permission_request(self, request):
        request.grant()

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
            QTabBar::tab:first {{ qproperty-closable: false; }}
            
            QWidget#HomeTab {{ background-color: {main_bg}; }}
            
            QWidget#FavPanelWidget {{
                background-color: rgba({c_theme.red()}, {c_theme.green()}, {c_theme.blue()}, 0.94);
                border-bottom: 1px solid rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.6);
            }}
            
            QPushButton#btn_ops {{ background-color: {bg_dark_tint}; border: 1px solid #000000; color: {text_color}; font-weight: bold; border-radius: 6px; font-size: 13px; font-family: 'Segoe UI'; letter-spacing: 1.5px; }}
            QPushButton#btn_ops:hover {{ background-color: {accent}; color: #07080a; }}
            
            QPushButton#btn_config_menu {{ background-color: {bg_dark_tint}; border: 1px solid #000000; color: {text_color}; font-weight: bold; border-radius: 6px; font-size: 13px; font-family: 'Segoe UI'; letter-spacing: 0.5px; }}
            QPushButton#btn_config_menu:hover {{ background-color: {hover_dark_tint}; border-color: {accent}; color: {accent}; }}
        """)
        
        self.lbl_status.setStyleSheet(f"color: {text_color}; font-family: 'Segoe UI'; font-weight: bold; font-size: 12px; margin: 0px; padding: 0px;")
        self.update_save_tabs_button_visual()
        self.sync_all_whatsapp_themes()

    def update_save_tabs_button_visual(self):
        accent = self.accent_color
        c_accent = QColor(accent)
        card_text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
        
        if self.save_tabs_enabled:
            self.btn_save_session.setStyleSheet(f"""
                QPushButton {{
                    background-color: {accent};
                    border: 1px solid #000000;
                    color: {card_text_color};
                    font-family: 'Segoe UI';
                    font-weight: bold;
                    border-radius: 4px;
                    margin: 0px;
                }}
            """)
            self.lbl_status.setText("Save abas ativado.")
        else:
            self.btn_save_session.setStyleSheet("""
                QPushButton {{
                    background-color: #161b24;
                    border: 1px solid #232a38;
                    color: #8a909d;
                    font-family: 'Segoe UI';
                    font-weight: bold;
                    border-radius: 4px;
                    margin: 0px;
                }}
                QPushButton:hover {{
                    border-color: #45a29e;
                    color: #fff;
                }}
            """)
            self.lbl_status.setText("")

    def trigger_save_tabs_button(self):
        self.save_tabs_enabled = not self.save_tabs_enabled
        self.update_save_tabs_button_visual()
        if self.save_tabs_enabled:
            self.rebuild_tabs_list_manually()
        else:
            self.opened_tabs_urls = []
        self.save_settings(force=True)

    def toggle_auto_save_from_checkbox(self, state):
        is_checked = (state == 2 or state == Qt.CheckState.Checked)
        self.auto_save = is_checked
        if self.auto_save:
            self.save_settings(force=True)

    def reorder_buttons(self, src_idx, target_idx):
        item = self.buttons_list.pop(src_idx)
        self.buttons_list.insert(target_idx, item)
        self.save_settings(force=True)
        self.create_home_tab()

    def filter_buttons_by_search(self, text):
        self.search_filter = text
        
        filtered_list = [b for b in self.buttons_list if self.search_filter.strip().lower() in b["label"].lower()]
        
        # AJUSTE DE ESTABILIDADE: Remove e reconstrói o container da grade para anular bugs do PyQt de espaçamento!
        if hasattr(self, 'grid_hbox') and self.grid_hbox is not None:
            self.grid_container_layout.removeItem(self.grid_hbox)
            old_widget = QWidget()
            old_widget.setLayout(self.grid_hbox)
            old_widget.deleteLater()
            
        self.grid_hbox = QHBoxLayout()
        self.grid_hbox.addStretch()
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(25)
        
        self.grid_hbox.addLayout(self.grid_layout)
        self.grid_hbox.addStretch()
        
        self.grid_container_layout.addLayout(self.grid_hbox)
                
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = filtered_list[start_idx:end_idx]
        
        accent = self.accent_color
        c_accent = QColor(accent)
        card_text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"
        
        row, col = 0, 0
        for i, item in enumerate(page_items):
            real_index = self.buttons_list.index(item)
            btn = DraggableToolButton(item_data=item, item_index=real_index, parent_hub=self)
            btn.setText(item["label"])
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setIconSize(QSize(56, 56))
            
            btn.setFixedSize(220, 145)
            
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
            
            self.grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
                
        max_pages = max(0, (len(filtered_list) - 1) // self.items_per_page)
        if hasattr(self, 'btn_next_page'):
            self.btn_next_page.setEnabled(self.current_page < max_pages)
            self.btn_prev_page.setEnabled(self.current_page > 0)
            self.page_label.setText(f"Página {self.current_page + 1}")

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
        home_vertical_layout.setContentsMargins(0, 0, 0, 0)
        home_vertical_layout.setSpacing(0)
        
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        
        # AJUSTE DE ALINHAMENTO: 55px (Perfeito para abrigar a barra flutuante de 48px com uma folga limpa)
        content_layout.setContentsMargins(40, 55, 40, 25)
        
        control_panel_layout = QVBoxLayout()
        control_panel_layout.setSpacing(10)
        
        btn_ops = QPushButton("STANDALONE HUB")
        btn_ops.setObjectName("btn_ops")
        btn_ops.setFixedSize(450, 42)
        
        btn_config_menu = QPushButton("CONFIGURAÇÕES  ⚙")
        btn_config_menu.setObjectName("btn_config_menu")
        btn_config_menu.setFixedSize(450, 42)
        btn_config_menu.clicked.connect(self.open_settings_dialog)
        
        self.search_bar = QLineEdit()
        self.search_bar.setFixedSize(450, 42)
        self.search_bar.setPlaceholderText("Digite aqui o botão que deseja acessar...")
        
        self.search_bar.blockSignals(True)
        self.search_bar.setText(self.search_filter)
        self.search_bar.blockSignals(False)
        self.search_bar.textChanged.connect(self.filter_buttons_by_search)
        
        c_theme = QColor(self.theme_base_color)
        is_light = c_theme.lightness() > 128
        input_bg = "rgba(255, 255, 255, 0.1)" if not is_light else "rgba(0, 0, 0, 0.05)"
        input_text = "#ffffff" if not is_light else "#07080a"
        
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: {input_bg};
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 6px;
                color: {input_text};
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: 600;
                padding-left: 15px;
                padding-right: 15px;
            }}
            QLineEdit:focus {{
                border: 1px solid {self.accent_color};
            }}
        """)
        
        control_panel_layout.addWidget(btn_ops, alignment=Qt.AlignmentFlag.AlignCenter)
        control_panel_layout.addWidget(btn_config_menu, alignment=Qt.AlignmentFlag.AlignCenter)
        control_panel_layout.addWidget(self.search_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addLayout(control_panel_layout)
        
        content_layout.addSpacing(20)

        # AJUSTE BLINDADO: A grade agora vive em um layout próprio para limpar seu tamanho seguramente
        self.grid_container_widget = QWidget()
        self.grid_container_layout = QVBoxLayout(self.grid_container_widget)
        self.grid_container_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.grid_container_widget)
        
        content_layout.addStretch()

        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        
        accent = self.accent_color
        c_accent = QColor(accent)
        card_text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"
        
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
        
        self.btn_prev_page = QPushButton("<")
        self.btn_prev_page.setFixedSize(50, 40)
        self.btn_prev_page.setStyleSheet(nav_style)
        self.btn_prev_page.clicked.connect(self.prev_page)
        
        label_color = "#07080a" if QColor(self.theme_base_color).lightness() > 128 else "#ffffff"
        self.page_label = QLabel(f"Página {self.current_page + 1}")
        self.page_label.setStyleSheet(f"color: {label_color}; font-weight: bold; font-size: 13px; font-family: 'Segoe UI';")
        
        self.btn_next_page = QPushButton(">")
        self.btn_next_page.setFixedSize(50, 40)
        self.btn_next_page.setStyleSheet(nav_style)
        self.btn_next_page.clicked.connect(self.next_page)
        
        nav_layout.addWidget(self.btn_prev_page)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.btn_next_page)
        nav_layout.addStretch()
        content_layout.addLayout(nav_layout)
        
        home_vertical_layout.addWidget(content_container)

        self.tabs.insertTab(0, self.home_widget, "Home")
        
        self.grid_hbox = None
        self.filter_buttons_by_search(self.search_filter)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.filter_buttons_by_search(self.search_filter)

    def next_page(self):
        filtered_list = self.buttons_list
        if self.search_filter:
            filtered_list = [b for b in self.buttons_list if self.search_filter.strip().lower() in b["label"].lower()]
        max_pages = max(0, (len(filtered_list) - 1) // self.items_per_page)
        if self.current_page < max_pages:
            self.current_page += 1
            self.filter_buttons_by_search(self.search_filter)

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("CONFIGURAÇÕES DO SISTEMA")
        dialog.setFixedWidth(380)
        dialog.setStyleSheet("""
            QDialog { background-color: #11141a; border: 1px solid #1c212d; }
            QLabel { color: #a0a5b5; font-family: 'Segoe UI'; font-size: 13px; }
            QCheckBox { color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; padding: 5px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QPushButton { background-color: #161b24; border: 1px solid #232a38; color: #ffffff; font-family: 'Segoe UI'; font-weight: 600; padding: 12px; border-radius: 6px; font-size: 13px; text-align: left; padding-left: 15px; }
            QPushButton:hover { background-color: #1f2633; border-color: #45a29e; }
            QPushButton#btn_danger { color: #ff5252; border-color: #3d1c1c; }
            QPushButton#btn_danger:hover { background-color: #2b1313; border-color: #ff5252; }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 25, 20, 25)
        
        chk_auto_save = QCheckBox("Salvar automaticamente (Customização)")
        chk_auto_save.setChecked(self.auto_save)
        chk_auto_save.stateChanged.connect(self.toggle_auto_save_from_checkbox)
        
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
        
        layout.addWidget(chk_auto_save)
        layout.addSpacing(10)
        layout.addWidget(btn_toolbox)
        layout.addWidget(btn_delete_toolbox)
        layout.addWidget(btn_presets)
        layout.addWidget(btn_color)
        layout.addWidget(btn_theme)
        layout.addWidget(btn_bg_image)
        
        btn_save_man = QPushButton("💾  Salvar Customização")
        btn_save_man.clicked.connect(lambda: [self.save_settings(force=True), dialog.accept()])
        layout.addWidget(btn_save_man)
        
        btn_reset = QPushButton("🔄  Restaurar Configurações Iniciais (Reset)")
        btn_reset.setObjectName("btn_danger")
        btn_reset.clicked.connect(lambda: [self.reset_to_defaults(), dialog.accept()])
        layout.addWidget(btn_reset)
        
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
            self.save_settings()
            dialog.accept()

    def open_color_picker(self):
        color = QColorDialog.getColor(QColor(self.accent_color), self, "Escolha sua Cor de Destaque")
        if color.isValid():
            self.accent_color = color.name()
            self.apply_styles()
            self.create_home_tab()
            self.save_settings()

    def open_theme_picker(self):
        color = QColorDialog.getColor(QColor(self.theme_base_color), self, "Escolha a Cor do Fundo Geral")
        if color.isValid():
            self.theme_base_color = color.name()
            self.apply_styles()
            self.create_home_tab()
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
            self.save_settings()
            dialog.accept()

    def remove_background_image(self, dialog):
        self.background_image_path = ""
        self.home_widget.setAutoFillBackground(False)
        self.create_home_tab()
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
            self.buttons_list.append({"label": name, "url": url, "favorite": False})
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
        target_item = next((b for b in self.buttons_list if b["label"] == target_label), None)
        if target_item:
            self.buttons_list.remove(target_item)
        max_pages = max(0, (len(self.buttons_list) - 1) // self.items_per_page)
        if self.current_page > max_pages:
            self.current_page = max_pages
        self.save_settings(force=True)  
        self.create_home_tab()
        self.update_favorites_panel()
        dialog.accept()

    def save_settings(self, force=False):
        if self.is_restoring:
            return
        if not self.auto_save and not force:
            return
        self.track_zoom_levels()

        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        data = {
            "auto_save": self.auto_save,
            "save_tabs_enabled": self.save_tabs_enabled,
            "accent_color": self.accent_color,
            "theme_base_color": self.theme_base_color,
            "background_image_path": self.background_image_path,
            "buttons": self.buttons_list,
            "opened_tabs": self.opened_tabs_urls if self.save_tabs_enabled else [],
            "zoom_settings": self.zoom_settings
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.auto_save = data.get("auto_save", False)
                    self.save_tabs_enabled = data.get("save_tabs_enabled", False)
                    self.accent_color = data.get("accent_color", "#d9d9d9")
                    self.theme_base_color = data.get("theme_base_color", "#242120")
                    self.background_image_path = data.get("background_image_path", "")
                    self.buttons_list = data.get("buttons", self.default_buttons.copy())
                    
                    for b in self.buttons_list:
                        if "favorite" not in b:
                            b["favorite"] = False
                            
                    self.opened_tabs_urls = data.get("opened_tabs", [])
                    self.zoom_settings = data.get("zoom_settings", {})
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
        self.save_tabs_enabled = False
        self.opened_tabs_urls = []
        self.zoom_settings = {}
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        self.home_widget.setAutoFillBackground(False)
        self.apply_styles()
        self.create_home_tab()
        self.update_favorites_panel()

    def open_web_tab(self, url, title):
        self.search_filter = ""
        if hasattr(self, 'search_bar') and self.search_bar:
            self.search_bar.blockSignals(True)
            self.search_bar.clear()
            self.search_bar.blockSignals(False)
            self.search_bar.clearFocus() 
            
        browser = QWebEngineView(self)
        browser.setPage(browser.page().__class__(self.profile, browser))
        browser.setProperty("original_url", url)
        browser.setUrl(QUrl(url))
        browser.page().zoomFactorChanged.connect(lambda factor, b=browser: self.on_zoom_changed(b, factor))
        browser.loadFinished.connect(lambda ok, b=browser: self.apply_whatsapp_theme_on_load(b))
        browser.page().permissionRequested.connect(self.handle_permission_request)
        
        if url in self.zoom_settings:
            browser.setZoomFactor(self.zoom_settings[url])
            
        index = self.tabs.addTab(browser, title)
        self.tabs.setCurrentIndex(index)
        
        if self.save_tabs_enabled and not self.is_restoring:
            self.opened_tabs_urls.append({"label": title, "url": url})
            self.save_settings(force=True)

    def apply_whatsapp_theme_on_load(self, browser):
        url = browser.url().toString()
        if "whatsapp.com" in url:
            c_theme = QColor(self.theme_base_color)
            is_light = c_theme.lightness() > 128
            js_script = f"""
            (function() {{
                const isLight = {str(is_light).lower()};
                if (isLight) {{
                    document.body.classList.remove('theme-dark');
                    document.body.classList.add('theme-light');
                    document.documentElement.style.colorScheme = 'light';
                }} else {{
                    document.body.classList.remove('theme-light');
                    document.body.classList.add('theme-dark');
                    document.documentElement.style.colorScheme = 'dark';
                }}
            }})();
            """
            browser.page().runJavaScript(js_script)

    def sync_all_whatsapp_themes(self):
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                self.apply_whatsapp_theme_on_load(widget)

    def on_zoom_changed(self, browser, factor):
        try:
            url = browser.property("original_url") or browser.url().toString()
            if url and url != "about:blank":
                self.zoom_settings[url] = factor
                if self.save_tabs_enabled:
                    self.save_settings(force=True)
        except RuntimeError:
            pass

    def track_zoom_levels(self):
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                url = widget.property("original_url") or widget.url().toString()
                if url and url != "about:blank":
                    self.zoom_settings[url] = widget.zoomFactor()

    def close_tab(self, index):
        if index != 0:
            if self.save_tabs_enabled and not self.is_restoring:
                tab_title = self.tabs.tabText(index)
                self.opened_tabs_urls = [t for t in self.opened_tabs_urls if t["label"] != tab_title]
                
            widget = self.tabs.widget(index)
            if widget:
                widget.deleteLater()
            self.tabs.removeTab(index)
            if self.save_tabs_enabled and not self.is_restoring:
                self.save_settings(force=True)

    def track_tabs_after_move(self):
        if not self.save_tabs_enabled or self.is_restoring:
            return
        urls = []
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                saved_url = widget.property("original_url") or widget.url().toString()
                urls.append({"label": self.tabs.tabText(i), "url": saved_url})
        self.opened_tabs_urls = urls
        self.save_settings(force=True)

    def rebuild_tabs_list_manually(self):
        urls = []
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                saved_url = widget.property("original_url") or widget.url().toString()
                urls.append({"label": self.tabs.tabText(i), "url": saved_url})
        self.opened_tabs_urls = urls

    def restore_tabs(self):
        if self.save_tabs_enabled and self.opened_tabs_urls:
            self.is_restoring = True
            tabs_to_open = list(self.opened_tabs_urls)
            for t in tabs_to_open:
                self.open_web_tab(t["url"], t["label"])
            QTimer.singleShot(200, self.release_restore_lock)

    def release_restore_lock(self):
        self.is_restoring = False
        self.tabs.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StandaloneHub()
    window.show()
    sys.exit(app.exec())