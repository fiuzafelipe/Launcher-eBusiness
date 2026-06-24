import os
import sys
import json
import gc
import datetime
import re
from core.config_manager import ConfigManager
from PyQt6.QtWidgets import (QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QSpacerItem, QSizePolicy, QDialog, 
                             QLineEdit, QLabel, QCheckBox, QFormLayout, QComboBox,
                             QFileDialog, QColorDialog, QMessageBox, QScrollArea, QMenu, QGraphicsBlurEffect,
                             QStackedLayout)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage, QWebEngineSettings, 
                                   QWebEnginePermission, QWebEngineDownloadRequest)
from PyQt6.QtCore import QUrl, Qt, QPoint, QTimer, QRect, QEvent, QPointF
from PyQt6.QtGui import QIcon, QColor, QImage, QShortcut, QKeySequence, QCursor, QPixmap, QPainter, QPainterPath, QPen

# Importações dos módulos customizados
from ui.components import (SecuritySetupDialog, SecurityModifyDialog, SecurityChangePasswordDialog, 
                           HistoryDialog, DraggableToolButton, CustomTabWidget, LockScreenWidget)
from core.remote_tools import launch_remote_tool

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =========================================================================================
# A MÁGICA DA RAM ZERO: FÍSICA DE CABOS USB VETORIAIS
# =========================================================================================
class CableNetworkWidget(QWidget):
    def __init__(self, parent_hub, parent=None):
        super().__init__(parent)
        self.parent_hub = parent_hub
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent; border-image: none;")
        
        # O Motor da Animação: Extremamente leve (~40ms = 25 FPS). Consumo imperceptível.
        self.dash_offset = 0
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(40) 

    def update_animation(self):
        # A ilusão de ótica: empurramos o tracejado para criar movimento.
        # O % 15 previne que o número cresça ao infinito e estoure a memória (15 = 5 linha + 10 vazio)
        self.dash_offset = (self.dash_offset - 1) % 15 
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        layout = self.parent_hub.grid_layout
        if not layout or layout.count() < 2: return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        accent_color = QColor(self.parent_hub.accent_color)
        
        centers = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if w.isVisible():
                    # Mapeia o centro do botão para o widget de cabos
                    pos = w.mapTo(self, QPoint(w.width()//2, w.height()//2))
                    centers.append(pos)
        
        if len(centers) < 2:
            painter.end()
            return

        cable_color = QColor(10, 10, 15, 160) 
        base_pen = QPen(cable_color, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        
        pulse_pen = QPen(accent_color, 2, Qt.PenStyle.CustomDashLine, Qt.PenCapStyle.RoundCap)
        pulse_pen.setDashPattern([5, 10]) 
        pulse_pen.setDashOffset(self.dash_offset)
        
        for i in range(len(centers)-1):
            # A CORREÇÃO ESTÁ AQUI: Convertemos para QPointF
            p1 = QPointF(centers[i])
            p2 = QPointF(centers[i+1])
            
            path = QPainterPath()
            path.moveTo(p1)
            
            # Cálculo de gravidade suave
            if abs(p1.y() - p2.y()) < 20: 
                cp1 = QPointF(p1.x() + (p2.x() - p1.x()) / 3, p1.y() + 60)
                cp2 = QPointF(p2.x() - (p2.x() - p1.x()) / 3, p2.y() + 60)
            else:
                cp1 = QPointF(p1.x() + 100, p1.y() + 80)
                cp2 = QPointF(p2.x() - 100, p2.y() - 80)
                
            path.cubicTo(cp1, cp2, p2)
            
            painter.setPen(base_pen)
            painter.drawPath(path)
            
            painter.setPen(pulse_pen)
            painter.drawPath(path)
            
        painter.end()


# =========================================================================================
# APLICAÇÃO PRINCIPAL
# =========================================================================================
class StandaloneHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fiuza Standalone Hub v1.0")
        self.resize(1280, 720)
        
        self.config_file = os.path.join(current_dir, "core", "config.json")
        self.config_manager = ConfigManager(self.config_file)
        self.icons_dir = os.path.join(os.path.dirname(current_dir), "assets", "icons")
        os.makedirs(self.icons_dir, exist_ok=True)
        
        self.default_buttons = [
            {"label": "Contako", "subtitle": "Chat de atendimento", "url": "https://atendimento.contako.com.br/", "favorite": False},
            {"label": "Tickets", "subtitle": "Ticket chamados", "url": "https://raphanet.confirm8.com/tickets", "favorite": False},
            {"label": "Confirm8", "subtitle": "Novo chamado", "url": "https://raphanet.confirm8.com/tickets/new", "favorite": False},
            {"label": "WhatsApp", "subtitle": "Mensagens Web", "url": "https://web.whatsapp.com/", "favorite": False},
            {"label": "Ticket Socin", "subtitle": "Suporte Socin", "url": "https://socin.movidesk.com/", "favorite": False},
            {"label": "Ticket Skyone", "subtitle": "Suporte Skyone", "url": "https://console.skyone.cloud/", "favorite": False},
            {"label": "Google Keep", "subtitle": "Suas anotações", "url": "https://keep.google.com/", "favorite": False},
            {"label": "AnyDesk / Remoto", "subtitle": "Acesso Remoto", "url": "remote://anydesk", "favorite": False}
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
        self.pinned_tabs = []
        self.zoom_settings = {}
        self.security_settings = {}
        self.history_data = {}
        self.current_page = 0
        self.items_per_page = 8
        self.is_restoring = False  
        self.search_filter = ""
        self.is_wp_light = False 
        
        self.theme_mode = "Escuro"
        self.accent_color = self.presets["Padrão (preto/branco)"]["accent"]       
        self.theme_base_color = self.presets["Padrão (preto/branco)"]["theme"]   
        self.background_image_path = "" 

        self.load_settings()

        app_data = os.getenv('LOCALAPPDATA')
        self.storage_path = os.path.join(app_data, "FiuzaTechnology", "StandaloneHub", "BrowserSession")
        os.makedirs(self.storage_path, exist_ok=True)

        self.profile = QWebEngineProfile("FiuzaProfile", self)
        self.profile.setPersistentStoragePath(self.storage_path)
        self.profile.setCachePath(self.storage_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.profile.setHttpCacheMaximumSize(104857600) 
        self.profile.downloadRequested.connect(self.handle_download_request)
        
        settings = self.profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        
        edge_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
        self.profile.setHttpUserAgent(edge_ua)
        self.profile.setHttpAcceptLanguage("pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7")

        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.tabs = CustomTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.optimize_memory_without_reload)
        
        self.tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)
        
        self.corner_widget = QWidget()
        self.corner_widget.setObjectName("CornerWidget")
        corner_layout = QHBoxLayout(self.corner_widget)
        corner_layout.setContentsMargins(5, 2, 5, 2)
        corner_layout.setSpacing(5)
        
        icons_vbox = QVBoxLayout()
        icons_vbox.setContentsMargins(0, 0, 0, 0)
        icons_vbox.setSpacing(2)
        
        self.btn_direct_nav = QPushButton("🔗")
        self.btn_direct_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_direct_nav.setFixedSize(22, 22)
        self.btn_direct_nav.clicked.connect(self.open_direct_nav_dialog)
        
        self.btn_search_fav = QPushButton("🔍")
        self.btn_search_fav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search_fav.setFixedSize(22, 22)
        self.btn_search_fav.clicked.connect(self.toggle_fav_search)
        
        icons_vbox.addWidget(self.btn_direct_nav)
        icons_vbox.addWidget(self.btn_search_fav)
        
        self.fav_search_bar = QLineEdit()
        self.fav_search_bar.setPlaceholderText("Buscar favorito...")
        self.fav_search_bar.setFixedWidth(130)
        self.fav_search_bar.setFixedHeight(28)
        self.fav_search_bar.setVisible(False)
        self.fav_search_bar.textChanged.connect(self.filter_favorites)
        
        corner_layout.addLayout(icons_vbox)
        corner_layout.addWidget(self.fav_search_bar, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.tabs.setCornerWidget(self.corner_widget, Qt.Corner.TopLeftCorner)
        self.main_layout.addWidget(self.tabs)
        
        self.bottom_bar_widget = QWidget()
        self.bottom_bar_widget.setObjectName("BottomBar")
        self.bottom_bar_widget.setFixedHeight(45)
        self.bottom_bar_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.bottom_bar = QHBoxLayout(self.bottom_bar_widget)
        self.bottom_bar.setContentsMargins(15, 5, 15, 10)
        
        self.lbl_status = QLabel("")
        self.btn_save_session = QPushButton("Save")
        self.btn_save_session.setFixedSize(100, 30)
        self.btn_save_session.clicked.connect(self.trigger_save_tabs_button)
        
        self.bottom_bar.addWidget(self.lbl_status)
        self.bottom_bar.addStretch()
        self.bottom_bar.addWidget(self.btn_save_session)
        self.main_layout.addWidget(self.bottom_bar_widget)
        
        self.create_home_tab()
        self.apply_styles()
        
        QTimer.singleShot(100, self.restore_tabs)
        
        self.tabs.tabBar().setMouseTracking(True)
        self.tabs.tabBar().installEventFilter(self)

        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.setInterval(200)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position_for_favorites)
        self.mouse_check_timer.start()

        self.shortcut_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_right.activated.connect(self.safe_next_page)
        self.shortcut_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_left.activated.connect(self.safe_prev_page)
        self.shortcut_esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.shortcut_esc.activated.connect(self.safe_close_search)

        self.showMaximized()
        
        if self.security_settings and self.security_settings.get("enabled", False):
            self.show_lock_screen()

    def show_tab_context_menu(self, pos):
        index = self.tabs.tabBar().tabAt(pos)
        if index <= 0: return 
        
        widget = self.tabs.widget(index)
        if not isinstance(widget, QWebEngineView): return
        
        is_pinned = widget.property("is_pinned")
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: #161b24; color: #fff; border: 1px solid {self.accent_color}; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; border-radius: 4px; padding: 5px; border-image: none; }}
            QMenu::item {{ padding: 8px 25px; border-radius: 4px; border-image: none; }}
            QMenu::item:selected {{ background-color: {self.accent_color}; color: #000; }}
        """)
        
        if is_pinned:
            action_unpin = menu.addAction("❌ Desfixar Aba")
            action = menu.exec(self.tabs.tabBar().mapToGlobal(pos))
            if action == action_unpin:
                widget.setProperty("is_pinned", False)
                raw_label = widget.property("original_label") or "Navegação"
                self.tabs.setTabText(index, raw_label[:20] + ("..." if len(raw_label)>20 else ""))
                self.save_settings(force=True)
        else:
            action_pin = menu.addAction("📌 Fixar Aba")
            action = menu.exec(self.tabs.tabBar().mapToGlobal(pos))
            if action == action_pin:
                widget.setProperty("is_pinned", True)
                raw_label = widget.property("original_label") or "Navegação"
                self.tabs.setTabText(index, "📌 " + raw_label[:18] + ("..." if len(raw_label)>18 else ""))
                self.save_settings(force=True)

    def closeEvent(self, event):
        self.save_settings(force=True)
        if hasattr(self, 'profile'):
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        event.accept()

    def show_lock_screen(self):
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(20)
        self.centralWidget().setGraphicsEffect(self.blur_effect)
        self.lock_screen = LockScreenWidget(self, self.security_settings)
        self.lock_screen.setGeometry(self.rect())
        self.lock_screen.show()
        self.lock_screen.raise_()

    def contextMenuEvent(self, event):
        if self.tabs.currentIndex() == 0:
            menu = QMenu(self)
            menu.setStyleSheet(f"""
                QMenu {{ background-color: #161b24; color: #fff; border: 1px solid {self.accent_color}; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; border-radius: 4px; padding: 5px; border-image: none; }}
                QMenu::item {{ padding: 8px 25px; border-radius: 4px; border-image: none; }}
                QMenu::item:selected {{ background-color: {self.accent_color}; color: #000; }}
            """)
            history_action = menu.addAction("🕒 Histórico")
            lock_action = None
            if self.security_settings.get("enabled", False):
                lock_action = menu.addAction("🔒 Trancar Tela")
            action = menu.exec(self.mapToGlobal(event.pos()))
            
            if action == history_action:
                dialog = HistoryDialog(self)
                dialog.exec()
            elif lock_action and action == lock_action:
                self.show_lock_screen()
        else:
            super().contextMenuEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'lock_screen') and self.lock_screen.isVisible():
            self.lock_screen.setGeometry(self.rect())

    def toggle_fav_search(self):
        is_visible = self.fav_search_bar.isVisible()
        self.fav_search_bar.setVisible(not is_visible)
        if not is_visible:
            self.fav_search_bar.setFocus()
            self.show_fav_panel()
        else:
            self.fav_search_bar.clear()
            self.hide_fav_panel()

    def safe_close_search(self):
        if hasattr(self, 'fav_search_bar') and self.fav_search_bar.isVisible():
            self.toggle_fav_search()

    def filter_favorites(self, text):
        self.update_favorites_panel(text)

    def safe_next_page(self):
        if self.tabs.currentIndex() == 0:
            if hasattr(self, 'search_bar') and self.search_bar.hasFocus(): return
            if hasattr(self, 'fav_search_bar') and self.fav_search_bar.hasFocus(): return
            self.next_page()

    def safe_prev_page(self):
        if self.tabs.currentIndex() == 0:
            if hasattr(self, 'search_bar') and self.search_bar.hasFocus(): return
            if hasattr(self, 'fav_search_bar') and self.fav_search_bar.hasFocus(): return
            self.prev_page()

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

    def update_wallpaper_brightness(self):
        self.is_wp_light = False
        if hasattr(self, 'background_image_path') and self.background_image_path and os.path.exists(self.background_image_path):
            try:
                img = QImage(self.background_image_path).scaled(50, 50, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
                lum = sum((img.pixelColor(x, y).red() * 0.299 + img.pixelColor(x, y).green() * 0.587 + img.pixelColor(x, y).blue() * 0.114) for x in range(50) for y in range(50)) / 2500
                self.is_wp_light = lum > 128
            except: pass

    def get_active_theme_color(self):
        c = QColor(self.theme_base_color)
        if getattr(self, 'theme_mode', 'Escuro') == "Claro":
            return QColor.fromHsl(c.hue(), min(c.saturation(), 60), 240).name()
        else:
            return QColor.fromHsl(c.hue(), c.saturation(), min(c.lightness(), 25)).name()

    def show_about_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Sobre o Standalone Hub")
        dialog.setFixedSize(400, 150)
        dialog.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid #232a38; border-image: none; }}
            QLabel {{ color: {self.accent_color}; font-family: 'Segoe UI'; font-size: 15px; font-weight: bold; text-align: center; border-image: none; }}
            QPushButton {{ background-color: #161b24; border: 1px solid #232a38; color: #fff; padding: 8px; border-radius: 4px; font-weight: bold; font-family: 'Segoe UI'; font-size: 13px; width: 100px; border-image: none; }}
            QPushButton:hover {{ background-color: {self.accent_color}; color: #000; border-color: {self.accent_color}; }}
        """)
        layout = QVBoxLayout(dialog)
        lbl = QLabel("Aplicação desenvolvida por Felipe Fiuza!\nBom uso.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        layout.addStretch()
        layout.addWidget(lbl)
        layout.addSpacing(15)
        layout.addLayout(btn_layout)
        layout.addStretch()
        dialog.exec()

    def process_and_save_icon(self, source_path, name):
        dest_path = os.path.join(self.icons_dir, f"{name.lower()}.png")
        image = QImage(source_path)
        if not image.isNull():
            image = image.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image = image.convertToFormat(QImage.Format.Format_ARGB32)
            bg_color = image.pixelColor(0, 0)
            tolerance = 25
            for y in range(image.height()):
                for x in range(image.width()):
                    pixel_color = image.pixelColor(x, y)
                    if (abs(pixel_color.red() - bg_color.red()) <= tolerance and
                        abs(pixel_color.green() - bg_color.green()) <= tolerance and
                        abs(pixel_color.blue() - bg_color.blue()) <= tolerance):
                        image.setPixelColor(x, y, QColor(0, 0, 0, 0)) 
            image.save(dest_path, "PNG")

    def edit_button_dialog(self, item_data):
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Botão")
        dialog.setFixedWidth(420)
        dialog.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid #1c212d; border-image: none; }}
            QLabel {{ color: #a0a5b5; font-family: 'Segoe UI'; font-size: 12px; font-weight: bold; border-image: none; }}
            QLineEdit {{ background-color: #161b24; border: 1px solid {self.accent_color}; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; border-image: none; }}
            QLineEdit:focus {{ border: 1px solid {self.accent_color}; }}
            QPushButton {{ font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; border-image: none; }}
        """)
        form_layout = QFormLayout(dialog)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        old_name = item_data["label"]
        input_name = QLineEdit(item_data["label"])
        input_subtitle = QLineEdit(item_data.get("subtitle", ""))
        input_url = QLineEdit(item_data["url"])
        btn_img = QPushButton("🖼️ Alterar Imagem")
        btn_img.setStyleSheet("background-color: #161b24; border: 1px solid #232a38; color: #fff; text-align: center;")
        selected_img = [""]
        def pick_img():
            path, _ = QFileDialog.getOpenFileName(dialog, "Selecionar Ícone", "", "Images (*.png *.jpg *.jpeg)")
            if path:
                selected_img[0] = path
                btn_img.setText("Imagem Selecionada!")
                btn_img.setStyleSheet(f"background-color: {self.accent_color}; color: #000; font-weight: bold; border: none;")
        btn_img.clicked.connect(pick_img)
        form_layout.addRow(QLabel("Nome do Botão:"), input_name)
        form_layout.addRow(QLabel("Nome do Subtítulo:"), input_subtitle)
        form_layout.addRow(QLabel("URL do Site:"), input_url)
        form_layout.addRow(btn_img)
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Salvar")
        btn_save.setStyleSheet(f"background-color: {self.accent_color}; color: #07080a; text-align: center; padding-left: 0;")
        btn_back = QPushButton("Cancelar")
        btn_back.setStyleSheet("background-color: #161b24; border: 1px solid #232a38; color: #fff; text-align: center; padding-left: 0;")
        def save_edit():
            new_name = input_name.text().strip()
            new_sub = input_subtitle.text().strip()
            new_url = input_url.text().strip()
            if new_name and new_url:
                if selected_img[0]:
                    self.process_and_save_icon(selected_img[0], new_name)
                    if old_name.lower() != new_name.lower():
                        old_icon = os.path.join(self.icons_dir, f"{old_name.lower()}.png")
                        if os.path.exists(old_icon):
                            try: os.remove(old_icon)
                            except: pass
                elif old_name.lower() != new_name.lower():
                    old_icon = os.path.join(self.icons_dir, f"{old_name.lower()}.png")
                    new_icon = os.path.join(self.icons_dir, f"{new_name.lower()}.png")
                    if os.path.exists(old_icon):
                        try: os.rename(old_icon, new_icon)
                        except: pass
                item_data["label"] = new_name
                item_data["subtitle"] = new_sub
                item_data["url"] = new_url
                self.save_settings(force=True)
                self.filter_buttons_by_search(self.search_filter)
                dialog.accept()
        btn_save.clicked.connect(save_edit)
        btn_back.clicked.connect(dialog.reject)
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_back)
        form_layout.addRow(btn_box)
        dialog.exec()

    def optimize_memory_without_reload(self, index):
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                if i != index:
                    widget.setVisible(False)
                else:
                    widget.setVisible(True)
                    if widget.property("needs_load"):
                        widget.setProperty("needs_load", False)
                        url = widget.property("original_url")
                        widget.setUrl(QUrl(url))
                        if url in self.zoom_settings:
                            widget.setZoomFactor(self.zoom_settings[url])
        gc.collect()

    def open_direct_nav_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Navegador Rápido")
        dialog.setFixedWidth(450)
        dialog.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid #232a38; border-radius: 8px; border-image: none; }}
            QLabel {{ color: {self.accent_color}; font-family: 'Segoe UI'; font-weight: bold; font-size: 13px; border-image: none; }}
            QLineEdit {{ background-color: #161b24; border: 1px solid #232a38; color: #fff; padding: 12px; border-radius: 6px; font-size: 13px; border-image: none; }}
            QLineEdit:focus {{ border: 1px solid {self.accent_color}; }}
            QPushButton {{ background-color: {self.accent_color}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; font-size: 13px; border-image: none; }}
            QPushButton:hover {{ opacity: 0.8; }}
            QPushButton#btn_cancel {{ background-color: #161b24; color: #fff; border: 1px solid #232a38; }}
        """)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        lbl = QLabel("🌐 Digite a URL:")
        input_url = QLineEdit()
        input_url.setPlaceholderText("Exemplo: google.com.br")
        btn_layout = QHBoxLayout()
        btn_go = QPushButton("Acessar")
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_cancel")
        btn_go.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        input_url.returnPressed.connect(dialog.accept)
        btn_layout.addWidget(btn_go)
        btn_layout.addWidget(btn_cancel)
        layout.addWidget(lbl)
        layout.addWidget(input_url)
        layout.addLayout(btn_layout)
        if dialog.exec() == QDialog.DialogCode.Accepted and input_url.text().strip():
            url = input_url.text().strip()
            if not url.startswith("http://") and not url.startswith("https://"): url = "https://" + url
            self.open_web_tab(url, "Carregando...")

    def update_favorites_panel(self, filter_text=""):
        if not hasattr(self, 'fav_hbox') or not self.fav_hbox: return
        
        while self.fav_hbox.count():
            item = self.fav_hbox.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            
        fav_items = [b for b in self.buttons_list if b.get("favorite", False)]
        if filter_text:
            fav_items = [b for b in fav_items if filter_text.strip().lower() in b["label"].lower()]
            
        c_accent = QColor(self.accent_color)
        bg_rgba = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.85)"
            
        for item in fav_items:
            btn = QPushButton(item["label"])
            btn.setObjectName("FavItemBtn")
            btn.setFixedSize(140, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            btn.setStyleSheet(f"""
                QPushButton#FavItemBtn {{ 
                    background-color: {bg_rgba}; 
                    border: 1px solid rgba(0,0,0,0.5); 
                    color: #07080a; 
                    font-size: 12px; 
                    font-weight: bold; 
                    border-radius: 4px; 
                    border-image: none !important;
                }}
                QPushButton#FavItemBtn:hover {{ 
                    background-color: {self.accent_color}; 
                }}
            """)
            btn.clicked.connect(lambda checked, u=item["url"], l=item["label"]: self.open_web_tab(u, l))
            self.fav_hbox.addWidget(btn)
            btn.show() 
            
        self.fav_hbox.addStretch()

    def show_fav_panel(self):
        if hasattr(self, 'fav_area_layout'):
            if self.fav_area_layout.currentWidget() != self.fav_panel_widget:
                self.update_favorites_panel(self.fav_search_bar.text())
                self.fav_area_layout.setCurrentWidget(self.fav_panel_widget)

    def hide_fav_panel(self):
        if hasattr(self, 'fav_area_layout'):
            if self.fav_area_layout.currentWidget() == self.fav_panel_widget:
                if hasattr(self, 'fav_search_bar') and self.fav_search_bar.isVisible() and self.fav_search_bar.hasFocus(): return
                self.fav_area_layout.setCurrentWidget(self.fav_placeholder)

    def check_mouse_position_for_favorites(self):
        if not hasattr(self, 'home_widget') or not self.home_widget: return
        if self.tabs.currentIndex() != 0: 
            self.hide_fav_panel()
            return
            
        has_favs = any(b.get("favorite", False) for b in self.buttons_list)
        if not has_favs:
            self.hide_fav_panel()
            return
            
        if hasattr(self, 'fav_search_bar') and self.fav_search_bar.isVisible() and self.fav_search_bar.hasFocus():
            self.show_fav_panel()
            return
            
        global_cursor_pos = QCursor.pos()
        cursor_pos = self.mapFromGlobal(global_cursor_pos)
        
        if cursor_pos.y() >= 0 and cursor_pos.y() <= 95:
            self.show_fav_panel()
        else:
            self.hide_fav_panel()

    def eventFilter(self, obj, event):
        if obj == self.tabs.tabBar():
            if event.type() == QEvent.Type.MouseMove:
                if self.tabs.currentIndex() == 0:
                    has_favs = any(b.get("favorite", False) for b in self.buttons_list)
                    if has_favs: self.show_fav_panel()
        return super().eventFilter(obj, event)

    def delete_button_by_data(self, item_data):
        self.buttons_list = [b for b in self.buttons_list if b != item_data]
        icon_path = os.path.join(self.icons_dir, f"{item_data['label'].lower()}.png")
        if os.path.exists(icon_path):
            try: os.remove(icon_path)
            except: pass
        self.save_settings(force=True)
        self.filter_buttons_by_search(self.search_filter)
        self.update_favorites_panel()

    def handle_permission_request(self, request: QWebEnginePermission):
        request.grant()

    def handle_download_request(self, download: QWebEngineDownloadRequest):
        default_name = download.downloadFileName()
        if not default_name: default_name = "download_midia"
        download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        suggested_path = os.path.join(download_dir, default_name)
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

    def create_home_tab(self):
        if hasattr(self, 'home_widget') and self.home_widget:
            self.tabs.removeTab(0)
            self.home_widget.deleteLater()

        self.home_widget = QWidget()
        self.home_widget.setObjectName("HomeTab")
        self.home_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.home_widget.setStyleSheet("background-color: transparent;")

        home_vertical_layout = QVBoxLayout(self.home_widget)
        home_vertical_layout.setContentsMargins(0, 0, 0, 0)
        home_vertical_layout.setSpacing(0)
        
        self.fav_area = QWidget()
        self.fav_area.setObjectName("FavArea")
        self.fav_area.setFixedHeight(45) 
        self.fav_area.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.fav_area_layout = QStackedLayout(self.fav_area)
        self.fav_area_layout.setContentsMargins(0,0,0,0)

        self.fav_placeholder = QWidget()
        self.fav_placeholder.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.fav_placeholder.setStyleSheet("background: transparent; border-image: none;")
        
        self.fav_panel_widget = QWidget()
        self.fav_panel_widget.setObjectName("FavPanelWidget")
        self.fav_panel_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.fav_hbox = QHBoxLayout(self.fav_panel_widget)
        self.fav_hbox.setContentsMargins(15, 0, 15, 0)
        self.fav_hbox.setSpacing(10)

        self.fav_area_layout.addWidget(self.fav_placeholder) 
        self.fav_area_layout.addWidget(self.fav_panel_widget) 
        self.fav_area_layout.setCurrentWidget(self.fav_placeholder)
        
        home_vertical_layout.addWidget(self.fav_area)
        
        # INJEÇÃO DA NOSSA PLACA DE CIRCUITO INVISÍVEL
        self.grid_container_widget = CableNetworkWidget(self)
        content_layout = QVBoxLayout(self.grid_container_widget)
        content_layout.setContentsMargins(40, 15, 40, 25)
        
        control_panel_layout = QVBoxLayout()
        control_panel_layout.setSpacing(10)
        
        has_wp = hasattr(self, 'background_image_path') and self.background_image_path and os.path.exists(self.background_image_path)
        text_color = "#111111" if getattr(self, 'is_wp_light', False) else "#f5f5f5"
        
        c_accent = QColor(self.accent_color)
        c_theme = QColor(self.get_active_theme_color())
        
        if has_wp:
            input_bg = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.5)"
            input_text = text_color
            font_weight = "600"
            page_color = text_color
        else:
            is_light = c_theme.lightness() > 128
            input_bg = "rgba(255, 255, 255, 0.1)" if not is_light else "rgba(0, 0, 0, 0.05)"
            input_text = "#ffffff" if not is_light else "#07080a"
            font_weight = "bold"
            page_color = "#07080a" if is_light else "#ffffff"

        btn_ops = QPushButton("STANDALONE HUB")
        btn_ops.setObjectName("btn_ops")
        btn_ops.setFixedSize(450, 42)
        btn_ops.clicked.connect(self.show_about_dialog)
        
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
        
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{ background-color: {input_bg}; border: 1px solid rgba(0, 0, 0, 0.6); border-radius: 6px; color: {input_text}; font-family: 'Segoe UI'; font-size: 13px; font-weight: {font_weight}; padding-left: 15px; padding-right: 15px; border-image: none; }}
            QLineEdit:focus {{ border: 2px solid {self.accent_color}; }}
        """)
        
        control_panel_layout.addWidget(btn_ops, alignment=Qt.AlignmentFlag.AlignCenter)
        control_panel_layout.addWidget(btn_config_menu, alignment=Qt.AlignmentFlag.AlignCenter)
        control_panel_layout.addWidget(self.search_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addLayout(control_panel_layout)
        content_layout.addSpacing(20)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(25)
        
        grid_container_hbox = QHBoxLayout()
        grid_container_hbox.addStretch()
        grid_container_hbox.addLayout(self.grid_layout)
        grid_container_hbox.addStretch()
        content_layout.addLayout(grid_container_hbox)

        self.nav_container = QWidget()
        self.nav_container.setFixedHeight(45)
        nav_layout = QHBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.addStretch()
        
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"
        nav_style = f"""
            QPushButton {{ background-color: {self.accent_color}; border: 1px solid #000000; color: #07080a; font-weight: bold; font-size: 15px; border-radius: 5px; border-image: none; }}
            QPushButton:hover {{ background-color: {hover_dark_tint}; color: {self.accent_color}; border-color: {self.accent_color}; }}
            QPushButton:disabled {{ border: 1px solid rgba(0,0,0,0.1); color: rgba(120, 120, 120, 0.5); background-color: rgba(0, 0, 0, 0.15); }}
        """
        
        self.btn_prev_page = QPushButton("<")
        self.btn_prev_page.setFixedSize(60, 40)
        self.btn_prev_page.setStyleSheet(nav_style)
        self.btn_prev_page.clicked.connect(self.prev_page)
        
        self.page_label = QLabel(f"Página {self.current_page + 1}")
        self.page_label.setFixedWidth(80) 
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet(f"color: {page_color}; font-weight: {font_weight}; font-size: 14px; font-family: 'Segoe UI'; background: transparent; border-image: none;")
        
        self.btn_next_page = QPushButton(">")
        self.btn_next_page.setFixedSize(60, 40)
        self.btn_next_page.setStyleSheet(nav_style)
        self.btn_next_page.clicked.connect(self.next_page)
        
        nav_layout.addWidget(self.btn_prev_page)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.btn_next_page)
        nav_layout.addStretch()
        
        content_layout.addStretch()
        content_layout.addWidget(self.nav_container)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; border-image: none; }")
        scroll_area.setWidget(self.grid_container_widget)
        
        home_vertical_layout.addWidget(scroll_area)

        self.tabs.insertTab(0, self.home_widget, "Home")
        self.update_favorites_panel()
        self.filter_buttons_by_search(self.search_filter)
        
        if self.search_filter:
            self.search_bar.setFocus()
            self.search_bar.setSelection(len(self.search_filter), 0)

    def apply_styles(self):
        accent = self.accent_color
        c_accent = QColor(accent)
        main_bg = self.get_active_theme_color()
        c_theme = QColor(main_bg)
        
        is_light_theme = c_theme.lightness() > 128
        
        has_wp = hasattr(self, 'background_image_path') and self.background_image_path and os.path.exists(self.background_image_path)
        is_bg_light = getattr(self, 'is_wp_light', False)
        
        if has_wp:
            icon_col = "#111111" if is_bg_light else "#ffffff"
        else:
            icon_col = "#07080a" if is_light_theme else "#ffffff"
            
        self.btn_direct_nav.setStyleSheet(f"QPushButton {{ background: transparent; border: none; font-size: 14px; color: {icon_col}; border-image: none; }} QPushButton:hover {{ color: {accent}; }}")
        self.btn_search_fav.setStyleSheet(f"QPushButton {{ background: transparent; border: none; font-size: 14px; color: {icon_col}; border-image: none; }} QPushButton:hover {{ color: {accent}; }}")
        self.corner_widget.setStyleSheet("background: transparent; border-image: none;")
        
        search_bg = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.25)"
        text_search_fav = "#000000" if is_light_theme else "#ffffff"
        if has_wp:
            text_search_fav = "#111111" if is_bg_light else "#f5f5f5"
            
        self.fav_search_bar.setStyleSheet(f"""
            QLineEdit {{ background-color: {search_bg}; border: 1px solid {accent}; border-radius: 4px; color: {text_search_fav}; font-family: 'Segoe UI'; font-size: 12px; font-weight: bold; padding: 0 5px; }}
            QLineEdit:focus {{ background-color: rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.5); }}
        """)
        
        # A LINHA FORTE E UNIFICADA (Superior, 2px) e A LINHA FRACA COM A SUA COR DE DESTAQUE (Inferior, 1px)
        strong_line = f"2px solid {accent}"
        faint_line = f"1px solid rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.50)"
        
        if has_wp:
            bg_path = self.background_image_path.replace("\\", "/")
            main_bg_style = f"border-image: url('{bg_path}') 0 0 0 0 stretch stretch;"
            
            tab_text_color = "#1a1a1a" if is_bg_light else "#e0e0e0"
            tabbar_bg = "rgba(255, 255, 255, 0.35)" if is_bg_light else "rgba(0, 0, 0, 0.35)"
            tab_inactive_bg = "rgba(255, 255, 255, 0.15)" if is_bg_light else "rgba(0, 0, 0, 0.15)"
            tab_active_bg = "rgba(255, 255, 255, 0.85)" if is_bg_light else "rgba(20, 20, 20, 0.85)"
            
            pane_bg = "transparent"
            
            btn_ops_bg = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.5)"
            btn_ops_hover_bg = accent
            btn_ops_hover_text = "#07080a"
            
            text_color = "#111111" if is_bg_light else "#f5f5f5"
            font_weight = "600"
            bottom_bar_bg = btn_ops_bg
        else:
            solid_text_color = "#07080a" if is_light_theme else "#ffffff"
            tab_text_color = "#232a38" if is_light_theme else "#8a909d"
            top_bar_bg_solid = QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(30, c_theme.lightness() - 12)).name() if is_light_theme else QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(5, c_theme.lightness() - 8)).name()
            tab_inactive_bg_solid = QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(40, c_theme.lightness() - 20)).name() if is_light_theme else QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(10, c_theme.lightness() + 6)).name()
            
            main_bg_style = f"background-color: {top_bar_bg_solid}; border-image: none;"
            tabbar_bg = top_bar_bg_solid
            tab_inactive_bg = tab_inactive_bg_solid
            tab_active_bg = main_bg
            
            pane_bg = main_bg
            
            btn_ops_bg = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.08)"
            btn_ops_hover_bg = accent
            btn_ops_hover_text = "#07080a"
            
            text_color = solid_text_color
            font_weight = "bold"
            bottom_bar_bg = "transparent"

        self.lbl_status.setStyleSheet(f"color: {text_color}; font-family: 'Segoe UI'; font-weight: {font_weight}; font-size: 13px; background: transparent; border: none;")
        
        self.setStyleSheet(f"""
            QWidget#CentralWidget {{ {main_bg_style} }}
            
            /* A MÁGICA DA LINHA UNIFICADA (NUNCA DUPLA): Apenas o Painel ganha a linha superior grossa */
            QTabWidget::pane {{ border-top: {strong_line}; background: {pane_bg}; border-image: none; }}
            
            /* TabBar perde qualquer borda no fundo para não duplicar com o Painel! */
            QTabBar {{ background-color: {tabbar_bg}; border-bottom: none; border-image: none; qproperty-drawBase: 0; }}
            
            QTabBar::tab {{ background: {tab_inactive_bg}; color: {tab_text_color}; padding: 8px 24px 14px 24px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 3px; margin-top: 6px; border: 1px solid rgba(0,0,0,0.15); border-bottom: none; font-family: 'Segoe UI'; font-weight: 500; font-size: 12px; border-image: none; }}
            QTabBar::tab:selected {{ background: {tab_active_bg}; color: {accent}; font-weight: bold; border: 1px solid {accent}; border-bottom: none; margin-top: 2px; padding-bottom: 16px; border-image: none; }}
            QTabBar::close-button {{ subcontrol-position: right; margin-bottom: 4px; }}
            QTabBar::tab:first {{ qproperty-closable: false; }}
            
            /* A LINHA FRACA COM COR 1px SÓLIDO (Borda Inferior dos Favoritos) */
            QWidget#FavArea {{ border-image: none; background: transparent; }}
            QWidget#FavPanelWidget {{ background-color: rgba({c_theme.red()}, {c_theme.green()}, {c_theme.blue()}, 0.95); border-bottom: {faint_line}; border-top: none; border-image: none; }}
            QWidget#FavPanelWidget * {{ border-image: none; }}
            QWidget#HomeTab {{ border-image: none; background: transparent; }}
            
            QWidget#BottomBar {{ background-color: {bottom_bar_bg}; border-top: 1px solid rgba(0,0,0,0.2); }}
            
            QPushButton#btn_ops {{ background-color: {btn_ops_bg}; border: 1px solid {accent}; color: {text_color}; font-weight: {font_weight}; border-radius: 6px; font-size: 14px; font-family: 'Segoe UI'; letter-spacing: 1.5px; border-image: none; }}
            QPushButton#btn_ops:hover {{ background-color: {btn_ops_hover_bg}; color: {btn_ops_hover_text}; border: 1px solid #000000; }}
            
            QPushButton#btn_config_menu {{ background-color: {btn_ops_bg}; border: 1px solid {accent}; color: {text_color}; font-weight: {font_weight}; border-radius: 6px; font-size: 14px; font-family: 'Segoe UI'; letter-spacing: 0.5px; border-image: none; }}
            QPushButton#btn_config_menu:hover {{ background-color: {btn_ops_hover_bg}; color: {btn_ops_hover_text}; border: 1px solid #000000; }}
        """)
        
        self.update_save_tabs_button_visual()
        self.sync_all_whatsapp_themes()

    def update_save_tabs_button_visual(self):
        accent = self.accent_color
        c_accent = QColor(accent)
        has_wp = hasattr(self, 'background_image_path') and self.background_image_path and os.path.exists(self.background_image_path)
        
        if has_wp:
            btn_bg_off = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.5)"
            text_col = "#111111" if getattr(self, 'is_wp_light', False) else "#f5f5f5"
        else:
            btn_bg_off = "#161b24"
            text_col = "#8a909d"
            
        if self.save_tabs_enabled:
            self.btn_save_session.setStyleSheet(f"""
                QPushButton {{ background-color: {accent}; border: 1px solid #000000; color: #07080a; font-family: 'Segoe UI'; font-weight: bold; border-radius: 4px; margin: 0px; }}
            """)
            self.lbl_status.setText("Save abas ativado.")
        else:
            self.btn_save_session.setStyleSheet(f"""
                QPushButton {{ background-color: {btn_bg_off}; border: 1px solid rgba(0,0,0,0.5); color: {text_col}; font-family: 'Segoe UI'; font-weight: 600; border-radius: 4px; margin: 0px; }}
                QPushButton:hover {{ background-color: {accent}; border-color: #000000; color: #07080a; }}
            """)
            self.lbl_status.setText("")

    def trigger_save_tabs_button(self):
        self.save_tabs_enabled = not self.save_tabs_enabled
        self.update_save_tabs_button_visual()
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
        self.filter_buttons_by_search(self.search_filter)

    def filter_buttons_by_search(self, text):
        self.search_filter = text
        filtered_list = [b for b in self.buttons_list if self.search_filter.strip().lower() in b["label"].lower()]
        
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = filtered_list[start_idx:end_idx]
        
        row, col = 0, 0
        for i, item in enumerate(page_items):
            real_index = self.buttons_list.index(item)
            btn = DraggableToolButton(item_data=item, item_index=real_index, parent_hub=self)
            btn.setFixedSize(220, 145)
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

    def log_history(self, label, url):
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        
        if not hasattr(self, 'history_data'):
            self.history_data = {}
            
        if date_str not in self.history_data:
            self.history_data[date_str] = []
            
        self.history_data[date_str].insert(0, {"time": time_str, "label": label, "url": url})
        self.save_settings(force=True)

    def open_theme_mode_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Modo de Tema")
        dialog.setFixedWidth(350)
        dialog.setWindowOpacity(0.92)
        
        accent = self.accent_color
        c_accent = QColor(accent)
        text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"
        
        dialog.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {accent}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; }}
            QPushButton {{ background-color: {accent}; color: {text_color}; font-family: 'Segoe UI'; font-weight: 600; padding: 12px; border-radius: 6px; font-size: 13px; border: 1px solid #000000; text-align: left; padding-left: 20px; }}
            QPushButton:hover {{ background-color: {hover_dark_tint}; border-color: {accent}; color: {accent}; }}
        """)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(15)
        
        lbl = QLabel("Escolha a luminosidade da interface:")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        
        btn_escuro = QPushButton("🌙  Modo Escuro (Fundo Preto)")
        btn_claro = QPushButton("☀️  Modo Claro (Fundo Branco)")
        
        def set_mode(mode):
            self.theme_mode = mode
            self.apply_styles()
            self.create_home_tab()
            self.save_settings(force=True)
            dialog.accept()
            
        btn_escuro.clicked.connect(lambda: set_mode("Escuro"))
        btn_claro.clicked.connect(lambda: set_mode("Claro"))
        
        layout.addWidget(btn_escuro)
        layout.addWidget(btn_claro)
        dialog.exec()

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("CONFIGURAÇÕES DO SISTEMA")
        dialog.setFixedWidth(380)
        dialog.setWindowOpacity(0.92)
        
        accent = self.accent_color
        c_accent = QColor(accent)
        text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"

        dialog.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {accent}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; }}
            QCheckBox {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; padding: 5px; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; }}
            QPushButton {{ 
                background-color: {accent}; color: {text_color}; font-family: 'Segoe UI'; font-weight: 600; padding: 10px; border-radius: 6px; font-size: 13px; text-align: left; padding-left: 15px; border: 1px solid #000000;
            }}
            QPushButton:hover {{ background-color: {hover_dark_tint}; border-color: {accent}; color: {accent}; }}
            QPushButton#btn_danger {{ background-color: #ff5252; color: #ffffff; border: 1px solid #000000; }}
            QPushButton#btn_danger:hover {{ background-color: #3d1c1c; color: #ff5252; border-color: #ff5252; }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 25, 20, 25)
        
        chk_auto_save = QCheckBox("Salvar automaticamente")
        chk_auto_save.setChecked(self.auto_save)
        chk_auto_save.stateChanged.connect(self.toggle_auto_save_from_checkbox)
        
        if self.security_settings.get("enabled", False):
            btn_security = QPushButton("🔓  Alterar ou Remover Senha")
            btn_security.clicked.connect(lambda: [dialog.accept(), self.open_security_modify()])
        else:
            btn_security = QPushButton("🔒  Definir Senha de Acesso")
            btn_security.clicked.connect(lambda: [dialog.accept(), self.open_security_setup()])

        btn_mode = QPushButton("🌗  Modo Escuro / Claro (Base)")
        btn_mode.clicked.connect(lambda: [dialog.accept(), self.open_theme_mode_dialog()])
        
        btn_toolbox = QPushButton("＋  Adicionar Botão")
        btn_toolbox.clicked.connect(lambda: [dialog.accept(), self.open_toolbox_dialog()])
        
        btn_delete_toolbox = QPushButton("🗙  Deletar Botão")
        btn_delete_toolbox.clicked.connect(lambda: [dialog.accept(), self.open_delete_toolbox_dialog()])
        
        btn_presets = QPushButton("🎨  Temas Pré-definidos")
        btn_presets.clicked.connect(lambda: [dialog.accept(), self.open_presets_dialog()])
        
        btn_color = QPushButton("🎨  Alterar Cor de Destaque")
        btn_color.clicked.connect(lambda: [dialog.accept(), self.open_color_picker()])
        
        btn_theme = QPushButton("🎭  Alterar Cor do Fundo")
        btn_theme.clicked.connect(lambda: [dialog.accept(), self.open_theme_picker()])
        
        btn_bg_image = QPushButton("🖼️  Imagem de Fundo (Wallpaper)")
        btn_bg_image.clicked.connect(lambda: [dialog.accept(), self.open_background_dialog()])
        
        layout.addWidget(chk_auto_save)
        layout.addSpacing(10)
        layout.addWidget(btn_security)
        layout.addWidget(btn_mode)
        layout.addWidget(btn_toolbox)
        layout.addWidget(btn_delete_toolbox)
        layout.addWidget(btn_presets)
        layout.addWidget(btn_color)
        layout.addWidget(btn_theme)
        layout.addWidget(btn_bg_image)
        
        btn_save_man = QPushButton("💾  Salvar Customização")
        btn_save_man.clicked.connect(lambda: [self.save_settings(force=True), dialog.accept()])
        layout.addWidget(btn_save_man)
        
        btn_reset = QPushButton("🔄  Restaurar Padrões de Fábrica")
        btn_reset.setObjectName("btn_danger")
        btn_reset.clicked.connect(lambda: [self.reset_to_defaults(), dialog.accept()])
        layout.addWidget(btn_reset)
        
        dialog.exec()

    def open_security_setup(self):
        dialog = SecuritySetupDialog(self, self.security_settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.security_settings = dialog.final_data
            self.save_settings(force=True)

    def open_security_modify(self):
        dialog = SecurityModifyDialog(self)
        dialog.exec()

    def open_presets_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Selecionar Tema Pré-definido")
        dialog.setFixedWidth(380)
        dialog.setWindowOpacity(0.92)
        dialog.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {self.accent_color}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }}
            QComboBox {{ background-color: #161b24; border: 1px solid {self.accent_color}; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; font-size: 13px; }}
            QPushButton {{ background-color: {self.accent_color}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
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
        btn_back = QPushButton("Cancelar")
        btn_back.setStyleSheet("background-color: #161b24; color: #fff;")
        
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
        dialog.setWindowOpacity(0.92)
        dialog.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {self.accent_color}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-weight: bold; font-family: 'Segoe UI'; font-size: 13px; }}
            QPushButton {{ background-color: {self.accent_color}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
        """)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("Personalize o fundo do seu Standalone Hub:"))
        btn_add = QPushButton("Adicionar Imagem")
        btn_add.clicked.connect(lambda: self.select_background_image(dialog))
        
        btn_del = QPushButton("Excluir Imagem")
        btn_del.setStyleSheet("background-color: #ff5252; color: white;")
        btn_del.clicked.connect(lambda: self.remove_background_image(dialog))
        
        layout.addWidget(btn_add)
        layout.addWidget(btn_del)
        dialog.exec()

    def select_background_image(self, dialog):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem de Fundo", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.background_image_path = file_path
            self.update_wallpaper_brightness()
            self.save_settings(force=True)
            self.apply_styles()
            self.create_home_tab()
            dialog.accept()

    def remove_background_image(self, dialog):
        self.background_image_path = ""
        self.is_wp_light = False
        self.save_settings(force=True)
        self.apply_styles()
        self.create_home_tab()
        dialog.accept()

    def open_toolbox_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar ao Toolbox")
        dialog.setFixedWidth(420)
        dialog.setWindowOpacity(0.92)
        dialog.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {self.accent_color}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 12px; font-weight: bold; }}
            QLineEdit {{ background-color: #161b24; border: 1px solid {self.accent_color}; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; }}
            QPushButton {{ background-color: {self.accent_color}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
        """)
        form_layout = QFormLayout(dialog)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        input_name = QLineEdit()
        input_sub = QLineEdit()
        input_url = QLineEdit()
        
        btn_img = QPushButton("🖼️ Adicionar Imagem (Opcional)")
        selected_img = [""]
        
        def pick_img():
            path, _ = QFileDialog.getOpenFileName(dialog, "Selecionar Ícone", "", "Images (*.png *.jpg *.jpeg)")
            if path:
                selected_img[0] = path
                btn_img.setText("Imagem Selecionada!")
                
        btn_img.clicked.connect(pick_img)
        form_layout.addRow(QLabel("Nome do Botão:"), input_name)
        form_layout.addRow(QLabel("Subtítulo:"), input_sub)
        form_layout.addRow(QLabel("URL do Site:"), input_url)
        form_layout.addRow(btn_img)
        
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Adicionar")
        btn_back = QPushButton("Cancelar")
        btn_back.setStyleSheet("background-color: #161b24; color: #fff;")
        
        btn_save.clicked.connect(lambda: self.add_toolbox_item(input_name.text(), input_sub.text(), input_url.text(), selected_img[0], dialog))
        btn_back.clicked.connect(dialog.reject)
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_back)
        form_layout.addRow(btn_box)
        dialog.exec()

    def add_toolbox_item(self, name, sub, url, img_path, dialog):
        if name.strip() and url.strip():
            if img_path: self.process_and_save_icon(img_path, name)
            self.buttons_list.append({"label": name, "subtitle": sub, "url": url, "favorite": False})
            self.save_settings(force=True)
            self.filter_buttons_by_search(self.search_filter)
            dialog.accept()

    def open_delete_toolbox_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Remover Botão do Toolbox")
        dialog.setFixedWidth(400)
        dialog.setWindowOpacity(0.92)
        dialog.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {self.accent_color}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }}
            QComboBox {{ background-color: #161b24; border: 1px solid {self.accent_color}; border-radius: 6px; color: #fff; padding: 8px; font-family: 'Segoe UI'; }}
            QPushButton {{ background-color: {self.accent_color}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; text-align: center; }}
        """)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(QLabel("Selecione o botão que deseja excluir definitivamente:"))
        combo = QComboBox()
        for item in self.buttons_list: combo.addItem(item["label"])
        layout.addWidget(combo)
        
        btn_box = QHBoxLayout()
        btn_del = QPushButton("Deletar e Salvar")
        btn_del.setStyleSheet("background-color: #ff5252; color: #fff;")
        btn_back = QPushButton("Voltar")
        btn_back.setStyleSheet("background-color: #161b24; color: #fff;")
        
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
            icon_path = os.path.join(self.icons_dir, f"{target_label.lower()}.png")
            if os.path.exists(icon_path):
                try: os.remove(icon_path)
                except: pass
        max_pages = max(0, (len(self.buttons_list) - 1) // self.items_per_page)
        if self.current_page > max_pages: self.current_page = max_pages
        self.save_settings(force=True)  
        self.filter_buttons_by_search(self.search_filter)
        self.update_favorites_panel()
        dialog.accept()

    def save_settings(self, force=False):
        if getattr(self, 'is_restoring', False): return
        if not getattr(self, 'auto_save', False) and not force: return
        self.track_zoom_levels()
        
        pinned = []
        urls = []
        if hasattr(self, 'tabs'):
            for i in range(1, self.tabs.count()):
                widget = self.tabs.widget(i)
                if isinstance(widget, QWebEngineView):
                    url = widget.property("original_url") or widget.url().toString()
                    label = widget.property("original_label") or self.tabs.tabText(i).replace("📌 ", "")
                    if widget.property("is_pinned"):
                        pinned.append({"label": label, "url": url})
                    elif self.save_tabs_enabled:
                        urls.append({"label": label, "url": url})
            self.pinned_tabs = pinned
            self.opened_tabs_urls = urls

        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        data = {
            "auto_save": getattr(self, 'auto_save', False),
            "save_tabs_enabled": getattr(self, 'save_tabs_enabled', False),
            "theme_mode": getattr(self, 'theme_mode', 'Escuro'),
            "accent_color": getattr(self, 'accent_color', '#d9d9d9'),
            "theme_base_color": getattr(self, 'theme_base_color', '#242120'),
            "background_image_path": getattr(self, 'background_image_path', ''),
            "buttons": getattr(self, 'buttons_list', []),
            "opened_tabs": getattr(self, 'opened_tabs_urls', []),
            "pinned_tabs": getattr(self, 'pinned_tabs', []),
            "zoom_settings": getattr(self, 'zoom_settings', {}),
            "security": getattr(self, 'security_settings', {}),
            "history": getattr(self, 'history_data', {})
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_settings(self):
    data = self.config_manager.load()
    
    self.auto_save = data.get("auto_save", False)
    self.save_tabs_enabled = data.get("save_tabs_enabled", False)
    self.theme_mode = data.get("theme_mode", "Escuro")
    self.accent_color = data.get("accent_color", "#d9d9d9")
    self.theme_base_color = data.get("theme_base_color", "#242120")
    self.background_image_path = data.get("background_image_path", "")
    self.buttons_list = data.get("buttons")
    self.opened_tabs_urls = data.get("opened_tabs", [])
    self.pinned_tabs = data.get("pinned_tabs", [])
    self.zoom_settings = data.get("zoom_settings", {})
    self.security_settings = data.get("security", {})
    self.history_data = data.get("history", {})
    self.update_wallpaper_brightness()

    def reset_to_defaults(self):
        self.buttons_list = self.default_buttons.copy()
        self.accent_color = self.presets["Padrão (preto/branco)"]["accent"]
        self.theme_base_color = self.presets["Padrão (preto/branco)"]["theme"]
        self.theme_mode = "Escuro"
        self.background_image_path = ""
        self.is_wp_light = False
        self.current_page = 0
        self.auto_save = False
        self.save_tabs_enabled = False
        self.opened_tabs_urls = []
        self.pinned_tabs = []
        self.zoom_settings = {}
        self.security_settings = {}
        self.history_data = {}
        if os.path.exists(self.config_file): os.remove(self.config_file)
        self.apply_styles()
        self.create_home_tab()
        self.update_favorites_panel()

    def open_web_tab(self, url, title, is_pinned=False, lazy_load=False):
        self.search_filter = ""
        if hasattr(self, 'search_bar') and self.search_bar:
            self.search_bar.blockSignals(True)
            self.search_bar.clear()
            self.search_bar.blockSignals(False)
            self.search_bar.clearFocus() 
            
        browser = QWebEngineView(self)
        page = QWebEnginePage(self.profile, browser)
        browser.setPage(page)
        
        browser.setProperty("original_url", url)
        browser.setProperty("original_label", title)
        browser.setProperty("is_pinned", is_pinned)
        
        browser.titleChanged.connect(lambda t, b=browser: self.on_title_changed(b, t))
        browser.page().zoomFactorChanged.connect(lambda factor, b=browser: self.on_zoom_changed(b, factor))
        browser.loadFinished.connect(lambda ok, b=browser: self.apply_whatsapp_theme_on_load(b))
        
        display_title = title[:20] + "..." if len(title) > 20 else title
        if is_pinned:
            display_title = "📌 " + title[:18] + ("..." if len(title) > 18 else "")
            
        index = self.tabs.addTab(browser, display_title)
        
        if lazy_load:
            browser.setProperty("needs_load", True)
        else:
            browser.setProperty("needs_load", False)
            browser.setUrl(QUrl(url))
            if url in self.zoom_settings: browser.setZoomFactor(self.zoom_settings[url])
            self.tabs.setCurrentIndex(index)
        
        if not getattr(self, 'is_restoring', False) and not url.startswith("about:"):
            self.log_history(title, url)
        
        if not getattr(self, 'is_restoring', False):
            self.save_settings(force=True)

    def on_title_changed(self, browser, title):
        index = self.tabs.indexOf(browser)
        if index != -1:
            if not title.strip(): title = "Navegação"
            browser.setProperty("original_label", title)
            is_pinned = browser.property("is_pinned")
            
            short_title = title[:20] + "..." if len(title) > 20 else title
            if is_pinned:
                short_title = "📌 " + title[:18] + "..." if len(title) > 18 else "📌 " + title
                
            self.tabs.setTabText(index, short_title)
            if getattr(self, 'save_tabs_enabled', False) and not getattr(self, 'is_restoring', False):
                self.save_settings(force=True)

    def apply_whatsapp_theme_on_load(self, browser):
        url = browser.url().toString()
        if "whatsapp.com" in url:
            c_theme = QColor(self.get_active_theme_color())
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
            if isinstance(widget, QWebEngineView): self.apply_whatsapp_theme_on_load(widget)

    def on_zoom_changed(self, browser, factor):
        try:
            url = browser.property("original_url") or browser.url().toString()
            if url and url != "about:blank":
                self.zoom_settings[url] = factor
                if getattr(self, 'save_tabs_enabled', False): self.save_settings(force=True)
        except RuntimeError: pass

    def track_zoom_levels(self):
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                url = widget.property("original_url") or widget.url().toString()
                if url and url != "about:blank": self.zoom_settings[url] = widget.zoomFactor()

    def close_tab(self, index):
        if index != 0:
            widget = self.tabs.widget(index)
            if widget: widget.deleteLater()
            self.tabs.removeTab(index)
            if not getattr(self, 'is_restoring', False): 
                self.save_settings(force=True)

    def restore_tabs(self):
        self.is_restoring = True
        
        for t in getattr(self, 'pinned_tabs', []):
            self.open_web_tab(t["url"], t["label"], is_pinned=True, lazy_load=True)
            
        if getattr(self, 'save_tabs_enabled', False) and self.opened_tabs_urls:
            tabs_to_open = list(self.opened_tabs_urls)
            for t in tabs_to_open:
                already_pinned = any(p["url"] == t["url"] for p in getattr(self, 'pinned_tabs', []))
                if not already_pinned:
                    self.open_web_tab(t["url"], t["label"], is_pinned=False, lazy_load=False)
                    
        QTimer.singleShot(200, self.release_restore_lock)

    def release_restore_lock(self):
        self.is_restoring = False
        self.tabs.setCurrentIndex(0)