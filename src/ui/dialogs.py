import os
import hashlib
import random
import string
import datetime
import calendar
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QPushButton, QLineEdit, QLabel, QFileDialog,
                             QMessageBox, QGridLayout, QComboBox, QScrollArea, QWidget, QApplication,
                             QListWidget, QListWidgetItem, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon

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

class EditFolderDialog(QDialog):
    def __init__(self, parent, folder_data):
        super().__init__(parent)
        self.folder_data = folder_data
        layout = QFormLayout(self)
        self.input_name = QLineEdit(folder_data["label"])
        layout.addRow("Nome:", self.input_name)
        btn = QPushButton("Salvar")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        self.folder_data["label"] = self.input_name.text()
        self.accept()

class SecurityModifyDialog(QDialog):
    def __init__(self, parent_hub, security_data):
        super().__init__(parent_hub)
        # Padronizado para self.hub para evitar o erro AttributeError
        self.hub = parent_hub
        self.security_data = security_data
        
        self.setWindowTitle("Modificar Segurança")
        self.setFixedWidth(380)
        self.setWindowOpacity(0.95)
        
        # Agora o self.hub.accent_color funcionará perfeitamente
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
        # Remove a senha e limpa as configurações de segurança
        self.hub.security_settings = {}
        self.hub.save_settings(force=True)
        QMessageBox.information(self, "Sucesso", "A senha foi removida do sistema.")
        self.accept()

    def do_alterar(self):
        self.accept()
        # Importação local para evitar dependência circular
        from ui.dialogs import SecurityChangePasswordDialog
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
        
# =========================================================================================
# COMANDO RÁPIDO (COMMAND PALETTE)
# =========================================================================================
from PyQt6.QtWidgets import QFrame # Caso ainda não esteja no topo

