import os
import json

class ConfigManager:
    def __init__(self, config_path):
        """
        Gerenciador de configurações responsável pelo I/O do arquivo JSON.
        """
        self.config_file = config_path
        
        # Lista padrão encapsulada no gerenciador de dados
        self.default_buttons = [
            {"label": "Contako", "subtitle": "Chat de atendimento", "url": "https://atendimento.contako.com.br/", "favorite": False},
            {"label": "Confirm8", "subtitle": "Chamados", "url": "https://raphanet.confirm8.com/tickets", "favorite": False},
            {"label": "Confirm8", "subtitle": "Abertura de chamados", "url": "https://raphanet.confirm8.com/tickets/new", "favorite": False},
            {"label": "WhatsApp", "subtitle": "Rede social", "url": "https://web.whatsapp.com/", "favorite": False},
            {"label": "Ticket Socin", "subtitle": "Abertura de Tickets", "url": "https://socin.movidesk.com/", "favorite": False},
            {"label": "Ticket Skyone", "subtitle": "Abertura de Tickets", "url": "https://console.skyone.cloud/", "favorite": False},
            {"label": "Google Keep", "subtitle": "Anotações do Keep", "url": "https://keep.google.com/", "favorite": False},
            {"label": "BigData Wifi", "subtitle": "Chat Bigdata", "url": "https://chatbot.bigdatawifi.com.br/login", "favorite": False},
            {"label": "Gmail", "subtitle": "Acesso email", "url": "https://gmail.com", "favorite": False},
            {"label": "Ultraviewer", "subtitle": "Acesso remoto", "url": "remote://ultraviewer", "favorite": False},
            {"label": "Anydesk", "subtitle": "Acesso remoto", "url": "remote://anydesk", "favorite": False},
            {"label": "Teamviewer", "subtitle": "Acesso remoto", "url": "remote://teamviewer", "favorite": False},
            {"label": "Youtube", "subtitle": "Streaming de Videos", "url": "https://youtube.com", "favorite": False},
            {"label": "Notepad", "subtitle": "Anotações Raphanet", "url": "https://notepad.pw/raphanet", "favorite": False},
            {"label": "Sefaz", "subtitle": "Portal Monitoramento", "url": "https://nfce.sefaz.se.gov.br/portal/painelMonitor.jsp", "favorite": False},
            {"label": "Rentry", "subtitle": "Wiki Raphanet", "url": "https://rentry.org/raphanet", "favorite": False},
            {"label": "Rocketseat", "subtitle": "Curso de Programação", "url": "https://app.rocketseat.com.br/?type=ALL", "favorite": False}
        ]

    def get_default_data(self):
        """Retorna a estrutura inicial padrão do sistema."""
        return {
            "auto_save": True,
            "save_tabs_enabled": True,
            "theme_mode": "Escuro",
            "accent_color": "#d9d9d9",
            "theme_base_color": "#242120",
            "background_image_path": "",
            "buttons": self.default_buttons.copy(),
            "opened_tabs": [],
            "pinned_tabs": [],
            "zoom_settings": {},
            "security": {},
            "history": {}
        }

    def load(self):
        """Carrega as configurações do arquivo JSON ou retorna a estrutura padrão."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Sanity check para chaves obrigatórias que possam estar ausentes em JSONs antigos
                    if "buttons" not in data or not data["buttons"]:
                        data["buttons"] = self.default_buttons.copy()
                    
                    for b in data["buttons"]:
                        if "favorite" not in b:
                            b["favorite"] = False
                            
                    return data
            except Exception as e:
                print(f"[ConfigManager] Erro ao carregar arquivo. Usando padrões. Erro: {e}")
        
        return self.get_default_data()

    def save(self, data):
        """Salva um dicionário de dados estruturado no arquivo JSON."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"[ConfigManager] Erro ao salvar arquivo: {e}")
            return False

    def delete_config_file(self):
        """Remove o arquivo de configuração física do disco (Reset de fábrica)."""
        if os.path.exists(self.config_file):
            try:
                os.remove(self.config_file)
                return True
            except Exception as e:
                print(f"[ConfigManager] Erro ao deletar arquivo físico: {e}")
        return False