import os
import hashlib
from PyQt6.QtWidgets import (QApplication, QPushButton, QLabel, QFrame, QGridLayout, 
                             QMenu, QMessageBox, QVBoxLayout, QWidget, QTabWidget, 
                             QLineEdit, QDialog)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QPixmap, QColor, QDrag, QPainter
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

# Importações do Core
from core.remote_tools import launch_remote_tool

class DraggableToolButton(QFrame):
    def __init__(self, item_data, item_index, parent_hub, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.item_index = item_index
        self.hub = parent_hub
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        self.internal_layout = QVBoxLayout(self)
        self.internal_layout.setContentsMargins(6, 6, 6, 12)
        self.internal_layout.setSpacing(6)
        
        self.icon_area = QFrame()
        self.icon_area.setFixedHeight(85)
        self.icon_area.setStyleSheet("background-color: rgba(0, 0, 0, 0.15); border-radius: 8px; border: none;")
        self.icon_layout = QGridLayout(self.icon_area)
        self.icon_layout.setContentsMargins(8, 8, 8, 8)
        
        self.btn_star = QPushButton()
        self.btn_star.setFixedSize(20, 20)
        self.btn_star.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_star.clicked.connect(self.toggle_favorite)
        
        self.btn_delete = QPushButton("✕")
        self.btn_delete.setFixedSize(20, 20)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet("QPushButton { background: transparent; color: rgba(255,82,82,0.8); font-weight: bold; border: none; font-size: 14px; } QPushButton:hover { color: #ff0000; }")
        self.btn_delete.clicked.connect(self.confirm_delete)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.icon_lbl.setStyleSheet("background: transparent;")
        
        icon_name = f"{self.item_data['label'].lower()}.png"
        icon_path = os.path.join(self.hub.icons_dir, icon_name)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.icon_lbl.setPixmap(pixmap)
        
        self.icon_layout.addWidget(self.btn_star, 0, 0, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.icon_layout.addWidget(self.btn_delete, 0, 2, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.icon_layout.addWidget(self.icon_lbl, 0, 0, 2, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        self.internal_layout.addWidget(self.icon_area)
        
        self.title_lbl = QLabel(self.item_data['label'])
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        subtitle_text = self.item_data.get("subtitle", "")
        self.subtitle_lbl = QLabel(subtitle_text)
        self.subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        if not subtitle_text: self.subtitle_lbl.hide()
            
        self.internal_layout.addWidget(self.title_lbl)
        self.internal_layout.addWidget(self.subtitle_lbl)
        self.update_star_visual()

    def update_card_style(self):
        self.setObjectName("Card")
        accent = self.hub.accent_color
        c_accent = QColor(accent)
        card_text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
        sub_text_color = "rgba(7, 8, 10, 0.65)" if c_accent.lightness() > 140 else "rgba(255, 255, 255, 0.75)"
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"
        
        self.title_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {card_text_color}; background: transparent; border: none;")
        self.subtitle_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {sub_text_color}; background: transparent; border: none;")
        
        is_fav = self.item_data.get("favorite", False)
        border_bottom = "4px solid #ffeb3b" if is_fav else "1px solid rgba(0,0,0,0.3)"
        
        self.setStyleSheet(f"""
            QFrame#Card {{ background-color: {accent}; border: 1px solid rgba(0,0,0,0.3); border-bottom: {border_bottom}; border-radius: 12px; }}
            QFrame#Card:hover {{ background-color: {hover_dark_tint}; border: 1px solid {accent}; border-bottom: {border_bottom}; }}
        """)

    def update_star_visual(self):
        is_fav = self.item_data.get("favorite", False)
        accent = QColor(self.hub.accent_color)
        off_color = "rgba(0, 0, 0, 0.5)" if accent.lightness() > 140 else "rgba(255, 255, 255, 0.5)"
        color = "#ffeb3b" if is_fav else off_color
        self.btn_star.setStyleSheet(f"QPushButton {{ background: transparent; color: {color}; border: none; font-size: 18px; }} QPushButton:hover {{ color: #ffeb3b; }}")
        self.btn_star.setText("★" if is_fav else "☆")
        self.update_card_style()

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background-color: #161b24; color: #fff; border: 1px solid {self.hub.accent_color}; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; border-radius: 4px; padding: 5px; }} QMenu::item {{ padding: 8px 25px; border-radius: 4px; }} QMenu::item:selected {{ background-color: {self.hub.accent_color}; color: #000; }}")
        edit_action = menu.addAction("✏️ Editar Botão")
        action = menu.exec(self.mapToGlobal(pos))
        if action == edit_action: self.hub.edit_button_dialog(self.item_data)

    def toggle_favorite(self):
        self.item_data["favorite"] = not self.item_data.get("favorite", False)
        self.update_star_visual()
        self.hub.save_settings(force=True)
        self.hub.update_favorites_panel()

    def confirm_delete(self):
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Deseja apagar o botão '{self.item_data['label']}'? SIM OU NÃO.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: self.hub.delete_button_by_data(self.item_data)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.__drag_start_pos = event.pos()
            self.__drag_occurred = False 
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.MouseButton.LeftButton: return
        if (event.pos() - self.__drag_start_pos).manhattanLength() < QApplication.startDragDistance(): return
        self.__drag_occurred = True
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.item_index))
        drag.setMimeData(mime_data)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.pos())
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()

    def dropEvent(self, event):
        try:
            source_index = int(event.mimeData().text())
            target_index = self.item_index
            if source_index != target_index:
                self.hub.reorder_buttons(source_index, target_index)
                event.acceptProposedAction()
        except ValueError: pass

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
                try: launch_remote_tool(tool)
                except: pass
            else: self.hub.open_web_tab(url, label)
        super().mouseReleaseEvent(event)


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
        if hasattr(window, 'track_tabs_after_move'): window.track_tabs_after_move()

class LockScreenWidget(QWidget):
    def __init__(self, parent, security_data):
        super().__init__(parent)
        self.hub = parent
        self.security_data = security_data
        self.attempts = 0
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.panel_container = QWidget(self)
        self.panel_layout = QVBoxLayout(self.panel_container)
        self.panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.panel = QFrame()
        self.panel.setFixedSize(450, 480)
        self.panel.setStyleSheet(f"""
            QFrame {{ background-color: rgba(17, 20, 26, 0.85); border: 2px solid {self.hub.accent_color}; border-radius: 20px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; border: none; background: transparent; }}
            QLineEdit {{ background-color: rgba(0, 0, 0, 0.5); border: 1px solid {self.hub.accent_color}; border-radius: 8px; color: #fff; padding: 12px; font-family: 'Segoe UI'; font-size: 15px; font-weight: bold; text-transform: uppercase; }}
            QPushButton {{ background-color: {self.hub.accent_color}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 12px; border-radius: 8px; font-size: 14px; }}
            QPushButton:hover {{ background-color: #ffffff; }}
        """)
        
        self.inner_layout = QVBoxLayout(self.panel)
        self.inner_layout.setContentsMargins(40, 40, 40, 40)
        self.inner_layout.setSpacing(20)
        
        self.icon_lbl = QLabel("👤")
        self.icon_lbl.setStyleSheet(f"font-size: 60px; color: {self.hub.accent_color};")
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        first_name = self.security_data.get('name', 'Usuário').split(' ')[0]
        self.lbl_greeting = QLabel(f"Olá! {first_name},\ndigite sua senha para acessar:")
        self.lbl_greeting.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center;")
        self.lbl_greeting.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.input_pwd = QLineEdit()
        self.input_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pwd.setPlaceholderText("Senha secreta...")
        self.input_pwd.returnPressed.connect(self.check_password)
        
        self.btn_unlock = QPushButton("Acessar o Hub")
        self.btn_unlock.clicked.connect(self.check_password)
        
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #ff5252; font-size: 13px; font-weight: bold;")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_hint = QLabel(f"Dica: {self.security_data.get('hint', '')}")
        self.lbl_hint.setStyleSheet("color: #8a909d; font-size: 12px;")
        self.lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.inner_layout.addStretch()
        self.inner_layout.addWidget(self.icon_lbl)
        self.inner_layout.addWidget(self.lbl_greeting)
        self.inner_layout.addSpacing(10)
        self.inner_layout.addWidget(self.input_pwd)
        self.inner_layout.addWidget(self.btn_unlock)
        self.inner_layout.addWidget(self.lbl_error)
        self.inner_layout.addWidget(self.lbl_hint)
        self.inner_layout.addStretch()
        
        self.panel_layout.addWidget(self.panel)
        self.layout.addWidget(self.panel_container)
        
        self.input_key = QLineEdit()
        self.input_key.setPlaceholderText("Chave Mestra (Ex: FIUZA-XXXX-XXXX)")
        self.input_key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_key.setVisible(False)
        self.input_key.returnPressed.connect(self.validate_master_key)
        
        self.btn_validate = QPushButton("Validar Chave")
        self.btn_validate.setVisible(False)
        self.btn_validate.clicked.connect(self.validate_master_key)
        
        self.inner_layout.insertWidget(4, self.input_key)
        self.inner_layout.insertWidget(5, self.btn_validate)

    def paintEvent(self, event):
        painter = QPainter(self)
        bg_path = self.security_data.get('image', '')
        if bg_path and os.path.exists(bg_path):
            pixmap = QPixmap(bg_path).scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - pixmap.width()) // 2
            y = (self.height() - pixmap.height()) // 2
            painter.drawPixmap(x, y, pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160)) 

    def check_password(self):
        pwd = self.input_pwd.text().strip()
        hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest()
        
        if hashed_pwd == self.security_data.get('password_hash'):
            self.hub.centralWidget().setGraphicsEffect(None)
            self.hide()
            self.deleteLater()
        else:
            self.attempts += 1
            self.input_pwd.clear()
            self.lbl_error.setText("Usuário ou senha incorreta.")
            if self.attempts >= 3:
                self.trigger_recovery()

    def trigger_recovery(self):
        self.input_pwd.setVisible(False)
        self.btn_unlock.setVisible(False)
        self.lbl_hint.setVisible(False)
        
        self.lbl_error.setStyleSheet("color: #ffeb3b; font-size: 13px; font-weight: bold;")
        self.lbl_error.setText("Bloqueio Ativo.\nPor favor, informe a sua Chave Mestra\nde Recuperação.")
        
        self.input_key.setVisible(True)
        self.btn_validate.setVisible(True)

    def validate_master_key(self):
        master_key_input = self.input_key.text().strip().upper()
        hashed_input = hashlib.sha256(master_key_input.encode()).hexdigest()
        
        if hashed_input == self.security_data.get('master_key_hash'):
            self.input_key.clear()
            from ui.dialogs import SecuritySetupDialog
            dialog = SecuritySetupDialog(self.hub, self.security_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.hub.security_settings = dialog.final_data
                self.hub.save_settings(force=True)
                self.security_data = self.hub.security_settings
                self.hub.centralWidget().setGraphicsEffect(None)
                self.hide()
                self.deleteLater()
        else:
            self.lbl_error.setStyleSheet("color: #ff5252; font-size: 13px; font-weight: bold;")
            self.lbl_error.setText("Chave Mestra Inválida!")
            self.input_key.clear()