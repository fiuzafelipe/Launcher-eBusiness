import os
import sys
import shutil
import gc
import datetime
import logging

from core.browser_engine import BrowserEngine
from core.config_manager import ConfigManager
from ui.browser_tab import BrowserTab
from ui.styles import get_main_stylesheet

from ui.components import (CustomTabWidget, ThemeSelectorButton, FolderCableFrame,
                           DraggableToolButton, LockScreenWidget)

from ui.dialogs import (HistoryDialog, AboutDialog, DirectNavDialog, CommandPaletteDialog)
from ui.settings_dialogs import SettingsDialog

from PyQt6.QtWidgets import (QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QSizePolicy, QLineEdit, QLabel, QDialog,
                             QFileDialog, QMessageBox, QScrollArea, QMenu, QGraphicsBlurEffect,
                             QStackedLayout, QApplication, QTabWidget, QGraphicsDropShadowEffect)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage, QWebEngineSettings,
                                   QWebEnginePermission, QWebEngineDownloadRequest,
                                   QWebEngineScript, QWebEngineUrlRequestInterceptor)
from PyQt6.QtCore import QUrl, Qt, QPoint, QTimer, QEvent, QPointF
from PyQt6.QtGui import QColor, QImage, QShortcut, QKeySequence, QCursor, QPainter, QPainterPath, QPen, QIcon

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class HomePanelAdapter(QWidget):
    def __init__(self, hub):
        super().__init__()
        self.hub = hub


class StandaloneHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_file = os.path.join(current_dir, "core", "config.json")
        self.setWindowTitle("Custom Explorer")
        self.resize(1280, 720)
        
        # Inicialização de caminhos e configs
        self.config_manager = ConfigManager(self.config_file)
        self.icons_dir = os.path.join(os.path.dirname(current_dir), "assets", "icons")
        os.makedirs(self.icons_dir, exist_ok=True)
        
        # ============================================================
        # MOTOR DO NAVEGADOR (Isolado)
        # Mantém intactas as sessões do Google e configs do WhatsApp
        # ============================================================
        self.browser_engine = BrowserEngine(self)
        self.profile = self.browser_engine.get_profile()
        self.storage_path = self.browser_engine.storage_path

        # ============================================================
        # VARIÁVEIS E PRESETS ORIGINAIS
        # ============================================================
        self.presets = {"Padrão (preto/branco)": {"theme": "#242120", "accent": "#d9d9d9"}, "Verde": {"theme": "#0f2419", "accent": "#12d97c"}, "Vermelho": {"theme": "#270d0d", "accent": "#d91e10"}, "Azul Claro": {"theme": "#0d2721", "accent": "#0dd9a6"}, "Azul Escuro": {"theme": "#0d0d27", "accent": "#0d0dd9"}, "Laranja": {"theme": "#271a0c", "accent": "#d9790c"}, "Amarelo": {"theme": "#27270c", "accent": "#d9d9d9"}, "Roxo Claro": {"theme": "#270d27", "accent": "#d90ccf"}, "Rosa": {"theme": "#270d14", "accent": "#d90c3c"}, "Branco": {"theme": "#d6dcd1", "accent": "#ffffff"}}
        self.current_page, self.items_per_page, self.is_restoring, self.search_filter, self.is_wp_light = 0, 8, False, "", False
        self.load_settings()
        
        # APLICA ICONE SALVO
        try:
            icon_path = os.path.join(self.icons_dir, self.app_icon)
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print("[ICON ERROR]", e)
        
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
        self.btn_direct_nav.clicked.connect(lambda: DirectNavDialog(self).exec())
        
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

        # LADO ESQUERDO
        self.bottom_bar.addWidget(
            self.lbl_status,
            alignment=Qt.AlignmentFlag.AlignVCenter
        )

        # ESPAÇO CENTRAL RESERVADO
        self.bottom_bar.addStretch()

        # LADO DIREITO
        self.bottom_bar.addWidget(
            self.btn_save_session,
            alignment=Qt.AlignmentFlag.AlignVCenter
        )

        # BOTÃO TEMA FICA INDEPENDENTE
        self.theme_btn = ThemeSelectorButton(self)
        self.theme_btn.setFixedSize(40,40)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setOffset(0,0)
        shadow.setColor(QColor(self.accent_color))

        self.theme_btn.setGraphicsEffect(shadow)
        
        self.theme_btn.setParent(self.bottom_bar_widget)
        self.theme_btn.move(
            (self.bottom_bar_widget.width() - 40) // 2,
            2
        )
        self.theme_btn.raise_()
        
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

        # Atalhos existentes
        self.shortcut_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_right.activated.connect(self.safe_next_page)
        self.shortcut_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_left.activated.connect(self.safe_prev_page)
        self.shortcut_esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.shortcut_esc.activated.connect(self.safe_close_search)
        
        # --- NOVO: Atalho da Command Palette ---
        self.shortcut_cmd = QShortcut(QKeySequence("Ctrl+K"), self)
        self.shortcut_cmd.activated.connect(self.show_command_palette)

        self.showMaximized()
        if getattr(self, 'security_settings', {}) and self.security_settings.get("enabled", False):
            self.show_lock_screen()