class CommandPaletteDialog(QDialog):
    def __init__(self, parent_hub):
        super().__init__(parent_hub)
        self.hub = parent_hub
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(700, 520)
        
        self.setup_ui()
        self.populate_list()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.bg_widget = QWidget()
        self.bg_widget.setObjectName("CmdBg")
        accent = self.hub.accent_color
        
        self.bg_widget.setStyleSheet(f"""
            QWidget#CmdBg {{
                background-color: rgba(17, 20, 26, 0.98);
                border: 2px solid {accent};
                border-radius: 12px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 12)
        self.bg_widget.setGraphicsEffect(shadow)
        
        bg_layout = QVBoxLayout(self.bg_widget)
        bg_layout.setContentsMargins(20, 15, 20, 20)
        bg_layout.setSpacing(12)
        
        # =================================================================
        # 1. CABEÇALHO (Título + Chrome Top-Right)
        # =================================================================
        header_layout = QHBoxLayout()
        
        # --- NOVO: Título Dinâmico Estilizado ---
        lbl_title = QLabel("✨ Painel Inteligente")
        lbl_title.setStyleSheet(f"""
            color: {accent};
            font-family: 'Segoe UI';
            font-size: 17px;
            font-weight: 800;
            letter-spacing: 1px;
            background: transparent;
        """)
        header_layout.addWidget(lbl_title)
        
        header_layout.addStretch() # Empurra a barra de ferramentas para a direita
        
        self.chrome_toolbar = QFrame()
        self.chrome_toolbar.setStyleSheet("""
            QFrame { background: transparent; }
            QPushButton { 
                background: transparent; 
                border: none; 
                font-size: 16px; 
                color: #b0b3b8; 
                border-radius: 14px; 
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); color: #fff; }
            QFrame#separator { background-color: rgba(255, 255, 255, 0.15); max-width: 1px; margin: 6px 4px; }
        """)
        ct_layout = QHBoxLayout(self.chrome_toolbar)
        ct_layout.setContentsMargins(0, 0, 0, 0)
        ct_layout.setSpacing(2)
        
        # --- NOVO: Botões com Funcionalidade Conectada ---
        btn_ext = QPushButton("🧩")
        btn_ext.setFixedSize(28, 28)
        btn_ext.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ext.clicked.connect(self.action_extensions)
        
        sep1 = QFrame()
        sep1.setObjectName("separator")
        
        btn_music = QPushButton("🎵")
        btn_music.setFixedSize(28, 28)
        btn_music.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_music.clicked.connect(self.action_music)
        
        btn_sync = QPushButton("👤")
        btn_sync.setFixedSize(28, 28)
        btn_sync.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sync.clicked.connect(self.action_sync)
        
        btn_menu = QPushButton("⋮")
        btn_menu.setFixedSize(28, 28)
        btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_menu.clicked.connect(self.action_menu)
        
        sep2 = QFrame()
        sep2.setObjectName("separator")
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("QPushButton:hover { background-color: #ff5252; color: #fff; }")
        btn_close.clicked.connect(self.reject)
        
        ct_layout.addWidget(btn_ext)
        ct_layout.addWidget(sep1)
        ct_layout.addWidget(btn_music)
        ct_layout.addWidget(btn_sync)
        ct_layout.addWidget(btn_menu)
        ct_layout.addWidget(sep2)
        ct_layout.addWidget(btn_close)
        
        header_layout.addWidget(self.chrome_toolbar)
        bg_layout.addLayout(header_layout)

        # =================================================================
        # 2. BARRA DE PESQUISA INTERNA
        # =================================================================
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("O que você deseja acessar? (Busque ferramentas ou pastas...)")
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(0, 0, 0, 0.4);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                padding: 14px 18px;
                font-family: 'Segoe UI';
                font-size: 16px;
                font-weight: bold;
            }}
            QLineEdit:focus {{
                border: 2px solid {accent};
                background-color: rgba(0, 0, 0, 0.6);
            }}
        """)
        self.search_bar.textChanged.connect(self.filter_items)
        bg_layout.addWidget(self.search_bar)
        
        self.result_list = QListWidget()
        self.result_list.setCursor(Qt.CursorShape.PointingHandCursor)
        self.result_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ color: white; padding: 12px 15px; border-radius: 8px; font-family: 'Segoe UI'; font-size: 15px; font-weight: 600; margin-bottom: 4px; }}
            QListWidget::item:selected {{ background-color: {accent}; color: #000000; }}
            QListWidget::item:hover {{ background-color: rgba(255, 255, 255, 0.1); }}
        """)
        self.result_list.itemActivated.connect(self.open_selected_item)
        self.result_list.itemClicked.connect(self.open_selected_item)
        bg_layout.addWidget(self.result_list)

        # =================================================================
        # 3. BARRA DE PESQUISA GOOGLE
        # =================================================================
        self.google_frame = QFrame()
        self.google_frame.setFixedHeight(50)
        self.google_frame.setStyleSheet("""
            QFrame { background-color: #ffffff; border-radius: 25px; }
            QLabel, QPushButton { background: transparent; border: none; }
            QLineEdit { background: transparent; border: none; color: #202124; font-size: 15px; font-family: 'Segoe UI'; }
        """)
        
        g_layout = QHBoxLayout(self.google_frame)
        g_layout.setContentsMargins(15, 0, 10, 0)
        g_layout.setSpacing(12)
        
        icon_plus = QLabel("➕")
        icon_plus.setStyleSheet("color: #5f6368; font-size: 15px;")
        
        self.google_input = QLineEdit()
        self.google_input.setPlaceholderText("Pergunte ao Google ou digite um URL...")
        self.google_input.returnPressed.connect(self.do_google_search)
        
        icon_mic = QPushButton("🎤")
        icon_mic.setFixedSize(28, 28)
        icon_mic.setCursor(Qt.CursorShape.PointingHandCursor)
        icon_mic.setStyleSheet("color: #5f6368; font-size: 16px;")
        
        icon_lens = QPushButton("📷")
        icon_lens.setFixedSize(28, 28)
        icon_lens.setCursor(Qt.CursorShape.PointingHandCursor)
        icon_lens.setStyleSheet("color: #5f6368; font-size: 16px;")
        
        btn_ia = QPushButton("✨ Modo IA")
        btn_ia.setFixedHeight(34)
        btn_ia.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ia.setStyleSheet("""
            QPushButton { background-color: #f1f3f4; color: #202124; border-radius: 17px; padding: 0 15px; font-size: 13px; font-weight: 600; font-family: 'Segoe UI'; }
            QPushButton:hover { background-color: #e8eaed; }
        """)
        
        g_layout.addWidget(icon_plus)
        g_layout.addWidget(self.google_input)
        g_layout.addWidget(icon_mic)
        g_layout.addWidget(icon_lens)
        g_layout.addWidget(btn_ia)
        
        bg_layout.addWidget(self.google_frame)

        self.search_bar.installEventFilter(self)
        self.layout.addWidget(self.bg_widget)
        
    # =================================================================
    # AÇÕES DOS BOTÕES (Cabeçalho)
    # =================================================================
    def action_extensions(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Extensões", "Central de Extensões em desenvolvimento.\nAqui você gerenciará plugins e add-ons.")

    def action_music(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Controle de Mídia", "Módulo de música e controle de reprodução web em breve.")

    def action_sync(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Sincronização", "O sistema de Sincronização em Nuvem de usuários será implementado aqui.")

    def action_menu(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Opções", "Mais configurações da Command Palette serão disponibilizadas aqui.")
        
    # =================================================================
    # ARRASTAR A JANELA (Drag & Drop)
    # =================================================================
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
        
    # =================================================================
    # LÓGICA DE BUSCA E NAVEGAÇÃO
    # =================================================================
    def populate_list(self):
        self.all_items = []
        if hasattr(self.hub, 'buttons_list'):
            self.all_items.extend(self.hub.buttons_list)
        if hasattr(self.hub, 'folders_list'):
            for folder in self.hub.folders_list:
                self.all_items.extend(folder.get("buttons", []))
        self.filter_items("")
        
    def filter_items(self, text):
        self.result_list.clear()
        search_term = text.lower().strip()
        for item in self.all_items:
            label = item.get("label", "")
            if search_term in label.lower():
                from PyQt6.QtWidgets import QListWidgetItem # Para garantir que está carregado
                from PyQt6.QtGui import QIcon
                
                list_item = QListWidgetItem(f"🚀  {label}")
                icon_name = f"{label.lower()}.png"
                icon_path = os.path.join(self.hub.icons_dir, icon_name)
                if os.path.exists(icon_path):
                    list_item.setIcon(QIcon(icon_path))
                list_item.setData(Qt.ItemDataRole.UserRole, item)
                self.result_list.addItem(list_item)
                
        if self.result_list.count() > 0:
            self.result_list.setCurrentRow(0)
            
    def open_selected_item(self, item=None):
        if not item:
            item = self.result_list.currentItem()
        if not item: return
            
        item_data = item.data(Qt.ItemDataRole.UserRole)
        url = item_data.get("url", "")
        label = item_data.get("label", "")
        
        if url:
            self.hub.open_web_tab(url, label)
        self.accept()

    def do_google_search(self):
        query = self.google_input.text().strip()
        if not query: return
        
        if query.startswith("http://") or query.startswith("https://") or ("." in query and " " not in query):
            url = query if query.startswith("http") else f"https://{query}"
            label = query
        else:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            label = f"Busca: {query[:10]}..."
            
        self.hub.open_web_tab(url, label)
        self.accept()
        
    def eventFilter(self, obj, event):
        if obj == self.search_bar and event.type() == event.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Down:
                current = self.result_list.currentRow()
                if current < self.result_list.count() - 1:
                    self.result_list.setCurrentRow(current + 1)
                return True
            elif key == Qt.Key.Key_Up:
                current = self.result_list.currentRow()
                if current > 0:
                    self.result_list.setCurrentRow(current - 1)
                return True
            elif key in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                self.open_selected_item()
                return True
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        """Centralização Perfeita (Removido o -60 offset)"""
        if self.hub:
            hub_rect = self.hub.geometry()
            x = hub_rect.x() + (hub_rect.width() - self.width()) // 2
            y = hub_rect.y() + (hub_rect.height() - self.height()) // 2
            self.move(x, y) 
        super().showEvent(event)