import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QComboBox, QCheckBox, QLabel, QColorDialog, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor # <- Resolvido NameError aqui!

# Importações dos modais necessários que permaneceram no outro arquivo
from ui.dialogs import ToolboxDialog, DeleteToolboxDialog

class ThemeModeDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_hub = parent
        self.setWindowTitle("Modo de Tema")
        self.setFixedWidth(350)
        self.setWindowOpacity(0.92)
        
        accent = self.parent_hub.accent_color
        c_accent = QColor(accent)
        text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {accent}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; }}
            QPushButton {{ background-color: {accent}; color: {text_color}; font-family: 'Segoe UI'; font-weight: 600; padding: 12px; border-radius: 6px; font-size: 13px; border: 1px solid #000000; text-align: left; padding-left: 20px; }}
            QPushButton:hover {{ background-color: {hover_dark_tint}; border-color: {accent}; color: {accent}; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(15)
        
        lbl = QLabel("Escolha a luminosidade da interface:")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        
        btn_escuro = QPushButton("🌙  Modo Escuro (Fundo Preto)")
        btn_claro = QPushButton("☀️  Modo Claro (Fundo Branco)")
        
        btn_escuro.clicked.connect(lambda: self.set_mode("Escuro"))
        btn_claro.clicked.connect(lambda: self.set_mode("Claro"))
        
        layout.addWidget(btn_escuro)
        layout.addWidget(btn_claro)

    def set_mode(self, mode):
        self.parent_hub.theme_mode = mode
        self.parent_hub.apply_styles()
        self.parent_hub.create_home_tab()
        self.parent_hub.save_settings(force=True)
        self.accept()


class PresetsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_hub = parent
        self.setWindowTitle("Selecionar Tema Pré-definido")
        self.setFixedWidth(380)
        self.setWindowOpacity(0.92)
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {self.parent_hub.accent_color}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }}
            QComboBox {{ background-color: #161b24; border: 1px solid {self.parent_hub.accent_color}; border-radius: 6px; color: #fff; padding: 10px; font-family: 'Segoe UI'; font-size: 13px; }}
            QPushButton {{ background-color: {self.parent_hub.accent_color}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(QLabel("Escolha uma das 10 paletas prontas abaixo:"))
        
        self.combo = QComboBox()
        self.combo.addItems(list(self.parent_hub.presets.keys()))
        layout.addWidget(self.combo)
        
        btn_box = QHBoxLayout()
        btn_apply = QPushButton("Aplicar Tema")
        btn_back = QPushButton("Cancelar")
        btn_back.setStyleSheet("background-color: #161b24; color: #fff; padding: 10px; border-radius: 6px;")
        
        btn_apply.clicked.connect(self.apply_preset)
        btn_back.clicked.connect(self.reject)
        btn_box.addWidget(btn_apply)
        btn_box.addWidget(btn_back)
        layout.addLayout(btn_box)

    def apply_preset(self):
        preset_name = self.combo.currentText()
        if preset_name in self.parent_hub.presets:
            selected = self.parent_hub.presets[preset_name]
            self.parent_hub.theme_base_color = selected["theme"]
            self.parent_hub.accent_color = selected["accent"]
            self.parent_hub.apply_styles()
            self.parent_hub.create_home_tab()
            self.parent_hub.save_settings(force=True)
            self.accept()


class BackgroundDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_hub = parent
        self.setWindowTitle("Configurar Imagem de Fundo")
        self.setFixedWidth(360)
        self.setWindowOpacity(0.92)
        self.setStyleSheet(f"""
            QDialog {{ background-color: #11141a; border: 1px solid {self.parent_hub.accent_color}; border-radius: 8px; }}
            QLabel {{ color: #ffffff; font-weight: bold; font-family: 'Segoe UI'; font-size: 13px; }}
            QPushButton {{ background-color: {self.parent_hub.accent_color}; color: #000; font-family: 'Segoe UI'; font-weight: bold; padding: 10px; border-radius: 6px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("Personalize o fundo do seu Standalone Hub:"))
        btn_add = QPushButton("Adicionar Imagem")
        btn_add.clicked.connect(self.select_bg)
        
        btn_del = QPushButton("Excluir Imagem")
        btn_del.setStyleSheet("background-color: #ff5252; color: white;")
        btn_del.clicked.connect(self.remove_bg)
        
        layout.addWidget(btn_add)
        layout.addWidget(btn_del)

    def select_bg(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem de Fundo", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.parent_hub.background_image_path = file_path
            self.parent_hub.update_wallpaper_brightness()
            self.parent_hub.save_settings(force=True)
            self.parent_hub.apply_styles()
            self.parent_hub.create_home_tab()
            self.accept()

    def remove_bg(self):
        self.parent_hub.background_image_path = ""
        self.parent_hub.is_wp_light = False
        self.parent_hub.save_settings(force=True)
        self.parent_hub.apply_styles()
        self.parent_hub.create_home_tab()
        self.accept()


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_hub = parent
        self.setWindowTitle("CONFIGURAÇÕES DO SISTEMA")
        self.setFixedWidth(380)
        self.setWindowOpacity(0.92)
        
        accent = self.parent_hub.accent_color
        c_accent = QColor(accent)
        text_color = "#07080a" if c_accent.lightness() > 140 else "#ffffff"
        hover_dark_tint = f"rgba({c_accent.red()}, {c_accent.green()}, {c_accent.blue()}, 0.40)"

        self.setStyleSheet(f"""
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
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 25, 20, 25)
        
        chk_auto_save = QCheckBox("Salvar automaticamente")
        chk_auto_save.setChecked(self.parent_hub.auto_save)
        chk_auto_save.stateChanged.connect(self.parent_hub.toggle_auto_save_from_checkbox)
        
        if self.parent_hub.security_settings.get("enabled", False):
            btn_security = QPushButton("🔓  Alterar ou Remover Senha")
            btn_security.clicked.connect(lambda: [self.accept(), self.parent_hub.open_security_modify()])
        else:
            btn_security = QPushButton("🔒  Definir Senha de Acesso")
            btn_security.clicked.connect(lambda: [self.accept(), self.parent_hub.open_security_setup()])

        btn_mode = QPushButton("🌗  Modo Escuro / Claro (Base)")
        btn_mode.clicked.connect(lambda: [self.accept(), ThemeModeDialog(self.parent_hub).exec()])
        
        btn_toolbox = QPushButton("＋  Adicionar Botão")
        btn_toolbox.clicked.connect(lambda: [self.accept(), ToolboxDialog(self.parent_hub).exec()])
        
        btn_delete_toolbox = QPushButton("🗙  Deletar Botão")
        btn_delete_toolbox.clicked.connect(lambda: [self.accept(), DeleteToolboxDialog(self.parent_hub).exec()])
        
        btn_presets = QPushButton("🎨  Temas Pré-definidos")
        btn_presets.clicked.connect(lambda: [self.accept(), PresetsDialog(self.parent_hub).exec()])
        
        btn_color = QPushButton("🎨  Alterar Cor de Destaque")
        btn_color.clicked.connect(lambda: [self.accept(), self.open_color_picker()])
        
        btn_theme = QPushButton("🎭  Alterar Cor do Fundo")
        btn_theme.clicked.connect(lambda: [self.accept(), self.open_theme_picker()])
        
        btn_bg_image = QPushButton("🖼️  Imagem de Fundo (Wallpaper)")
        btn_bg_image.clicked.connect(lambda: [self.accept(), BackgroundDialog(self.parent_hub).exec()])
        
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
        btn_save_man.clicked.connect(lambda: [self.parent_hub.save_settings(force=True), self.accept()])
        layout.addWidget(btn_save_man)
        
        btn_reset = QPushButton("🔄  Restaurar Padrões de Fábrica")
        btn_reset.setObjectName("btn_danger")
        btn_reset.clicked.connect(lambda: [self.parent_hub.reset_to_defaults(), self.accept()])
        layout.addWidget(btn_reset)

    def open_color_picker(self):
        color = QColorDialog.getColor(QColor(self.parent_hub.accent_color), self, "Escolha sua Cor de Destaque")
        if color.isValid():
            self.parent_hub.accent_color = color.name()
            self.parent_hub.apply_styles()
            self.parent_hub.create_home_tab()
            self.parent_hub.save_settings(force=True)

    def open_theme_picker(self):
        color = QColorDialog.getColor(QColor(self.parent_hub.theme_base_color), self, "Escolha a Cor do Fundo Geral")
        if color.isValid():
            self.parent_hub.theme_base_color = color.name()
            self.parent_hub.apply_styles()
            self.parent_hub.create_home_tab()
            self.parent_hub.save_settings(force=True)