# ===================================================================================================
# TODOS OS OUTROS MÉTODOS (force_clean_session, logout_google, apply_styles, etc) CONTINUAM IGUAIS
# Você não precisa alterar absolutamente nada abaixo da função __init__
# ===================================================================================================

    def force_clean_session(self):
        try:
            self.profile.cookieStore().deleteAllCookies()
            self.profile.clearHttpCache()
            self.profile.clearAllVisitedLinks()
            print("[SESSION] Cookies removidos")
        except Exception as e:
            print("[SESSION CLEAN ERROR]", e)

    def logout_google(self):

        try:

            for i in range(1, self.tabs.count()):

                browser = self.tabs.widget(i)

                if isinstance(browser, QWebEngineView):

                    browser.setUrl(
                        QUrl(
                            "https://accounts.google.com/Logout"
                        )
                    )

                    break


            QTimer.singleShot(
                5000,
                self.reload_browser_session
            )


            QMessageBox.information(
                self,
                "Logout Google",
                "Conta Google desconectada."
            )

            print("[GOOGLE] Logout realizado")

        except Exception as e:

            print("[LOGOUT ERROR]", e)

    def reload_browser_session(self):

        """
        Recarrega perfil Chromium sem fechar programa
        """

        try:

            for i in range(1, self.tabs.count()):

                widget = self.tabs.widget(i)

                if isinstance(widget, QWebEngineView):

                    widget.reload()


            print("[SESSION] Relogin preparado")


        except Exception as e:

            print("[RELOGIN ERROR]", e)

    def clear_google_storage(self):

        """
        Limpa completamente a sessão Google/Chromium
        Remove:
        - Cookies
        - Cache
        - LocalStorage
        - IndexedDB
        - Sessões salvas
        - Permissões
        """

        reply = QMessageBox.question(
            self,
            "Limpar sessão Google",
            "Isso removerá todos os logins salvos do navegador.\n\n"
            "Deseja continuar?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:

            print("[SESSION] Iniciando limpeza...")

            # Remove cookies
            self.profile.cookieStore().deleteAllCookies()

            # Limpa cache Chromium
            self.profile.clearHttpCache()

            # Limpa histórico
            self.profile.clearAllVisitedLinks()

            # Remove storage completo
            if os.path.exists(self.storage_path):

                shutil.rmtree(
                    self.storage_path,
                    ignore_errors=True
                )

            # Recria pasta limpa

            os.makedirs(
                self.storage_path,
                exist_ok=True
            )

            QMessageBox.information(
                self,
                "Sessão limpa",
                "Dados Google removidos com sucesso.\n\n"
                "Reinicie o Custom Explorer."
            )

            print(
                "[SESSION] Storage Google resetado"
            )

        except Exception as e:

            QMessageBox.warning(
                self,
                "Erro",
                str(e)
            )

            print(
                "[CLEAR SESSION ERROR]",
                e
            )

    def show_tab_context_menu(self, pos):
        index = self.tabs.tabBar().tabAt(pos)
        if index <= 0: return 
        widget = self.tabs.widget(index)
        if not isinstance(widget, QWebEngineView): return
        is_pinned = widget.property("is_pinned")
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background-color: #161b24; color: #fff; border: 1px solid {self.accent_color}; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; padding: 5px; }} QMenu::item {{ padding: 8px 25px; border-radius: 4px; }} QMenu::item:selected {{ background-color: {self.accent_color}; color: #000; }}")
        
        if is_pinned:
            action_unpin = menu.addAction("❌ Desfixar Aba")
            if menu.exec(self.tabs.tabBar().mapToGlobal(pos)) == action_unpin:
                widget.setProperty("is_pinned", False)
                raw_label = widget.property("original_label") or "Navegação"
                self.tabs.setTabText(index, raw_label[:20] + ("..." if len(raw_label)>20 else ""))
                self.save_settings(force=True)
        else:
            action_pin = menu.addAction("📌 Fixar Aba")
            if menu.exec(self.tabs.tabBar().mapToGlobal(pos)) == action_pin:
                widget.setProperty("is_pinned", True)
                raw_label = widget.property("original_label") or "Navegação"
                self.tabs.setTabText(index, "📌 " + raw_label[:18] + ("..." if len(raw_label)>18 else ""))
                self.save_settings(force=True)

    def closeEvent(self, event):
        self.save_settings(force=True)
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
            menu.setStyleSheet(f"QMenu {{ background-color: #161b24; color: #fff; border: 1px solid {self.accent_color}; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; padding: 5px; }} QMenu::item {{ padding: 8px 25px; border-radius: 4px; }} QMenu::item:selected {{ background-color: {self.accent_color}; color: #000; }}")
            
            history_action = menu.addAction("🕒 Histórico")
            folder_action = menu.addAction("📁 Criar Pasta")
            lock_action = menu.addAction("🔒 Trancar Tela") if self.security_settings.get("enabled", False) else None
            
            action = menu.exec(self.mapToGlobal(event.pos()))
            
            if action == history_action:
                HistoryDialog(self).exec()
            elif action == folder_action:
                from ui.folder_dialogs import CreateFolderDialog
                CreateFolderDialog(self).exec()
            elif lock_action and action == lock_action:
                self.show_lock_screen()
        else:
            super().contextMenuEvent(event)

    def open_security_modify(self):
        from ui.dialogs import SecurityModifyDialog
        dialog = SecurityModifyDialog(self, self.security_settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.security_settings = dialog.security_data
            self.save_settings(force=True)
            QMessageBox.information(self, "Sucesso", "Configurações de segurança atualizadas!")

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if hasattr(self, "theme_btn"):

            self.theme_btn.move(
                (self.bottom_bar_widget.width() - self.theme_btn.width()) // 2,
                2
            )

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
        if hasattr(self, 'fav_search_bar') and self.fav_search_bar.isVisible(): self.toggle_fav_search()

    def show_command_palette(self):
        """Abre a barra de pesquisa rápida global (Ctrl+K)"""
        # Verifica com segurança se a tela de bloqueio existe e está visível
        try:
            if hasattr(self, 'lock_screen') and self.lock_screen is not None and self.lock_screen.isVisible():
                return
        except RuntimeError:
            # O objeto C++ já foi deletado da memória (a tela foi desbloqueada)
            self.lock_screen = None
            
        palette = CommandPaletteDialog(self)
        palette.exec()

    def filter_favorites(self, text): self.update_favorites_panel(text)

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
        return QColor.fromHsl(c.hue(), min(c.saturation(), 60), 240).name() if getattr(self, 'theme_mode', 'Escuro') == "Claro" else QColor.fromHsl(c.hue(), c.saturation(), min(c.lightness(), 25)).name()

    def optimize_memory_without_reload(self, index):
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                if i != index: widget.setVisible(False)
                else:
                    widget.setVisible(True)
                    if widget.property("needs_load"):
                        widget.setProperty("needs_load", False)
                        widget.setUrl(QUrl(widget.property("original_url")))
        gc.collect()

    def update_favorites_panel(self, filter_text=""):
        if not hasattr(self, 'fav_hbox') or not self.fav_hbox: return
        while self.fav_hbox.count():
            item = self.fav_hbox.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        fav_items = [b for b in self.buttons_list if b.get("favorite", False)]
        if filter_text: fav_items = [b for b in fav_items if filter_text.strip().lower() in b["label"].lower()]
        bg_rgba = f"rgba({QColor(self.accent_color).red()}, {QColor(self.accent_color).green()}, {QColor(self.accent_color).blue()}, 0.85)"
            
        for item in fav_items:
            btn = QPushButton(item["label"])
            btn.setObjectName("FavItemBtn")
            btn.setFixedSize(140, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"QPushButton#FavItemBtn {{ background-color: {bg_rgba}; border: 1px solid rgba(0,0,0,0.5); color: #07080a; font-size: 12px; font-weight: bold; border-radius: 4px; }} QPushButton#FavItemBtn:hover {{ background-color: {self.accent_color}; }}")
            btn.clicked.connect(lambda checked, u=item["url"], l=item["label"]: self.open_web_tab(u, l))
            self.fav_hbox.addWidget(btn)
        self.fav_hbox.addStretch()

    def show_fav_panel(self):
        if hasattr(self, 'fav_area_layout') and self.fav_area_layout.currentWidget() != self.fav_panel_widget:
            self.update_favorites_panel(self.fav_search_bar.text())
            self.fav_area_layout.setCurrentWidget(self.fav_panel_widget)

    def hide_fav_panel(self):
        if hasattr(self, 'fav_area_layout') and self.fav_area_layout.currentWidget() == self.fav_panel_widget:
            if hasattr(self, 'fav_search_bar') and self.fav_search_bar.isVisible() and self.fav_search_bar.hasFocus(): return
            self.fav_area_layout.setCurrentWidget(self.fav_placeholder)

    def check_mouse_position_for_favorites(self):
        if not hasattr(self, 'home_widget') or not self.home_widget or self.tabs.currentIndex() != 0:
            self.hide_fav_panel()
            return
        if not any(b.get("favorite", False) for b in self.buttons_list): return
        if hasattr(self, 'fav_search_bar') and self.fav_search_bar.isVisible() and self.fav_search_bar.hasFocus(): return
        
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        self.show_fav_panel() if 0 <= cursor_pos.y() <= 95 else self.hide_fav_panel()

    def eventFilter(self, obj, event):
        if obj == self.tabs.tabBar() and event.type() == QEvent.Type.MouseMove and self.tabs.currentIndex() == 0:
            if any(b.get("favorite", False) for b in self.buttons_list): self.show_fav_panel()
        return super().eventFilter(obj, event)

    def delete_button_by_data(self, item_data):
        from PyQt6.QtWidgets import QApplication
        from ui.components import FolderPanelWidget
        
        if item_data in getattr(self, 'buttons_list', []):
            self.buttons_list.remove(item_data)
            
        if item_data in getattr(self, 'folders_list', []):
            self.folders_list.remove(item_data)
        
        for folder in getattr(self, 'folders_list', []):
            if item_data in folder.get("buttons", []):
                folder["buttons"].remove(item_data)
        
        lbl_name = item_data.get('label', '').lower()
        paths_to_check = [
            os.path.join(self.icons_dir, f"{lbl_name}.png"),
            os.path.join(self.icons_dir, f"folder_{lbl_name}.png")
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                try: os.remove(path)
                except: pass
                
        self.save_settings(force=True)
        self.filter_buttons_by_search(self.search_filter)
        
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, FolderPanelWidget):
                widget.refresh_grid()

    def edit_button_dialog(self, item_data):
        if item_data.get("type") == "folder":
            from ui.folder_dialogs import CreateFolderDialog
            dialog = CreateFolderDialog(self, folder_data=item_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.save_settings(force=True)
                self.filter_buttons_by_search(self.search_filter)
        else:
            from ui.dialogs import EditButtonDialog
            EditButtonDialog(self, item_data).exec()
            self.filter_buttons_by_search(self.search_filter)

    def edit_folder_dialog(self, folder_data):
        from ui.dialogs import EditFolderDialog 
        dialog = EditFolderDialog(self, folder_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.save_settings(force=True)
            self.filter_buttons_by_search(self.search_filter)

    def handle_permission_request(self, request: QWebEnginePermission): request.grant()

    def handle_download_request(self, download: QWebEngineDownloadRequest):
        default_name = download.downloadFileName() or "download_midia"
        suggested_path = os.path.join(os.path.join(os.path.expanduser('~'), 'Downloads'), default_name)
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", suggested_path)
        if file_path:
            download.setDownloadDirectory(os.path.dirname(file_path))
            download.setDownloadFileName(os.path.basename(file_path))
            download.accept()
            self.lbl_status.setText(f"Baixando: {os.path.basename(file_path)}...")
            download.receivedBytesChanged.connect(lambda: self.update_download_progress(download))
        else: download.interrupt()

    def update_download_progress(self, download):
        if download.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress:
            if download.totalBytes() > 0: self.lbl_status.setText(f"Baixando... {int((download.receivedBytes() / download.totalBytes()) * 100)}%")
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
        self.fav_area_layout = QStackedLayout(self.fav_area)
        self.fav_area_layout.setContentsMargins(0,0,0,0)
        self.fav_placeholder = QWidget()
        self.fav_placeholder.setStyleSheet("background: transparent; border-image: none;")
        self.fav_panel_widget = QWidget()
        self.fav_panel_widget.setObjectName("FavPanelWidget")
        self.fav_hbox = QHBoxLayout(self.fav_panel_widget)
        self.fav_hbox.setContentsMargins(15, 0, 15, 0)
        self.fav_hbox.setSpacing(10)
        self.fav_area_layout.addWidget(self.fav_placeholder) 
        self.fav_area_layout.addWidget(self.fav_panel_widget) 
        home_vertical_layout.addWidget(self.fav_area)
        
        self.home_panel_adapter = HomePanelAdapter(self)

        self.grid_container_widget = FolderCableFrame(
            self.home_panel_adapter
        )

        self.grid_container_widget.setMouseTracking(True)

        self.grid_container_widget.setStyleSheet(
            """
            QWidget {
                border: none;
                background: transparent;
            }
            """
        )

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(40, 15, 40, 60)

        self.grid_container_widget.setLayout(content_layout)
        control_panel_layout = QVBoxLayout()
        control_panel_layout.setSpacing(10)
        
        has_wp = hasattr(self, 'background_image_path') and self.background_image_path and os.path.exists(self.background_image_path)
        text_color = "#111111" if getattr(self, 'is_wp_light', False) else "#f5f5f5"
        self.current_text_color = text_color # Guarda para atualizar a cor do botão depois
        c_accent = QColor(self.accent_color)
        c_theme = QColor(self.get_active_theme_color())
        
        if has_wp:
            input_bg, input_text, font_weight, page_color = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.5)", text_color, "600", text_color
        else:
            is_light = c_theme.lightness() > 128
            input_bg, input_text, font_weight, page_color = "rgba(255, 255, 255, 0.1)" if not is_light else "rgba(0, 0, 0, 0.05)", "#ffffff" if not is_light else "#07080a", "bold", "#07080a" if is_light else "#ffffff"

        btn_ops = QPushButton("STANDALONE HUB")
        btn_ops.setObjectName("btn_ops")
        btn_ops.setFixedSize(450, 42)
        btn_ops.clicked.connect(lambda: AboutDialog(self).exec())
        
        btn_config_menu = QPushButton("CONFIGURAÇÕES  ⚙")
        btn_config_menu.setObjectName("btn_config_menu")
        btn_config_menu.setFixedSize(450, 42)
        btn_config_menu.clicked.connect(lambda: SettingsDialog(self).exec())
        self.btn_ops_home = btn_ops
        self.btn_config_home = btn_config_menu
        
        self.search_bar = QLineEdit()
        self.theme_search_box = self.search_bar
        self.search_bar.setFixedSize(450, 42)
        self.search_bar.setPlaceholderText("Digite aqui o botão que deseja acessar...")
        self.search_bar.setText(self.search_filter)
        self.search_bar.textChanged.connect(self.filter_buttons_by_search)
        self.search_bar.setStyleSheet(f"QLineEdit {{ background-color: {input_bg}; border: 1px solid {self.accent_color}; border-radius: 6px; color: {input_text}; font-family: 'Segoe UI'; font-size: 13px; font-weight: {font_weight}; padding-left: 15px; padding-right: 15px; }} QLineEdit:focus {{ border: 2px solid {self.accent_color}; }}")
        
        control_panel_layout.addWidget(btn_ops, alignment=Qt.AlignmentFlag.AlignCenter)
        control_panel_layout.addWidget(btn_config_menu, alignment=Qt.AlignmentFlag.AlignCenter)
        control_panel_layout.addWidget(self.search_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        content_layout.addLayout(control_panel_layout)
        content_layout.addSpacing(5)

        self.grid_layout = QGridLayout()

        self.grid_layout.setSpacing(25)

        self.grid_layout.setContentsMargins(20, 0, 20, 0)
        self.grid_layout.setSpacing(25)
        grid_container_hbox = QHBoxLayout()
        grid_container_hbox.addStretch()
        grid_container_hbox.addLayout(self.grid_layout)
        grid_container_hbox.addStretch()
        content_layout.addLayout(grid_container_hbox)

        self.nav_container = QWidget()
        nav_layout = QHBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(0, 10, 0, 10)
        nav_layout.addStretch()
        nav_style = f"QPushButton {{ background-color: {self.accent_color}; border: 1px solid rgba(0,0,0,0.25); color: #07080a; font-weight: bold; font-size: 15px; border-radius: 5px; }} QPushButton:hover {{ background-color: rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40); color: {self.accent_color}; border-color: rgba(255,255,255,0.5); }} QPushButton:disabled {{ border: 1px solid rgba(0,0,0,0.1); color: rgba(120, 120, 120, 0.5); background-color: rgba(0, 0, 0, 0.15); }}"
        
        self.btn_prev_page = QPushButton("<")
        self.btn_prev_page.setFixedSize(60, 40)
        self.btn_prev_page.setStyleSheet(nav_style)
        self.btn_prev_page.clicked.connect(self.prev_page)
        
        self.page_label = QLabel(f"Página {self.current_page + 1}")
        self.page_label.setFixedWidth(80) 
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet(
            f"""
            color:
            {page_color};

            font-weight:
            {font_weight};

            font-size:
            14px;

            font-family:
            'Segoe UI';

            background:
            transparent;
            """
        )

        self.theme_page_label = self.page_label
        
        self.btn_next_page = QPushButton(">")
        self.btn_next_page.setFixedSize(60, 40)
        self.btn_next_page.setStyleSheet(nav_style)
        self.btn_next_page.clicked.connect(self.next_page)
        
        nav_layout.addWidget(self.btn_prev_page)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.btn_next_page)
        nav_layout.addStretch()
        
        content_layout.addStretch()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.grid_container_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        scroll_area.setWidget(self.grid_container_widget)
        home_vertical_layout.addWidget(scroll_area)
        
        home_vertical_layout.addWidget(self.nav_container)
        home_vertical_layout.addSpacing(10)

        self.tabs.insertTab(0, self.home_widget, "Home")
        self.update_favorites_panel()
        self.filter_buttons_by_search(self.search_filter)

    def apply_styles(self):
        accent = self.accent_color
        c_accent = QColor(accent)
        main_bg = self.get_active_theme_color()
        c_theme = QColor(main_bg)
        is_light_theme = c_theme.lightness() > 128
        has_wp = hasattr(self, 'background_image_path') and self.background_image_path and os.path.exists(self.background_image_path)
        is_bg_light = getattr(self, 'is_wp_light', False)
        
        icon_col = "#111111" if (has_wp and is_bg_light) else ("#07080a" if is_light_theme else "#ffffff")
        self.btn_direct_nav.setStyleSheet(f"QPushButton {{ background: transparent; border: none; font-size: 14px; color: {icon_col}; }} QPushButton:hover {{ color: {accent}; }}")
        self.btn_search_fav.setStyleSheet(f"QPushButton {{ background: transparent; border: none; font-size: 14px; color: {icon_col}; }} QPushButton:hover {{ color: {accent}; }}")
        self.corner_widget.setStyleSheet("background: transparent;")
        
        text_search_fav = "#111111" if (has_wp and is_bg_light) else ("#000000" if is_light_theme else "#ffffff")
        self.fav_search_bar.setStyleSheet(f"QLineEdit {{ background-color: rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.25); border: 1px solid {accent}; border-radius: 4px; color: {text_search_fav}; font-family: 'Segoe UI'; font-size: 12px; font-weight: bold; padding: 0 5px; }}")
        
        strong_line, faint_line = f"3px solid {accent}", f"1px solid rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.50)"

        # CORREÇÃO GLOBAL: Definindo a cor sólida e hover transparente como base
        btn_ops_bg = accent 
        btn_ops_hover_bg = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"
        btn_ops_hover_text = "#ffffff"

        if has_wp:
            main_bg_style = f"border-image: url('{self.background_image_path.replace('\\', '/')}') 0 0 0 0 stretch stretch;"
            tabbar_bg = "rgba(255,255,255,0.35)" if is_bg_light else "rgba(0,0,0,0.35)"
            tab_inactive_bg = "rgba(255,255,255,0.15)" if is_bg_light else "rgba(0,0,0,0.15)"
            tab_active_bg = "rgba(255,255,255,0.85)" if is_bg_light else "rgba(20,20,20,0.85)"
            pane_bg = "transparent"
            text_color = "#111111" if is_bg_light else "#f5f5f5"
            font_weight = "600"
            bottom_bar_bg = "transparent"
        else:
            solid_text_color = "#07080a" if is_light_theme else "#ffffff"
            top_bar_bg_solid = QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(30, c_theme.lightness() - 12)).name() if is_light_theme else QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(5, c_theme.lightness() - 8)).name()
            tab_inactive_bg_solid = QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(40, c_theme.lightness() - 20)).name() if is_light_theme else QColor.fromHsl(c_theme.hue(), c_theme.saturation(), max(10, c_theme.lightness() + 6)).name()
            main_bg_style = f"background-color: {top_bar_bg_solid};"
            tabbar_bg = top_bar_bg_solid
            tab_inactive_bg = tab_inactive_bg_solid
            tab_active_bg = main_bg
            pane_bg = main_bg
            text_color = solid_text_color
            font_weight = "bold"
            bottom_bar_bg = "transparent"

        self.lbl_status.setStyleSheet(
            f"""
            QLabel {{
                color:{accent};
                font-family:'Segoe UI';
                font-weight:bold;
                font-size:13px;
                background:transparent;
            }}
            """
        )
        
        # O stylesheet global agora recebe as cores sólidas corretamente
        self.setStyleSheet(get_main_stylesheet(accent, main_bg, strong_line, faint_line, tabbar_bg, tab_inactive_bg, tab_active_bg, pane_bg, btn_ops_bg, btn_ops_hover_bg, btn_ops_hover_text, text_color, font_weight, bottom_bar_bg, main_bg_style))
        self.update_save_tabs_button_visual()
        
        # atualiza caixa de pesquisa conforme tema
        if hasattr(self, "theme_search_box"):
            self.theme_search_box.setStyleSheet(
                f"""
                QLineEdit {{
                    background-color: rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.35);
                    border: 1px solid {accent};
                    border-radius:6px;
                    color:{text_color};
                    font-family:'Segoe UI';
                    font-size:13px;
                    font-weight:bold;
                    padding-left:15px;
                }}
                QLineEdit:focus {{
                    border: 2px solid {accent};
                }}
                """
            )

        # atualiza navegação < >
        if hasattr(self, "btn_prev_page"):
            nav_style = f"""
            QPushButton {{
                background-color: {accent};
                border: 1px solid rgba(0,0,0,0.25);
                color: #07080a;
                font-weight: bold;
                font-size: 15px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40);
                border: 1px solid {accent};
                color: #07080a;
            }}
            QPushButton:disabled {{
                border: 1px solid rgba(0,0,0,0.10);
                color: rgba(120,120,120,0.5);
                background-color: rgba(0,0,0,0.15);
            }}
            """
            self.btn_prev_page.setStyleSheet(nav_style)
            self.btn_next_page.setStyleSheet(nav_style)
        
        # CORREÇÃO LOCAL: Usando ID Selectors (#btn_ops) para vencer a briga do CSS!
        if hasattr(self, "btn_ops_home"):
            btn_text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"

            self.btn_ops_home.setStyleSheet(f"""
                QPushButton#btn_ops {{
                    background-color: {accent};
                    border: 1px solid rgba(0,0,0,0.3);
                    border-radius: 8px;
                    color: {btn_text_color};
                    font-weight: bold;
                    letter-spacing: 2px;
                }}
                QPushButton#btn_ops:hover {{
                    background-color: rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40);
                    border: 1px solid {accent};
                    color: #ffffff;
                }}
            """)
            
            self.btn_config_home.setStyleSheet(f"""
                QPushButton#btn_config_menu {{
                    background-color: {accent};
                    border: 1px solid rgba(0,0,0,0.3);
                    border-radius: 8px;
                    color: {btn_text_color};
                    font-weight: bold;
                    letter-spacing: 2px;
                }}
                QPushButton#btn_config_menu:hover {{
                    background-color: rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40);
                    border: 1px solid {accent};
                    color: #ffffff;
                }}
            """)

        self.sync_all_whatsapp_themes()

    def update_save_tabs_button_visual(self):

        accent = QColor(self.accent_color)

        r = accent.red()
        g = accent.green()
        b = accent.blue()

        bottom_bg = f"rgba({r},{g},{b},0.22)"
        status_bg = f"rgba({r},{g},{b},0.45)"

        if hasattr(self, 'background_image_path') and self.background_image_path and os.path.exists(self.background_image_path):
            
            bottom_bg = f"rgba({r},{g},{b},0.35)"
            status_bg = f"rgba({r},{g},{b},0.60)"

        # FUNDO GERAL DA BARRA INFERIOR
        self.bottom_bar_widget.setStyleSheet(
            f"""
            QWidget#BottomBar {{

                background-color:
                {bottom_bg};

                border-top:
                2px solid {self.accent_color};

            }}

            QWidget#BottomBar:hover {{

                background-color:
                rgba(
                {r},
                {g},
                {b},
                0.45
                );

                border-top:
                2px solid {self.accent_color};

            }}

            """
        )
        
        # EFEITO DE LUZ NO FUNDO DA BARRA
        glow = QGraphicsDropShadowEffect()

        glow.setBlurRadius(35)

        glow.setOffset(0, -5)

        glow.setColor(
            QColor(
                r,
                g,
                b,
                180
            )
        )

        self.bottom_bar_widget.setGraphicsEffect(glow)

        # BOTAO SAVE FIXO
        self.btn_save_session.setStyleSheet(
            f"""
            QPushButton {{
                background-color: rgba({r},{g},{b},0.85);
                border: 1px solid {self.accent_color};
                color:#07080a;
                font-weight:bold;
                border-radius:5px;
                margin-top:8px;
            }}

            QPushButton:hover {{
                background-color:{self.accent_color};
                color:white;
                border:1px solid white;
            }}
            """
        )
         
        # STATUS SAVE ABAS         
        if self.save_tabs_enabled:

            self.lbl_status.setStyleSheet(
                f"""
                QLabel {{
                    background-color:{status_bg};
                    border:1px solid {self.accent_color};
                    color:white;
                    font-family:'Segoe UI';
                    font-size:13px;
                    font-weight:bold;
                    border-radius:6px;
                    padding-left:12px;
                    padding-right:12px;
                    padding-top:7px;
                    padding-bottom:7px;
                }}
                """
            )


            self.lbl_status.setText("Save abas ativado.")

        else:

            self.lbl_status.setStyleSheet(
                """
                QLabel {
                    background:transparent;
                    border:none;
                    color:white;
                    font-family:'Segoe UI';
                    font-size:13px;
                    font-weight:bold;
                }
                """
            )

            self.lbl_status.setText("")

        self.lbl_status.adjustSize()

        self.lbl_status.setFixedHeight(32)

        self.btn_save_session.setFixedHeight(30)

    def trigger_save_tabs_button(self):
        self.save_tabs_enabled = not self.save_tabs_enabled
        self.update_save_tabs_button_visual()
        self.save_settings(force=True)

    def toggle_auto_save_from_checkbox(self, state):
        self.auto_save = (state == 2 or state == Qt.CheckState.Checked)
        if self.auto_save: self.save_settings(force=True)

    def reorder_buttons(self, src_idx, target_idx):
        self.buttons_list.insert(target_idx, self.buttons_list.pop(src_idx))
        self.save_settings(force=True)
        self.filter_buttons_by_search(self.search_filter)

    def filter_buttons_by_search(self, text):
        self.search_filter = text
        filtered_list = [b for b in self.buttons_list if self.search_filter.strip().lower() in b["label"].lower()]
        self.render_grid(self.grid_layout, filtered_list)
        
        max_pages = max(0, (len(filtered_list) - 1) // self.items_per_page)
        if hasattr(self, 'btn_next_page'):
            self.btn_next_page.setEnabled(self.current_page < max_pages)
            self.btn_prev_page.setEnabled(self.current_page > 0)
            self.page_label.setText(f"Página {self.current_page + 1}")

    def render_grid(self, layout, items):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
                
        all_items = items
        if layout == self.grid_layout:
            all_items = items + getattr(self, 'folders_list', [])
        
        page_items = all_items[self.current_page * self.items_per_page : (self.current_page * self.items_per_page) + self.items_per_page] if layout == self.grid_layout else all_items
        
        row, col = 0, 0
        for item in page_items:
            btn = DraggableToolButton(item_data=item, item_index=all_items.index(item), parent_hub=self)
            btn.setFixedSize(220, 145)
            layout.addWidget(btn, row, col)
            col += 1
            if col > 3: col, row = 0, row + 1

    def log_history(self, label, url):
        date_str, time_str = datetime.datetime.now().strftime("%Y-%m-%d"), datetime.datetime.now().strftime("%H:%M")
        if not hasattr(self, 'history_data'): self.history_data = {}
        if date_str not in self.history_data: self.history_data[date_str] = []
        self.history_data[date_str].insert(0, {"time": time_str, "label": label, "url": url})
        self.save_settings(force=True)

    def load_settings(self):
        data = self.config_manager.load()
        self.buttons_list = data.get("buttons", [])
        self.folders_list = data.get("folders", [])
        self.auto_save, self.save_tabs_enabled = data.get("auto_save", False), data.get("save_tabs_enabled", False)
        self.theme_mode, self.accent_color, self.theme_base_color = data.get("theme_mode", "Escuro"), data.get("accent_color", "#10b981"), data.get("theme_base_color", "#242120")
        
        self.app_icon = data.get("app_icon", "Custom Transparent.ico")
        
        self.background_image_path = data.get("background_image_path", "")
        self.opened_tabs_urls, self.pinned_tabs = data.get("opened_tabs", []), data.get("pinned_tabs", [])
        self.zoom_settings, self.security_settings, self.history_data = data.get("zoom_settings", {}), data.get("security", {}), data.get("history", {})
        self.update_wallpaper_brightness()

    def save_settings(self, force=False):
        if getattr(self, 'is_restoring', False) or (not getattr(self, 'auto_save', False) and not force): 
            return
        
        self.track_zoom_levels()
        pinned, urls = [], []
        
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
            
            self.pinned_tabs, self.opened_tabs_urls = pinned, urls

        self.config_manager.save({
            "auto_save": getattr(self, 'auto_save', False),
            "save_tabs_enabled": getattr(self, 'save_tabs_enabled', False),
            "theme_mode": getattr(self, 'theme_mode', 'Escuro'),
            "accent_color": getattr(self, 'accent_color', '#10b981'),
            "theme_base_color": getattr(self, 'theme_base_color', '#242120'),
            
            "app_icon": getattr(self, 'app_icon', 'Custom Transparent.ico'),
            
            "background_image_path": getattr(self, 'background_image_path', ''),
            "buttons": getattr(self, 'buttons_list', []),
            "folders": getattr(self, 'folders_list', []),  
            "opened_tabs": getattr(self, 'opened_tabs_urls', []),
            "pinned_tabs": getattr(self, 'pinned_tabs', []),
            "zoom_settings": getattr(self, 'zoom_settings', {}),
            "security": getattr(self, 'security_settings', {}),
            "history": getattr(self, 'history_data', {})
        })

    def reset_to_defaults(self):
        self.buttons_list, self.accent_color, self.theme_base_color, self.theme_mode, self.background_image_path, self.is_wp_light, self.current_page, self.auto_save, self.save_tabs_enabled, self.opened_tabs_urls, self.pinned_tabs, self.zoom_settings, self.security_settings, self.history_data = self.config_manager.default_buttons.copy(), self.presets["Padrão (preto/branco)"]["accent"], self.presets["Padrão (preto/branco)"]["theme"], "Escuro", "", False, 0, False, False, [], [], {}, {}, {}
        self.app_icon = "Custom Transparent.ico"
        self.config_manager.delete_config_file()
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
            
        # Instancia a nossa nova Aba Customizada e Inteligente
        browser = BrowserTab(self, self.profile, url, title, is_pinned, lazy_load)
        
        # Adiciona no TabWidget
        index = self.tabs.addTab(browser, f"📌 {title[:18]}..." if is_pinned else title[:20])
        
        if not lazy_load:
            self.tabs.setCurrentIndex(index)
            
        if not getattr(self, 'is_restoring', False) and not url.startswith("about:"): 
            self.log_history(title, url)
            
        if not getattr(self, 'is_restoring', False): 
            self.save_settings(force=True)

    def update_tab_title(self, browser, title):
        """Método simples chamado pela própria aba quando ela troca de nome"""
        index = self.tabs.indexOf(browser)
        if index != -1:
            title = "Navegação" if not title.strip() else title
            browser.setProperty("original_label", title)
            self.tabs.setTabText(index, f"📌 {title[:18]}..." if browser.property("is_pinned") else title[:20])
            if getattr(self, 'save_tabs_enabled', False) and not getattr(self, 'is_restoring', False): 
                self.save_settings(force=True)

    def sync_all_whatsapp_themes(self):
        """Apenas manda as abas atualizarem seus próprios temas"""
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, BrowserTab): 
                widget.apply_whatsapp_theme(ok=True)

    def track_zoom_levels(self):
        for i in range(1, self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QWebEngineView):
                url = widget.property("original_url") or widget.url().toString()
                if url and url != "about:blank": self.zoom_settings[url] = widget.zoomFactor()

    def open_security_setup(self):
        from ui.dialogs import SecuritySetupDialog, SecurityModifyDialog
        
        if getattr(self, 'security_settings', {}) and self.security_settings.get("enabled", False):
            dialog = SecurityModifyDialog(self, self.security_settings)
        else:
            dialog = SecuritySetupDialog(self, self.security_settings)
            
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.security_settings = dialog.final_data
            self.save_settings(force=True)

    def close_tab(self, index):
        if index != 0:
            if self.tabs.widget(index): self.tabs.widget(index).deleteLater()
            self.tabs.removeTab(index)
            if not getattr(self, 'is_restoring', False): self.save_settings(force=True)

    def restore_tabs(self):
        self.is_restoring = True
        for t in getattr(self, 'pinned_tabs', []): self.open_web_tab(t["url"], t["label"], is_pinned=True, lazy_load=True)
        if getattr(self, 'save_tabs_enabled', False) and self.opened_tabs_urls:
            for t in list(self.opened_tabs_urls):
                if not any(p["url"] == t["url"] for p in getattr(self, 'pinned_tabs', [])): self.open_web_tab(t["url"], t["label"], is_pinned=False, lazy_load=False)
        QTimer.singleShot(200, lambda: [setattr(self, 'is_restoring', False), self.tabs.setCurrentIndex(0)])