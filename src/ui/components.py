import os
import hashlib
import subprocess
import ctypes
from PyQt6.QtWidgets import (QApplication, QPushButton, QLabel, QFrame, QGridLayout, 
                             QMenu, QMessageBox, QVBoxLayout, QWidget, QTabWidget, 
                             QLineEdit, QDialog, QHBoxLayout, QFileDialog, QGraphicsDropShadowEffect,
                             QComboBox, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QMimeData, QUrl, QPoint, QTimer, QPointF, QVariantAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QPixmap, QColor, QDrag, QPainter, QIcon, QShortcut, QKeySequence, QPainterPath, QPen
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from core.remote_tools import launch_remote_tool
from core.image_utils import process_and_save_icon

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
        
        icon_name = "folder_icon.png" if self.item_data.get("type") == "folder" else f"{self.item_data.get('label', '').lower()}.png"
        icon_path = os.path.join(self.hub.icons_dir, icon_name)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.icon_lbl.setPixmap(pixmap)
        elif self.item_data.get("type") == "folder":
            self.icon_lbl.setText("📁")
            self.icon_lbl.setStyleSheet("font-size: 30px;")
            
        self.icon_layout.addWidget(self.btn_star, 0, 0, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.icon_layout.addWidget(self.btn_delete, 0, 2, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.icon_layout.addWidget(self.icon_lbl, 0, 0, 2, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        self.internal_layout.addWidget(self.icon_area)
        
        self.title_lbl = QLabel(self.item_data.get('label', ''))
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

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(10)
        self.shadow.setOffset(0, 5)
        self.shadow.setColor(QColor(0, 0, 0, 80)) 
        self.setGraphicsEffect(self.shadow)

        self.anim_lift = QVariantAnimation(self)
        self.anim_lift.setDuration(150)
        self.anim_lift.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim_lift.valueChanged.connect(self.update_lift)

    def refresh_icon(self):
        icon_name = f"{self.item_data.get('label', '').lower()}.png"
        icon_path = os.path.join(self.hub.icons_dir, icon_name)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.icon_lbl.setPixmap(pixmap)

    def update_card_style(self):
        self.setObjectName("Card")
        accent = self.hub.accent_color
        c_accent = QColor(accent)
        card_text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
        sub_text_color = "rgba(7, 8, 10, 0.65)" if c_accent.lightness() > 140 else "rgba(255, 255, 255, 0.75)"
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"
        
        bg_style = f"background-color: {accent};"
        
        if self.item_data.get("type") == "folder":
            folder_name = self.item_data.get("label", "").lower()
            icon_path = os.path.join(self.hub.icons_dir, f"folder_{folder_name}.png")
            if os.path.exists(icon_path):
                bg_style = f"background-image: url('{icon_path.replace(chr(92), '/')}'); background-position: center; background-repeat: no-repeat;"
        else:
            bg_img = self.item_data.get("image_path", "")
            if bg_img and os.path.exists(bg_img):
                bg_style = f"background-image: url('{bg_img.replace(chr(92), '/')}'); background-position: center; background-repeat: no-repeat; background-size: contain;"

        self.title_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {card_text_color}; background: transparent; border: none;")
        self.subtitle_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {sub_text_color}; background: transparent; border: none;")
        
        is_fav = self.item_data.get("favorite", False)
        border_bottom = "4px solid #ffeb3b" if is_fav else "1px solid rgba(0,0,0,0.3)"
        
        self.setStyleSheet(f"""
            QFrame#Card {{ {bg_style} border: 1px solid rgba(0,0,0,0.3); border-bottom: {border_bottom}; border-radius: 12px; }}
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
        
        edit_action = menu.addAction("✏️ Editar")
        swap_action = menu.addAction("🔄 Substituir")
        menu.addSeparator()

        is_folder = self.item_data.get("type") == "folder"
        from PyQt6.QtWidgets import QDialog
        is_in_folder = isinstance(self.window(), QDialog) and hasattr(self.window(), 'folder_data')
        
        send_to_folder_action = None
        send_to_home_action = None
        
        if not is_folder:
            if is_in_folder:
                send_to_home_action = menu.addAction("🏠 Enviar para a Home")
            else:
                send_to_folder_action = menu.addAction("📤 Enviar para Pasta...")
                
        action = menu.exec(self.mapToGlobal(pos))
        
        if action == edit_action: 
            self.hub.edit_button_dialog(self.item_data)
        elif action == swap_action:
            from ui.components import SwapButtonDialog
            dialog = SwapButtonDialog(self.hub, self.item_data)
            dialog.exec()
        elif send_to_home_action and action == send_to_home_action:
            if hasattr(self.hub, 'move_item_to_home'):
                self.hub.move_item_to_home(self.item_data)
                if hasattr(self.window(), 'refresh_grid'): self.window().refresh_grid()
        elif send_to_folder_action and action == send_to_folder_action:
            from ui.components import SendToFolderDialog
            dialog = SendToFolderDialog(self.hub, self.item_data)
            dialog.exec()

    def toggle_favorite(self):
        self.item_data["favorite"] = not self.item_data.get("favorite", False)
        self.update_star_visual()
        self.hub.save_settings(force=True)
        self.hub.update_favorites_panel()

    def confirm_delete(self):
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Deseja apagar '{self.item_data.get('label', 'este item')}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.hub.delete_button_by_data(self.item_data)
            parent_window = self.window()
            if hasattr(parent_window, 'refresh_grid'):
                parent_window.refresh_grid()
            else:
                self.hub.filter_buttons_by_search(self.hub.search_filter)

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
        # Envia a ID única da memória RAM
        mime_data.setText(str(id(self.item_data))) 
        drag.setMimeData(mime_data)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.pos())
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + "\nQFrame#Card { border: 2px solid #ffffff; background-color: rgba(255,255,255,0.2); }")

    def dragLeaveEvent(self, event):
        self.update_card_style() 

    def dropEvent(self, event):
        try: source_id = int(event.mimeData().text())
        except ValueError: return
        
        target_item = self.item_data
        self.update_card_style() 
        
        if hasattr(self.hub, 'get_item_by_id'):
            source_item = self.hub.get_item_by_id(source_id)
            if source_item and id(source_item) != id(target_item):
                if hasattr(self.hub, 'swap_items'):
                    self.hub.swap_items(source_item, target_item)
                event.acceptProposedAction()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if getattr(self, '__drag_occurred', False):
                self.__drag_occurred = False
                return
            
            if self.item_data.get("type") == "folder":
                from ui.components import FolderPanelWidget 
                panel = FolderPanelWidget(self.hub, self.item_data)
                panel.exec()
            else:
                if isinstance(self.window(), QDialog): self.window().accept()
                url = self.item_data.get("url", "")
                
                if url.startswith("media://"):
                    file_path = url.replace("media://", "")
                    if os.path.exists(file_path):
                        player = MediaViewerDialog(self.hub, file_path)
                        player.exec()
                    else:
                        QMessageBox.warning(self, "Erro", "Arquivo não encontrado!")
                
                elif url.lower().endswith(('.exe', '.bat', '.cmd', '.lnk')) or os.path.isfile(url):
                    exe_path = os.path.normpath(url)
                    exe_name = os.path.splitext(os.path.basename(exe_path))[0]
                    
                    try:
                        EnumWindows = ctypes.windll.user32.EnumWindows
                        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
                        GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
                        IsWindowVisible = ctypes.windll.user32.IsWindowVisible
                        
                        out = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {exe_name}*" /FO CSV /NH', shell=True, text=True)
                        pids = []
                        for line in out.strip().split('\n'):
                            parts = line.split('","')
                            if len(parts) > 1 and exe_name.lower() in parts[0].lower():
                                pids.append(int(parts[1].replace('"', '')))

                        if not pids:
                            os.startfile(exe_path)
                        else:
                            found_hwnd = None
                            def foreach_window(hwnd, lParam):
                                nonlocal found_hwnd
                                if IsWindowVisible(hwnd):
                                    pid = ctypes.c_ulong()
                                    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                                    if pid.value in pids:
                                        found_hwnd = hwnd
                                        return False 
                                return True
                            
                            EnumWindows(EnumWindowsProc(foreach_window), 0)
                            
                            if found_hwnd:
                                ctypes.windll.user32.ShowWindow(found_hwnd, 9) 
                                ctypes.windll.user32.SetForegroundWindow(found_hwnd)
                            else:
                                os.startfile(exe_path)
                    except Exception as e:
                        QMessageBox.warning(self, "Erro", f"Falha ao abrir:\n{e}")
                
                elif url.startswith("remote://"):
                    try: launch_remote_tool(url.split("//")[1])
                    except: pass
                else: 
                    self.hub.open_web_tab(url, self.item_data.get("label", ""))

    def update_lift(self, value):
        self.internal_layout.setContentsMargins(6, 6 - int(value), 6, 12 + int(value))

    def enterEvent(self, event):
        self.anim_lift.setStartValue(0)
        self.anim_lift.setEndValue(4) 
        self.anim_lift.start()
        
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 8)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim_lift.setStartValue(4)
        self.anim_lift.setEndValue(0)
        self.anim_lift.start()
        
        self.shadow.setBlurRadius(10)
        self.shadow.setOffset(0, 5)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        super().leaveEvent(event)


class MediaViewerDialog(QDialog):
    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.file_path = file_path
        self.setFixedSize(800, 550)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setStyleSheet("""
            QDialog { background-color: rgba(17, 20, 26, 0.95); border: 2px solid #10b981; border-radius: 12px; }
            QLabel { color: white; font-weight: bold; background: transparent; border: none; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        header = QHBoxLayout()
        title = QLabel(os.path.basename(file_path))
        title.setStyleSheet("font-size: 16px;")
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("QPushButton { background-color: #ff5252; color: white; border-radius: 15px; font-weight: bold; } QPushButton:hover { background-color: #ff0000; }")
        btn_close.clicked.connect(self.close_player)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_close)
        layout.addLayout(header)
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            self.img_label = QLabel()
            self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap(file_path)
            self.img_label.setPixmap(pixmap.scaled(750, 450, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            layout.addWidget(self.img_label)
            
        elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
            self.video_widget = QVideoWidget()
            self.video_widget.setStyleSheet("border: 1px solid #333; background-color: #000;")
            layout.addWidget(self.video_widget)
            
            self.audio_output = QAudioOutput()
            self.media_player = QMediaPlayer()
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.setVideoOutput(self.video_widget)
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            
            controls = QHBoxLayout()
            btn_play = QPushButton("▶ Play")
            btn_pause = QPushButton("⏸ Pause")
            
            for btn in [btn_play, btn_pause]:
                btn.setMinimumHeight(35)
                btn.setStyleSheet("QPushButton { background-color: #10b981; color: #000; font-weight: bold; border-radius: 6px; } QPushButton:hover { background-color: #059669; }")
            
            btn_play.clicked.connect(self.media_player.play)
            btn_pause.clicked.connect(self.media_player.pause)
            
            controls.addWidget(btn_play)
            controls.addWidget(btn_pause)
            layout.addLayout(controls)
            
            self.media_player.play()
            
    def close_player(self):
        if hasattr(self, 'media_player'):
            self.media_player.stop()
        self.accept()


class FolderCableFrame(QFrame):
    def __init__(self, parent_panel):
        super().__init__()
        self.panel = parent_panel
        self.dash_offset = 0
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(40)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(f"FolderCableFrame {{ background-color: rgba(0,0,0,0.25); border: 1px solid {self.panel.hub.accent_color}; border-radius: 10px; }}")

    def update_animation(self):
        self.dash_offset -= 2
        if self.dash_offset < -100: self.dash_offset = 0
        self.update()

    def paintEvent(self,event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cards = []

        widgets = self.findChildren(DraggableToolButton)
        for widget in widgets:
            if widget.isVisible():
                pos = widget.mapTo(self, QPoint(widget.width()//2, widget.height()//2))
                cards.append(pos)

        if len(cards) < 2:
            painter.end()
            return

        accent = QColor(self.panel.hub.accent_color)
        shadow_pen = QPen(QColor(0,0,0,120), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        cable_pen = QPen(QColor(5,5,5,230), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        glow_pen = QPen(accent, 3, Qt.PenStyle.CustomDashLine, Qt.PenCapStyle.RoundCap)
        glow_pen.setDashPattern([8, 16])
        glow_pen.setDashOffset(self.dash_offset)

        for i in range(len(cards)-1):
            p1 = QPointF(cards[i])
            p2 = QPointF(cards[i+1])
            path = QPainterPath()
            path.moveTo(p1)
            curva = 60
            path.cubicTo(QPointF(p1.x(), p1.y()+curva), QPointF(p2.x(), p2.y()+curva), p2)

            painter.setPen(shadow_pen)
            painter.drawPath(path)
            painter.setPen(cable_pen)
            painter.drawPath(path)
            painter.setPen(glow_pen)
            painter.drawPath(path)

        painter.end()

class FolderPanelWidget(QDialog):
    def __init__(self, parent_hub, folder_data):
        super().__init__(parent_hub)
        self.hub = parent_hub
        self.folder_data = folder_data
        self.current_page = 0
        self.items_per_page = 8
        self.search_filter = "" 
        
        self.setFixedSize(944,760)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        
        self.setStyleSheet(f"QDialog {{ background-color: rgba(17, 20, 26, 0.85); border: 2px solid {folder_data.get('color', self.hub.accent_color)}; border-radius: 12px; }} QLabel {{ background: transparent; border: none; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 25)
        layout.setSpacing(3)
        
        self.header_frame = QFrame()
        self.header_frame.setObjectName("HeaderFrame")
        self.header_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_frame.mousePressEvent = self.change_header_image
        self.header_frame.setAcceptDrops(True) 
        self.update_header_visuals() 
        
        header_layout = QVBoxLayout(self.header_frame)
        self.search_bar = QLineEdit()
        
        folder_label = self.folder_data.get("label", "Desconhecida")
        self.search_bar.setPlaceholderText(f"Digite aqui para pesquisar... [Pasta: {folder_label}]")
        self.search_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_bar.setStyleSheet(f"QLineEdit {{ background: rgba(0, 0, 0, 0.6); border: 1px solid {self.hub.accent_color}; color: #fff; font-size: 16px; font-weight: bold; border-radius: 6px; padding: 8px; }} QLineEdit:focus {{ background: rgba(0, 0, 0, 0.8); border: 2px solid #ffffff; }}")
        self.search_bar.textChanged.connect(self.filter_items)
        header_layout.addWidget(self.search_bar)
        layout.addWidget(self.header_frame)
        
        self.grid_frame = FolderCableFrame(self)
        self.grid_frame.setFixedHeight(330)
        self.grid_layout = QGridLayout(self.grid_frame)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(10, 5, 10, 5)
        layout.addWidget(self.grid_frame)
        layout.setStretchFactor(self.grid_frame, 1)
        
        self.nav_frame = QFrame()
        self.nav_frame.setObjectName("NavFrame")
        self.nav_frame.setFixedHeight(50)
        self.nav_frame.setStyleSheet(f"#NavFrame {{ border: 2px solid {self.hub.accent_color}; border-radius: 8px; background-color: rgba(0, 0, 0, 0.4); }}")
        
        nav_layout = QHBoxLayout(self.nav_frame)
        self.btn_prev = QPushButton("<")
        self.btn_next = QPushButton(">")
        self.page_label = QLabel("Página 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("color: #fff; font-weight: bold; font-size: 16px;")
        
        for btn in [self.btn_prev, self.btn_next]:
            btn.setFixedSize(60, 40)
            btn.setStyleSheet(f"QPushButton {{ background-color: {self.hub.accent_color}; color: #000; font-weight: bold; font-size: 18px; border-radius: 6px; }} QPushButton:hover {{ background-color: #ffffff; }}")
            
        self.btn_prev.clicked.connect(lambda: self.change_page(-1))
        self.btn_next.clicked.connect(lambda: self.change_page(1))
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.btn_next)
        layout.addWidget(self.nav_frame)
        
        self.shortcut_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_left.activated.connect(lambda: self.change_page(-1))
        self.shortcut_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_right.activated.connect(lambda: self.change_page(1))
        
        btn_add = QPushButton("➕ Adicionar Botão nesta Pasta")
        btn_add.setMinimumHeight(45)
        btn_add.setStyleSheet(f"QPushButton {{ background-color: {self.hub.accent_color}; color: #000; font-weight: bold; border-radius: 6px; }} QPushButton:hover {{ background-color: #ffffff; }}")
        btn_add.clicked.connect(self.add_button_to_folder)
        layout.addWidget(btn_add, 0)
        
        btn_back = QPushButton("Voltar / Fechar")
        btn_back.setMinimumHeight(45)
        btn_back.setStyleSheet(f"QPushButton {{ background-color: #161b24; color: #fff; font-weight: bold; border-radius: 6px; border: 1px solid {self.hub.accent_color}; }} QPushButton:hover {{ background-color: {self.hub.accent_color}; color: #000; }}")
        btn_back.clicked.connect(self.accept)
        layout.addWidget(btn_back, 0)
        
        self.refresh_grid()
        self.setFocus()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        added = False
        
        for file_path in files:
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.mp4', '.mkv', '.avi', '.mov', '.gif']:
                    name = os.path.basename(file_path)
                    if "buttons" not in self.folder_data: self.folder_data["buttons"] = []
                    new_btn = {"label": name[:12] + "..." if len(name) > 12 else name, "subtitle": "Mídia Local", "url": f"media://{file_path}", "image_path": file_path if ext in ['.png', '.jpg', '.jpeg'] else ""}
                    self.folder_data["buttons"].append(new_btn)
                    added = True
        
        if added:
            self.hub.save_settings(force=True)
            self.current_page = (len(self.folder_data["buttons"]) - 1) // self.items_per_page
            self.search_bar.clear()
            self.refresh_grid()

    def showEvent(self, event):
        super().showEvent(event)
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y - 50)

    def update_header_visuals(self):
        bg_img = self.folder_data.get("header_bg", "")
        base_style = f"border: 2px solid {self.hub.accent_color}; border-radius: 8px; background-color: rgba(0, 0, 0, 0.4);"
        hover_style = "border-color: #ffffff; background-color: rgba(0, 0, 0, 0.6);"
        if bg_img and os.path.exists(bg_img):
            base_style += f" background-image: url('{bg_img.replace(chr(92), '/')}'); background-position: center; background-size: cover; background-repeat: no-repeat;"
        self.header_frame.setStyleSheet(f"#HeaderFrame {{ {base_style} }} #HeaderFrame:hover {{ {hover_style} }}")

    def change_header_image(self, event):
        if self.search_bar.geometry().contains(event.pos()): return
        path, _ = QFileDialog.getOpenFileName(self, "Imagem de Fundo do Cabeçalho", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            name = self.folder_data.get("label", "folder").lower()
            dest = os.path.join(self.hub.icons_dir, f"{name}_header.png")
            process_and_save_icon(path, dest)
            self.folder_data["header_bg"] = dest
            self.hub.save_settings(force=True)
            self.update_header_visuals()

    def filter_items(self, text):
        self.search_filter = text.strip().lower()
        self.current_page = 0
        self.refresh_grid()

    def refresh_grid(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        all_items = self.folder_data.get("buttons", [])
        if self.search_filter:
            all_items = [b for b in all_items if self.search_filter in b.get("label", "").lower()]
            
        start = self.current_page * self.items_per_page
        page_items = all_items[start:start+self.items_per_page]
        
        self.page_label.setText(f"Página {self.current_page + 1}")
        self.hub.render_grid(self.grid_layout, page_items)
        
        max_pages = max(0, (len(all_items) - 1) // self.items_per_page)
        self.btn_next.setEnabled(self.current_page < max_pages)
        self.btn_prev.setEnabled(self.current_page > 0)

    def change_page(self, delta):
        all_items = self.folder_data.get("buttons", [])
        if self.search_filter: all_items = [b for b in all_items if self.search_filter in b.get("label", "").lower()]
        max_p = max(0, (len(all_items) - 1) // self.items_per_page) if all_items else 0
        self.current_page = max(0, min(self.current_page + delta, max_p))
        self.refresh_grid()

    def add_button_to_folder(self):
        if "buttons" not in self.folder_data: self.folder_data["buttons"] = []
        self.folder_data["buttons"].append({"label": "Novo Item", "url": "https://google.com"})
        self.hub.save_settings(force=True)
        self.current_page = (len(self.folder_data["buttons"]) - 1) // self.items_per_page
        self.search_bar.clear()
        self.refresh_grid()

    def accept(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        super().accept()

class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)  
        self.tabBar().tabMoved.connect(self.handle_tab_moved)
    def handle_tab_moved(self, from_idx, to_idx):
        if from_idx == 0 or to_idx == 0: return
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

class ThemeSelectorButton(QPushButton):
    def __init__(self, hub, parent=None):
        super().__init__(parent)
        self.hub = hub
        self.setFixedSize(40, 40) 
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Alterar Tema e Ícone do Custom Explorer")
        self.clicked.connect(self.show_theme_menu) 
        self.update_visual()

    def update_visual(self):
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QIcon

        current_icon = getattr(self.hub, 'app_icon', "Custom Transparent.ico")
        icon_path = os.path.join(self.hub.icons_dir, current_icon)
        
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(22, 22)) 
            
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #161b24;
                    border: 2px solid {self.hub.accent_color};
                    border-radius: 20px; 
                }}
                QPushButton:hover {{
                    border: 2px solid #ffffff;
                    background-color: rgba(255, 255, 255, 0.1);
                }}
            """)
        else:
            self.setIcon(QIcon())
            self.setStyleSheet(f"QPushButton {{ background-color: {self.hub.accent_color}; border: 2px solid #fff; border-radius: 20px; }}")

    def show_theme_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: #161b24; color: #fff; border: 1px solid {self.hub.accent_color}; font-size: 14px; font-weight: bold; padding: 5px; border-radius: 8px; }}
            QMenu::item {{ padding: 10px 30px 10px 15px; border-radius: 4px; margin: 2px; }}
            QMenu::item:selected {{ background-color: {self.hub.accent_color}; color: #000; }}
        """)

        themes = {
            "Tema Azul": ("Custom Blue.ico", "#2196F3"),
            "Tema Verde": ("Custom Green.ico", "#4CAF50"),
            "Tema Laranja": ("Custom Orange.ico", "#FF9800"),
            "Tema Rosa": ("Custom Pink.ico", "#E91E63"),
            "Tema Roxo": ("Custom Purple.ico", "#9C27B0"),
            "Tema Vermelho": ("Custom Red.ico", "#F44336"),
            "Tema Branco": ("Custom White.ico", "#FFFFFF"),
            "Tema Amarelo": ("Custom Yellow.ico", "#FFEB3B"),
            "Tema Padrão": ("Custom Transparent.ico", "#10b981")
        }

        for name, (filename, color) in themes.items():
            icon_path = os.path.join(self.hub.icons_dir, filename)
            action = menu.addAction(QIcon(icon_path) if os.path.exists(icon_path) else QIcon(), name)
            action.setData((filename, color))

        menu_height = len(themes) * 36 + 10 
        pos = self.mapToGlobal(QPoint(0, -menu_height))
        
        selected_action = menu.exec(pos)

        if selected_action:
            filename, new_color = selected_action.data()
            self.apply_theme_instantly(filename, new_color)

    def apply_theme_instantly(self, filename, new_color):
        self.hub.accent_color = new_color
        self.hub.app_icon = filename
        self.hub.save_settings(force=True)
        
        icon_path = os.path.join(self.hub.icons_dir, filename)
        if os.path.exists(icon_path):
            self.window().setWindowIcon(QIcon(icon_path))
        
        self.update_visual()
        
        if hasattr(self.hub, 'apply_styles'):
            self.hub.apply_styles()
            
        if hasattr(self.hub, 'btn_ops_home'):
            c_accent = QColor(new_color)
            btn_text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
            style = f"""
                QPushButton {{ background-color: {new_color}; border: 1px solid rgba(0,0,0,0.3); border-radius: 8px; color: {btn_text_color}; font-weight: bold; letter-spacing: 2px; }}
                QPushButton:hover {{ background-color: rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40); border: 1px solid {new_color}; color: #ffffff; }}
            """
            self.hub.btn_ops_home.setStyleSheet(style)
            self.hub.btn_config_home.setStyleSheet(style)
            
        if hasattr(self.hub, 'filter_buttons_by_search'):
            self.hub.filter_buttons_by_search(self.hub.search_filter)


# --- NOVO PAINEL: ENVIAR PARA PASTA ---
class SendToFolderDialog(QDialog):
    def __init__(self, parent_hub, current_item):
        super().__init__(parent_hub)
        self.hub = parent_hub
        self.current_item = current_item
        
        self.setWindowTitle("Enviar para Pasta")
        self.setFixedSize(400, 450)
        self.setWindowOpacity(0.95)
        
        accent = self.hub.accent_color
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {accent}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; }}
            QListWidget {{ background-color: #161b24; border: 1px solid {accent}; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; font-size: 15px; font-weight: bold; outline: none; }}
            QListWidget::item {{ padding: 12px; border-radius: 6px; border-bottom: 1px solid #1c212d; }}
            QListWidget::item:hover {{ background-color: rgba(255, 255, 255, 0.1); }}
            QListWidget::item:selected {{ background-color: {accent}; color: #000; }}
            QPushButton {{ background-color: {accent}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
            QPushButton#btn_cancel {{ background-color: #161b24; color: #fff; border: 1px solid #232a38; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        lbl_info = QLabel(f"Enviar [ {self.current_item.get('label', '')} ] para:")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)
        
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.execute_send)
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        self.btn_back = QPushButton("Cancelar")
        self.btn_back.setObjectName("btn_cancel")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.reject)
        
        self.btn_confirm = QPushButton("📤 Confirmar Envio")
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.clicked.connect(self.execute_send)
        self.btn_confirm.setEnabled(False)
        
        btn_layout.addWidget(self.btn_back)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)
        
        self.populate_folders()

    def populate_folders(self):
        folders = [f for f in self.hub.buttons_list if f.get("type") == "folder"]
        if not folders:
            self.list_widget.addItem("Nenhuma pasta disponível.")
            self.list_widget.setEnabled(False)
            return
            
        for folder in folders:
            if id(folder) == id(self.current_item): continue # Não deixa a pasta se engolir!
            item = QListWidgetItem(f"📁 {folder.get('label', 'Pasta')}")
            item.setData(Qt.ItemDataRole.UserRole, id(folder))
            self.list_widget.addItem(item)

    def on_item_clicked(self, item):
        self.btn_confirm.setEnabled(True)

    def execute_send(self):
        selected = self.list_widget.currentItem()
        if selected:
            folder_id = selected.data(Qt.ItemDataRole.UserRole)
            if folder_id:
                if hasattr(self.hub, 'move_item_to_folder_by_id'):
                    self.hub.move_item_to_folder_by_id(self.current_item, folder_id)
                self.accept()

# --- PAINEL: SUBSTITUIR (BLINDADO) ---
class SwapButtonDialog(QDialog):
    def __init__(self, parent_hub, current_item):
        super().__init__(parent_hub)
        self.hub = parent_hub
        self.current_item = current_item
        self.history = [] 
        
        self.item_refs = [] 
        self.tree_data = self.build_tree()
        self.current_nodes = self.tree_data
        
        self.setWindowTitle("Substituir Item")
        self.setFixedSize(450, 500)
        self.setWindowOpacity(0.95)
        
        accent = self.hub.accent_color
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {accent}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; }}
            QListWidget {{ background-color: #161b24; border: 1px solid {accent}; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; font-size: 15px; font-weight: bold; outline: none; }}
            QListWidget::item {{ padding: 12px; border-radius: 6px; border-bottom: 1px solid #1c212d; }}
            QListWidget::item:hover {{ background-color: rgba(255, 255, 255, 0.1); }}
            QListWidget::item:selected {{ background-color: {accent}; color: #000; }}
            QPushButton {{ background-color: {accent}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
            QPushButton#btn_cancel {{ background-color: #161b24; color: #fff; border: 1px solid #232a38; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        self.lbl_info = QLabel(f"Substituir: [ {self.current_item.get('label', '')} ]")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_info)
        
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        self.btn_back = QPushButton("⬅ Voltar")
        self.btn_back.setObjectName("btn_cancel")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.go_back)
        self.btn_back.setVisible(False)
        
        self.btn_confirm = QPushButton("🔄 Confirmar")
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.clicked.connect(self.action_confirm_swap)
        self.btn_confirm.setEnabled(False)
        
        btn_layout.addWidget(self.btn_back)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)
        
        self.populate_list()

    def build_tree(self):
        tree = []
        all_global = self.hub.buttons_list
        folders = [f for f in all_global if f.get("type") == "folder"]
        
        home_node = {"label": "🏠 Itens na Home (Páginas)", "type": "category", "children": []}
        items_per_page = self.hub.items_per_page
        max_pages = max(1, (len(all_global) + items_per_page - 1) // items_per_page) if all_global else 1
        
        for p in range(max_pages):
            page_items = all_global[p * items_per_page : (p + 1) * items_per_page]
            page_children = []
            
            for item in page_items:
                if id(item) == id(self.current_item): continue
                
                self.item_refs.append(item)
                ref_idx = len(self.item_refs) - 1
                
                icon = "📁" if item.get("type") == "folder" else "🔘"
                page_children.append({"label": f"{icon} {item.get('label', 'Sem Nome')}", "type": "item", "ref_idx": ref_idx})
                
            if page_children:
                home_node["children"].append({"label": f"📄 Página {p + 1}", "type": "category", "children": page_children})
        
        if home_node["children"]:
            tree.append(home_node)
            
        if folders:
            folders_node = {"label": "📂 Conteúdo das Pastas", "type": "category", "children": []}
            for folder in folders:
                if id(folder) == id(self.current_item): continue
                
                folder_children = []
                for item in folder.get("buttons", []):
                    if id(item) == id(self.current_item): continue
                    
                    self.item_refs.append(item)
                    ref_idx = len(self.item_refs) - 1
                    
                    folder_children.append({"label": f"🔘 {item.get('label', 'Sem Nome')}", "type": "item", "ref_idx": ref_idx})
                    
                if folder_children:
                    folders_node["children"].append({"label": f"📁 Pasta: {folder.get('label')}", "type": "category", "children": folder_children})
                    
            if folders_node["children"]:
                tree.append(folders_node)
                
        if not tree:
            tree.append({"label": "Nenhum item disponível para troca.", "type": "empty"})
            
        return tree

    def populate_list(self):
        self.list_widget.clear()
        for node in self.current_nodes:
            item = QListWidgetItem(node["label"])
            item.setData(Qt.ItemDataRole.UserRole, node)
            self.list_widget.addItem(item)
            
        self.btn_back.setVisible(len(self.history) > 0)
        self.btn_confirm.setEnabled(False)

    def on_item_clicked(self, item):
        node = item.data(Qt.ItemDataRole.UserRole)
        self.btn_confirm.setEnabled(node["type"] == "item")

    def on_item_double_clicked(self, item):
        node = item.data(Qt.ItemDataRole.UserRole)
        if node["type"] == "category":
            self.history.append(self.current_nodes)
            self.current_nodes = node["children"]
            self.populate_list()
        elif node["type"] == "item":
            self.execute_swap(node["ref_idx"])

    def go_back(self):
        if self.history:
            self.current_nodes = self.history.pop()
            self.populate_list()

    def action_confirm_swap(self):
        self.execute_swap()

    def execute_swap(self, target_idx=None):
        if target_idx is None or isinstance(target_idx, bool):
            selected = self.list_widget.currentItem()
            if selected:
                node = selected.data(Qt.ItemDataRole.UserRole)
                if node["type"] == "item":
                    target_idx = node.get("ref_idx")
        
        if target_idx is not None:
            target_item = self.item_refs[target_idx]
            if hasattr(self.hub, 'swap_items'):
                self.hub.swap_items(self.current_item, target_item)
            self.accept()