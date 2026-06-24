import os
import hashlib
import random
import string
import datetime
import calendar
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QPushButton, QLineEdit, QLabel, QFileDialog, 
                             QMessageBox, QFrame, QGridLayout, QMenu, QComboBox, QScrollArea, QWidget)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QPixmap, QColor, QDrag, QImage, QPainter
from core.remote_tools import launch_remote_tool

class SecuritySetupDialog(QDialog):
    def __init__(self, parent, current_data):
        super().__init__(parent)
        self.hub = parent
        self.setWindowTitle("Configurar Senha de Acesso")
        self.setFixedWidth(450)
        self.setWindowOpacity(0.95)
        self.current_data = current_data or {}
        accent = self.hub.accent_color
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {accent}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }}
            QLineEdit {{ background-color: #161b24; border: 1px solid {accent}; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; font-weight: bold; }}
            QPushButton {{ background-color: {accent}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
            QPushButton#btn_voltar {{ background-color: #161b24; color: #fff; border: 1px solid #232a38; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.input_name = QLineEdit(self.current_data.get("name", ""))
        self.input_name.setPlaceholderText("Ex: Felipe Fiuza")
        self.input_pass = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setPlaceholderText("Digite uma nova senha")
        self.input_confirm = QLineEdit()
        self.input_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_confirm.setPlaceholderText("Confirme a nova senha")
        self.input_hint = QLineEdit(self.current_data.get("hint", ""))
        self.input_hint.setPlaceholderText("Dica de senha")
        self.input_image = QLineEdit(self.current_data.get("image", ""))
        self.input_image.setPlaceholderText("Caminho da imagem (Opcional)")
        btn_img = QPushButton("🖼️ Procurar")
        btn_img.clicked.connect(self.select_image)
        
        img_layout = QHBoxLayout()
        img_layout.addWidget(self.input_image)
        img_layout.addWidget(btn_img)
        form_layout.addRow(QLabel("Nome:"), self.input_name)
        form_layout.addRow(QLabel("Nova senha:"), self.input_pass)
        form_layout.addRow(QLabel("Confirme:"), self.input_confirm)
        form_layout.addRow(QLabel("Dica de senha:"), self.input_hint)
        form_layout.addRow(QLabel("Imagem:"), img_layout)
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_confirm = QPushButton("Confirmar")
        btn_back = QPushButton("Voltar")
        btn_back.setObjectName("btn_voltar")
        btn_confirm.clicked.connect(self.save_security)
        btn_back.clicked.connect(self.reject)
        btn_layout.addWidget(btn_confirm)
        btn_layout.addWidget(btn_back)
        layout.addLayout(btn_layout)

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem de Bloqueio", "", "Imagens (*.png *.jpg *.jpeg)")
        if path: self.input_image.setText(path)

    def generate_master_key(self):
        chars = string.ascii_uppercase + string.digits
        return f"FIUZA-{''.join(random.choices(chars, k=4))}-{''.join(random.choices(chars, k=4))}"

    def save_security(self):
        name = self.input_name.text().strip()
        pwd = self.input_pass.text().strip()
        conf = self.input_confirm.text().strip()
        hint = self.input_hint.text().strip()
        img = self.input_image.text().strip()
        
        if not name or not pwd:
            QMessageBox.warning(self, "Erro", "Nome e Senha são obrigatórios.")
            return
        if pwd != conf:
            QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
            return
            
        hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest()
        master_key = self.generate_master_key()
        master_key_hash = hashlib.sha256(master_key.encode()).hexdigest()
        
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(master_key)
        
        QMessageBox.warning(self, "MUITO IMPORTANTE: CHAVE MESTRA", 
                            f"Anote esta Chave de Recuperação em um lugar seguro. Ela é a ÚNICA forma de recuperar sua conta caso esqueça a senha.\n\n"
                            f"CHAVE MESTRA (Já copiada para sua área de transferência!):\n{master_key}")
        
        self.final_data = {"enabled": True, "name": name, "password_hash": hashed_pwd, "master_key_hash": master_key_hash, "hint": hint, "image": img}
        self.accept()

class SecurityModifyDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.hub = parent
        self.setWindowTitle("Modificar Segurança")
        self.setFixedWidth(380)
        self.setWindowOpacity(0.95)
        accent = self.hub.accent_color
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {accent}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; text-align: center; }}
            QPushButton {{ background-color: {accent}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 12px; border-radius: 6px; font-size: 13px; }}
            QPushButton#btn_danger {{ background-color: #ff5252; color: #fff; border: 1px solid #000000; }}
            QPushButton#btn_voltar {{ background-color: #161b24; color: #fff; border: 1px solid #232a38; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        layout.addWidget(QLabel("Deseja alterar ou remover a senha?"))
        btn_alterar = QPushButton("Alterar Senha")
        btn_remover = QPushButton("Remover Senha")
        btn_remover.setObjectName("btn_danger")
        btn_voltar = QPushButton("Voltar")
        btn_voltar.setObjectName("btn_voltar")
        btn_alterar.clicked.connect(self.do_alterar)
        btn_remover.clicked.connect(self.do_remover)
        btn_voltar.clicked.connect(self.reject)
        layout.addWidget(btn_alterar)
        layout.addWidget(btn_remover)
        layout.addWidget(btn_voltar)

    def do_remover(self):
        self.hub.security_settings = {}
        self.hub.save_settings(force=True)
        QMessageBox.information(self, "Sucesso", "A senha foi removida do sistema.")
        self.accept()

    def do_alterar(self):
        self.accept()
        dialog = SecurityChangePasswordDialog(self.hub)
        dialog.exec()

class SecurityChangePasswordDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.hub = parent
        self.setWindowTitle("Alterar Senha")
        self.setFixedWidth(400)
        self.setWindowOpacity(0.95)
        accent = self.hub.accent_color
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {accent}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }}
            QLineEdit {{ background-color: #161b24; border: 1px solid {accent}; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; font-weight: bold; }}
            QPushButton {{ background-color: {accent}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
            QPushButton#btn_voltar {{ background-color: #161b24; color: #fff; border: 1px solid #232a38; }}
        """)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.input_pass = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setPlaceholderText("Nova senha")
        self.input_confirm = QLineEdit()
        self.input_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_confirm.setPlaceholderText("Confirmar nova senha")
        form_layout.addRow("Nova Senha:", self.input_pass)
        form_layout.addRow("Confirmar:", self.input_confirm)
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_confirm = QPushButton("Confirmar")
        btn_back = QPushButton("Voltar")
        btn_back.setObjectName("btn_voltar")
        btn_confirm.clicked.connect(self.save_new_pass)
        btn_back.clicked.connect(self.reject)
        btn_layout.addWidget(btn_confirm)
        btn_layout.addWidget(btn_back)
        layout.addLayout(btn_layout)

    def save_new_pass(self):
        pwd = self.input_pass.text().strip()
        conf = self.input_confirm.text().strip()
        if not pwd:
            QMessageBox.warning(self, "Erro", "Digite uma senha.")
            return
        if pwd != conf:
            QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
            return
        hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest()
        self.hub.security_settings['password_hash'] = hashed_pwd
        self.hub.save_settings(force=True)
        QMessageBox.information(self, "Sucesso", "Senha alterada com sucesso!")
        self.accept()

class HistoryDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.hub = parent
        self.setWindowTitle("Histórico de Navegação")
        self.setFixedSize(700, 550) # Tamanho reduzido e refinado
        self.setWindowOpacity(0.95)
        self.accent_color = self.hub.accent_color
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {self.accent_color}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }}
            QComboBox {{ background-color: #161b24; border: 1px solid {self.accent_color}; border-radius: 6px; color: #fff; padding: 8px; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }}
            QComboBox QAbstractItemView {{ background-color: #161b24; color: #fff; selection-background-color: {self.accent_color}; selection-color: #000; }}
            QPushButton {{ background-color: #161b24; color: #fff; font-family: 'Segoe UI'; font-weight: bold; padding: 6px; border-radius: 6px; border: 1px solid #232a38; }}
            QPushButton:hover {{ background-color: {self.accent_color}; color: #000; border: 1px solid #000000; }}
            QScrollArea {{ background: transparent; border: 1px solid #232a38; border-radius: 6px; }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        self.month_combo = QComboBox()
        self.month_combo.currentIndexChanged.connect(self.build_calendar)
        self.layout.addWidget(self.month_combo)
        
        self.days_widget = QWidget()
        self.days_layout = QGridLayout(self.days_widget)
        self.days_layout.setSpacing(5)
        self.layout.addWidget(self.days_widget)
        
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_container = QWidget()
        self.history_container.setStyleSheet("background: transparent;")
        self.history_list_layout = QVBoxLayout(self.history_container)
        self.history_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_scroll.setWidget(self.history_container)
        self.layout.addWidget(self.history_scroll)
        
        action_layout = QHBoxLayout()
        btn_clear = QPushButton("🗑️ Limpar Tudo")
        btn_clear.setStyleSheet("background-color: #3d1c1c; color: #ff5252; border: 1px solid #ff5252;")
        btn_clear.clicked.connect(self.clear_all_history)
        btn_export = QPushButton("📤 Exportar")
        btn_export.clicked.connect(self.export_history)
        btn_import = QPushButton("📥 Importar")
        btn_import.clicked.connect(self.import_history)
        
        action_layout.addWidget(btn_clear)
        action_layout.addStretch()
        action_layout.addWidget(btn_import)
        action_layout.addWidget(btn_export)
        self.layout.addLayout(action_layout)

        self.populate_months()
        
    def populate_months(self):
        self.month_combo.blockSignals(True)
        self.month_combo.clear()
        
        history_dates = list(self.hub.history_data.keys())
        now = datetime.datetime.now()
        current_year = now.strftime("%Y")
        
        # Coleta todos os anos que tem histórico + ano atual
        years = set([d[:4] for d in history_dates])
        years.add(current_year)
        sorted_years = sorted(list(years), reverse=True)
        
        months_pt = {1:"Janeiro", 2:"Fevereiro", 3:"Março", 4:"Abril", 5:"Maio", 6:"Junho", 7:"Julho", 8:"Agosto", 9:"Setembro", 10:"Outubro", 11:"Novembro", 12:"Dezembro"}
        
        # Gera os 12 meses para cada ano
        for y in sorted_years:
            for m in range(12, 0, -1):
                ym = f"{y}-{m:02d}"
                label = f"{months_pt[m]} de {y}"
                self.month_combo.addItem(label, ym)
                
        # Define o index inicial para o mês/ano atual
        current_ym = now.strftime("%Y-%m")
        index = self.month_combo.findData(current_ym)
        if index >= 0:
            self.month_combo.setCurrentIndex(index)
            
        self.month_combo.blockSignals(False)
        self.build_calendar()

    def build_calendar(self):
        while self.days_layout.count():
            child = self.days_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        ym = self.month_combo.currentData()
        if not ym: return
        y, m = map(int, ym.split("-"))
        _, days_in_month = calendar.monthrange(y, m)
        now = datetime.datetime.now()
        current_date_str = now.strftime("%Y-%m-%d")
        
        row, col = 0, 0
        for day in range(1, days_in_month + 1):
            date_str = f"{y:04d}-{m:02d}-{day:02d}"
            btn = QPushButton(str(day))
            btn.setFixedSize(35, 35)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            has_data = date_str in self.hub.history_data and len(self.hub.history_data[date_str]) > 0
            
            if date_str == current_date_str:
                btn.setStyleSheet(f"background-color: {self.accent_color}; color: #000; border: 2px solid #fff; font-weight: bold;")
            elif has_data:
                btn.setStyleSheet(f"background-color: rgba({QColor(self.accent_color).red()}, {QColor(self.accent_color).green()}, {QColor(self.accent_color).blue()}, 0.4); color: #fff; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: #11141a; color: #555; border: 1px solid #222;")
                
            btn.clicked.connect(lambda checked, ds=date_str: self.load_history_list(ds))
            self.days_layout.addWidget(btn, row, col)
            col += 1
            if col > 10:
                col = 0
                row += 1
        self.load_history_list(current_date_str)

    def load_history_list(self, date_str):
        while self.history_list_layout.count():
            child = self.history_list_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        items = self.hub.history_data.get(date_str, [])
        if not items:
            lbl = QLabel("Nenhum histórico para este dia.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #555; font-style: italic; margin-top: 20px;")
            self.history_list_layout.addWidget(lbl)
            return
            
        for idx, item in enumerate(items):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(10, 5, 10, 5)
            
            lbl_time = QLabel(f"[{item['time']}]")
            lbl_time.setFixedWidth(50)
            lbl_time.setStyleSheet(f"color: {self.accent_color}; font-weight: bold;")
            
            # Texto da URL junto ao Nome (Estilizado)
            short_url = item['url'][:50] + "..." if len(item['url']) > 50 else item['url']
            btn_link = QPushButton(f"{item['label']} - {short_url}")
            btn_link.setStyleSheet("text-align: left; background: transparent; border: none; font-size: 13px; color: #fff;")
            btn_link.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_link.clicked.connect(lambda checked, u=item['url'], l=item['label']: self.open_and_close(u, l))
            
            btn_del = QPushButton("✕")
            btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet("background: transparent; color: #ff5252; border: none; font-weight: bold;")
            btn_del.clicked.connect(lambda checked, d=date_str, i=idx: self.delete_single_item(d, i))
            
            row_layout.addWidget(lbl_time)
            row_layout.addWidget(btn_link)
            row_layout.addWidget(btn_del)
            self.history_list_layout.addWidget(row_widget)

    def open_and_close(self, url, label):
        self.hub.open_web_tab(url, label)
        self.accept()

    def delete_single_item(self, date_str, index):
        if date_str in self.hub.history_data:
            self.hub.history_data[date_str].pop(index)
            if not self.hub.history_data[date_str]:
                del self.hub.history_data[date_str]
            self.hub.save_settings(force=True)
            self.build_calendar()
            self.load_history_list(date_str)

    def clear_all_history(self):
        reply = QMessageBox.question(self, "Limpar Histórico", "Tem certeza que deseja apagar TODO o histórico?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.hub.history_data = {}
            self.hub.save_settings(force=True)
            self.populate_months()

    def export_history(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Histórico", "Historico_FiuzaHub.txt", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("=== HISTÓRICO FIUZA STANDALONE HUB ===\n")
                f.write("FORMATO DE IMPORTAÇÃO AUTOMÁTICA\n\n")
                for date_str, items in sorted(self.hub.history_data.items(), reverse=True):
                    f.write(f"DATA: {date_str}\n")
                    for item in items:
                        f.write(f"[{item['time']}] | {item['label']} | {item['url']}\n")
                    f.write("\n")
            QMessageBox.information(self, "Sucesso", "Histórico exportado com sucesso!")

    def import_history(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar Histórico", "", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                current_date = None
                imported_count = 0
                for line in lines:
                    line = line.strip()
                    if line.startswith("DATA:"):
                        current_date = line.replace("DATA:", "").strip()
                        if current_date not in self.hub.history_data:
                            self.hub.history_data[current_date] = []
                    elif line.startswith("[") and "|" in line and current_date:
                        parts = line.split("|")
                        if len(parts) == 3:
                            time_str = parts[0].replace("[", "").replace("]", "").strip()
                            label_str = parts[1].strip()
                            url_str = parts[2].strip()
                            self.hub.history_data[current_date].append({"time": time_str, "label": label_str, "url": url_str})
                            imported_count += 1
                for d in self.hub.history_data:
                    unique_data = []
                    seen = set()
                    for item in self.hub.history_data[d]:
                        tup = (item['time'], item['label'], item['url'])
                        if tup not in seen:
                            seen.add(tup)
                            unique_data.append(item)
                    self.hub.history_data[d] = sorted(unique_data, key=lambda x: x['time'], reverse=True)
                self.hub.save_settings(force=True)
                self.populate_months()
                QMessageBox.information(self, "Sucesso", f"Foram importados {imported_count} registros de histórico com sucesso!")
            except Exception as e:
                QMessageBox.warning(self, "Erro", "Não foi possível ler o arquivo. Certifique-se que é o formato original exportado.")

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

from PyQt6.QtWidgets import QTabWidget
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

class GoogleLoginInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        # O PULO DO GATO: Camuflagem ATIVA APENAS na tela de login!
        # Deixamos o youtube.com passar com o Chrome original para não dar conflito no motor V8.
        if "accounts.google.com" in url or "myaccount.google.com" in url:
            firefox_ua = b"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
            info.setHttpHeader(b"User-Agent", firefox_ua)

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