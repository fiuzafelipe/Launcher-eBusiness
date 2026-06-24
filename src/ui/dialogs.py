import os
import hashlib
import random
import string
import datetime
import calendar
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QPushButton, QLineEdit, QLabel, QFileDialog,
                             QMessageBox, QGridLayout, QComboBox, QScrollArea, QWidget, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor # <- Correção do erro aqui!

# Importações do Core
from core.image_utils import process_and_save_icon

# =========================================================================================
# MODAIS DE SEGURANÇA E ACESSO
# =========================================================================================

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
        
        if not name or not pwd:
            QMessageBox.warning(self, "Erro", "Nome e Senha são obrigatórios.")
            return
        if pwd != conf:
            QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
            return
            
        hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest()
        master_key = self.generate_master_key()
        master_key_hash = hashlib.sha256(master_key.encode()).hexdigest()
        
        QApplication.clipboard().setText(master_key)
        
        QMessageBox.warning(self, "MUITO IMPORTANTE: CHAVE MESTRA", 
                            f"Anote esta Chave de Recuperação em um lugar seguro. Ela é a ÚNICA forma de recuperar sua conta caso esqueça a senha.\n\n"
                            f"CHAVE MESTRA (Já copiada para sua área de transferência!):\n{master_key}")
        
        self.final_data = {"enabled": True, "name": name, "password_hash": hashed_pwd, "master_key_hash": master_key_hash, "hint": hint, "image": self.input_image.text().strip()}
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
        self.setFixedSize(700, 550) 
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
        
        years = set([d[:4] for d in history_dates])
        years.add(current_year)
        sorted_years = sorted(list(years), reverse=True)
        
        months_pt = {1:"Janeiro", 2:"Fevereiro", 3:"Março", 4:"Abril", 5:"Maio", 6:"Junho", 7:"Julho", 8:"Agosto", 9:"Setembro", 10:"Outubro", 11:"Novembro", 12:"Dezembro"}
        
        for y in sorted_years:
            for m in range(12, 0, -1):
                ym = f"{y}-{m:02d}"
                label = f"{months_pt[m]} de {y}"
                self.month_combo.addItem(label, ym)
                
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


class AboutDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_hub = parent # <-- CORREÇÃO: Variável segura
        self.setWindowTitle("Sobre o Standalone Hub")
        self.setFixedSize(400, 150)
        
        accent = self.parent_hub.accent_color
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid #232a38; border-image: none; }}
            QLabel {{ color: {accent}; font-family: 'Segoe UI'; font-size: 15px; font-weight: bold; text-align: center; border-image: none; }}
            QPushButton {{ background-color: #161b24; border: 1px solid #232a38; color: #fff; padding: 8px; border-radius: 4px; font-weight: bold; font-family: 'Segoe UI'; font-size: 13px; width: 100px; border-image: none; }}
            QPushButton:hover {{ background-color: {accent}; color: #000; border-color: {accent}; }}
        """)
        
        layout = QVBoxLayout(self)
        lbl = QLabel("Aplicação desenvolvida por Felipe Fiuza!\nBom uso.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        
        layout.addStretch()
        layout.addWidget(lbl)
        layout.addSpacing(15)
        layout.addLayout(btn_layout)
        layout.addStretch()


class ToolboxDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_hub = parent # <-- CORREÇÃO: Variável segura
        self.setWindowTitle("Adicionar ao Toolbox")
        self.setFixedWidth(420)
        self.setWindowOpacity(0.92)
        
        accent = self.parent_hub.accent_color
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {accent}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 12px; font-weight: bold; }}
            QLineEdit {{ background-color: #161b24; border: 1px solid {accent}; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; }}
            QPushButton {{ background-color: {accent}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
        """)
        
        form_layout = QFormLayout(self)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        self.input_name = QLineEdit()
        self.input_sub = QLineEdit()
        self.input_url = QLineEdit()
        
        self.btn_img = QPushButton("🖼️ Adicionar Imagem (Opcional)")
        self.selected_img = ""
        self.btn_img.clicked.connect(self.pick_img)
        
        form_layout.addRow(QLabel("Nome do Botão:"), self.input_name)
        form_layout.addRow(QLabel("Subtítulo:"), self.input_sub)
        form_layout.addRow(QLabel("URL do Site:"), self.input_url)
        form_layout.addRow(self.btn_img)
        
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Adicionar")
        btn_back = QPushButton("Cancelar")
        btn_back.setStyleSheet("background-color: #161b24; color: #fff;")
        
        btn_save.clicked.connect(self.add_toolbox_item)
        btn_back.clicked.connect(self.reject)
        
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_back)
        form_layout.addRow(btn_box)

    def pick_img(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Ícone", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.selected_img = path
            self.btn_img.setText("Imagem Selecionada!")

    def add_toolbox_item(self):
        name = self.input_name.text().strip()
        sub = self.input_sub.text().strip()
        url = self.input_url.text().strip()
        
        if name and url:
            if self.selected_img:
                dest_path = os.path.join(self.parent_hub.icons_dir, f"{name.lower()}.png")
                process_and_save_icon(self.selected_img, dest_path)
                
            self.parent_hub.buttons_list.append({"label": name, "subtitle": sub, "url": url, "favorite": False})
            self.parent_hub.save_settings(force=True)
            self.parent_hub.filter_buttons_by_search(self.parent_hub.search_filter)
            self.accept()


class EditButtonDialog(QDialog):
    def __init__(self, parent, item_data):
        super().__init__(parent)
        self.parent_hub = parent
        self.item_data = item_data
        self.setWindowTitle("Editar Botão")
        self.setFixedWidth(420)
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid #1c212d; }}
            QLabel {{ color: #a0a5b5; font-family: 'Segoe UI'; font-size: 12px; font-weight: bold; }}
            QLineEdit {{ background-color: #161b24; border: 1px solid {self.parent_hub.accent_color}; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; }}
            QLineEdit:focus {{ border: 1px solid {self.parent_hub.accent_color}; }}
            QPushButton {{ font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
        """)
        form_layout = QFormLayout(self)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        self.old_name = item_data["label"]
        self.input_name = QLineEdit(item_data["label"])
        self.input_subtitle = QLineEdit(item_data.get("subtitle", ""))
        self.input_url = QLineEdit(item_data["url"])
        self.btn_img = QPushButton("🖼️ Alterar Imagem")
        self.btn_img.setStyleSheet("background-color: #161b24; border: 1px solid #232a38; color: #fff; text-align: center;")
        self.selected_img = ""
        self.btn_img.clicked.connect(self.pick_img)
        form_layout.addRow(QLabel("Nome do Botão:"), self.input_name)
        form_layout.addRow(QLabel("Nome do Subtítulo:"), self.input_subtitle)
        form_layout.addRow(QLabel("URL do Site:"), self.input_url)
        form_layout.addRow(self.btn_img)
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Salvar")
        btn_save.setStyleSheet(f"background-color: {self.parent_hub.accent_color}; color: #07080a; font-weight: bold;")
        btn_back = QPushButton("Cancelar")
        btn_back.setStyleSheet("background-color: #161b24; border: 1px solid #232a38; color: #fff;")
        btn_save.clicked.connect(self.save_edit)
        btn_back.clicked.connect(self.reject)
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_back)
        form_layout.addRow(btn_box)

    def pick_img(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Ícone", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.selected_img = path
            self.btn_img.setText("Imagem Selecionada!")
            self.btn_img.setStyleSheet(f"background-color: {self.parent_hub.accent_color}; color: #000; font-weight: bold; border: none;")

    def save_edit(self):
        new_name = self.input_name.text().strip()
        new_sub = self.input_subtitle.text().strip()
        new_url = self.input_url.text().strip()
        if new_name and new_url:
            if self.selected_img:
                dest_path = os.path.join(self.parent_hub.icons_dir, f"{new_name.lower()}.png")
                process_and_save_icon(self.selected_img, dest_path)
                if self.old_name.lower() != new_name.lower():
                    old_icon = os.path.join(self.parent_hub.icons_dir, f"{self.old_name.lower()}.png")
                    if os.path.exists(old_icon):
                        try: os.remove(old_icon)
                        except: pass
            elif self.old_name.lower() != new_name.lower():
                old_icon = os.path.join(self.parent_hub.icons_dir, f"{self.old_name.lower()}.png")
                new_icon = os.path.join(self.parent_hub.icons_dir, f"{new_name.lower()}.png")
                if os.path.exists(old_icon):
                    try: os.rename(old_icon, new_icon)
                    except: pass
            self.item_data["label"] = new_name
            self.item_data["subtitle"] = new_sub
            self.item_data["url"] = new_url
            self.parent_hub.save_settings(force=True)
            self.parent_hub.filter_buttons_by_search(self.parent_hub.search_filter)
            self.accept()


class DirectNavDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_hub = parent
        self.setWindowTitle("Navegador Rápido")
        self.setFixedWidth(450)
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid #232a38; border-radius: 8px; }}
            QLabel {{ color: {self.parent_hub.accent_color}; font-family: 'Segoe UI'; font-weight: bold; font-size: 13px; }}
            QLineEdit {{ background-color: #161b24; border: 1px solid #232a38; color: #fff; padding: 12px; border-radius: 6px; font-size: 13px; }}
            QLineEdit:focus {{ border: 1px solid {self.parent_hub.accent_color}; }}
            QPushButton {{ background-color: {self.parent_hub.accent_color}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; font-size: 13px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        lbl = QLabel("🌐 Digite a URL:")
        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("Exemplo: google.com.br")
        btn_layout = QHBoxLayout()
        btn_go = QPushButton("Acessar")
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background-color: #161b24; color: #fff; border: 1px solid #232a38; padding: 10px; border-radius: 6px;")
        btn_go.clicked.connect(self.go_url)
        btn_cancel.clicked.connect(self.reject)
        self.input_url.returnPressed.connect(self.go_url)
        btn_layout.addWidget(btn_go)
        btn_layout.addWidget(btn_cancel)
        layout.addWidget(lbl)
        layout.addWidget(self.input_url)
        layout.addLayout(btn_layout)

    def go_url(self):
        url = self.input_url.text().strip()
        if url:
            if not url.startswith("http://") and not url.startswith("https://"): url = "https://" + url
            self.parent_hub.open_web_tab(url, "Carregando...")
            self.accept()


class DeleteToolboxDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_hub = parent
        self.setWindowTitle("Remover Botão do Toolbox")
        self.setFixedWidth(400)
        self.setWindowOpacity(0.92)
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {self.parent_hub.accent_color}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }}
            QComboBox {{ background-color: #161b24; border: 1px solid {self.parent_hub.accent_color}; border-radius: 6px; color: #fff; padding: 8px; font-family: 'Segoe UI'; }}
            QPushButton {{ background-color: {self.parent_hub.accent_color}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(QLabel("Selecione o botão que deseja excluir definitivamente:"))
        self.combo = QComboBox()
        for item in self.parent_hub.buttons_list: self.combo.addItem(item["label"])
        layout.addWidget(self.combo)
        btn_box = QHBoxLayout()
        btn_del = QPushButton("Deletar e Salvar")
        btn_del.setStyleSheet("background-color: #ff5252; color: #fff;")
        btn_back = QPushButton("Voltar")
        btn_back.setStyleSheet("background-color: #161b24; color: #fff;")
        btn_del.clicked.connect(self.delete_item)
        btn_back.clicked.connect(self.reject)
        btn_box.addWidget(btn_del)
        btn_box.addWidget(btn_back)
        layout.addLayout(btn_box)

    def delete_item(self):
        target_label = self.combo.currentText()
        target_item = next((b for b in self.parent_hub.buttons_list if b["label"] == target_label), None)
        if target_item:
            self.parent_hub.buttons_list.remove(target_item)
            icon_path = os.path.join(self.parent_hub.icons_dir, f"{target_label.lower()}.png")
            if os.path.exists(icon_path):
                try: os.remove(icon_path)
                except: pass
        max_pages = max(0, (len(self.parent_hub.buttons_list) - 1) // self.parent_hub.items_per_page)
        if self.parent_hub.current_page > max_pages: self.parent_hub.current_page = max_pages
        self.parent_hub.save_settings(force=True)  
        self.parent_hub.filter_buttons_by_search(self.parent_hub.search_filter)
        self.parent_hub.update_favorites_panel()
        self.accept()