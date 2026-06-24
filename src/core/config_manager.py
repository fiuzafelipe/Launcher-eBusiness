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
            {"label": "Tickets", "subtitle": "Ticket chamados", "url": "https://raphanet.confirm8.com/tickets", "favorite": False},
            {"label": "Confirm8", "subtitle": "Novo chamado", "url": "https://raphanet.confirm8.com/tickets/new", "favorite": False},
            {"label": "WhatsApp", "subtitle": "Mensagens Web", "url": "https://web.whatsapp.com/", "favorite": False},
            {"label": "Ticket Socin", "subtitle": "Suporte Socin", "url": "https://socin.movidesk.com/", "favorite": False},
            {"label": "Ticket Skyone", "subtitle": "Suporte Skyone", "url": "https://console.skyone.cloud/", "favorite": False},
            {"label": "Google Keep", "subtitle": "Suas anotações", "url": "https://keep.google.com/", "favorite": False},
            {"label": "AnyDesk / Remoto", "subtitle": "Acesso Remoto", "url": "remote://anydesk", "favorite": False}
        ]

    def get_default_data(self):
        """Retorna a estrutura inicial padrão do sistema."""
        return {
            "auto_save": False,
            "save_tabs_enabled": False,
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