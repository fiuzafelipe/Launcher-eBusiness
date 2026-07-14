import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLineEdit, 
                             QLabel, QFileDialog, QHBoxLayout, QCheckBox)
from core.image_utils import process_and_save_icon

class CreateFolderDialog(QDialog):
    def __init__(self, parent, folder_data=None):
        super().__init__(parent)
        self.parent_hub = parent
        self.folder_data = folder_data
        is_editing = self.folder_data is not None
        
        self.setWindowTitle("Editar Pasta" if is_editing else "Criar Nova Pasta")
        self.setFixedWidth(400)
        self.setStyleSheet("""
            QDialog { background-color: #11141a; border: 1px solid #10b981; border-radius: 10px; }
            QLineEdit { background-color: #161b24; border: 1px solid #10b981; border-radius: 6px; color: #fff; padding: 10px; }
            QLabel { color: #fff; font-weight: bold; }
            QCheckBox { color: #fff; font-weight: bold; font-family: 'Segoe UI'; font-size: 12px; }
            QPushButton { font-weight: bold; padding: 10px; border-radius: 6px; }
        """)
        
        self.selected_img = ""
        self.input_name = QLineEdit(self.folder_data.get("label", "") if is_editing else "")
        self.input_sub = QLineEdit(self.folder_data.get("subtitle", "") if is_editing else "")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        layout.addWidget(QLabel("Nome da Pasta:"))
        layout.addWidget(self.input_name)
        layout.addWidget(QLabel("Subtítulo:"))
        layout.addWidget(self.input_sub)
        
        img_layout = QHBoxLayout()
        self.btn_img = QPushButton("🖼️ Adicionar Imagem")
        self.btn_img.setStyleSheet("background-color: #161b24; color: #fff; border: 1px solid #10b981;")
        self.btn_rem_img = QPushButton("🗑️ Remover Imagem")
        self.btn_rem_img.setStyleSheet("background-color: #ff5252; color: #fff; border: none;")
        self.btn_img.clicked.connect(self.pick_img)
        self.btn_rem_img.clicked.connect(self.remove_img)
        img_layout.addWidget(self.btn_img)
        img_layout.addWidget(self.btn_rem_img)
        layout.addLayout(img_layout)
        
        # --- NOVA CHECKBOX DE TRANSPARÊNCIA (Pasta) ---
        self.check_transparent = QCheckBox("Tornar fundo da imagem transparente")
        if is_editing:
            self.check_transparent.setChecked(self.folder_data.get("transparent_icon", False))
        else:
            self.check_transparent.setChecked(False)
            
        layout.addWidget(self.check_transparent)
        
        self.btn_save = QPushButton("Salvar" if is_editing else "Adicionar")
        self.btn_save.setMinimumHeight(45)
        self.btn_save.setStyleSheet("background-color: #10b981; color: #000; font-weight: bold; margin-top: 15px;")
        self.btn_save.clicked.connect(self.save_folder)
        layout.addWidget(self.btn_save)

    def pick_img(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Ícone", "", "Images (*.png *.jpg *.jpeg)")
        if path: self.selected_img = path; self.btn_img.setText("Imagem selecionada!")

    def remove_img(self):
        self.selected_img = "REMOVE"
        self.btn_img.setText("Imagem será removida")

    def save_folder(self):
        old_name = self.folder_data.get("label") if self.folder_data else None
        new_name = self.input_name.text().strip()
        if not new_name: return
        
        if old_name and old_name != new_name:
            old_path = os.path.join(self.parent_hub.icons_dir, f"folder_{old_name.lower()}.png")
            new_path = os.path.join(self.parent_hub.icons_dir, f"folder_{new_name.lower()}.png")
            if os.path.exists(old_path): os.rename(old_path, new_path)
        
        # O SEGOTE DE OUVIR O CHECKBOX E ENVIAR AO MOTOR DE IMAGEM
        if self.selected_img == "REMOVE":
            target = os.path.join(self.parent_hub.icons_dir, f"folder_{new_name.lower()}.png")
            if os.path.exists(target): os.remove(target)
        elif self.selected_img:
            dest_path = os.path.join(self.parent_hub.icons_dir, f"folder_{new_name.lower()}.png")
            process_and_save_icon(self.selected_img, dest_path, transparent=self.check_transparent.isChecked())
            
        # Salva as decisões
        if self.folder_data:
            self.folder_data.update({
                "label": new_name, 
                "subtitle": self.input_sub.text(),
                "transparent_icon": self.check_transparent.isChecked()
            })
        else:
            self.parent_hub.folders_list.append({
                "label": new_name, 
                "subtitle": self.input_sub.text(), 
                "type": "folder", 
                "buttons": [], 
                "color": self.parent_hub.accent_color,
                "transparent_icon": self.check_transparent.isChecked()
            })
            
        self.parent_hub.save_settings(force=True)
        self.parent_hub.filter_buttons_by_search(self.parent_hub.search_filter)
        self.accept()