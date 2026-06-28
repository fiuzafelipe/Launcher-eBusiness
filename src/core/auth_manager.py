import os
import threading
from google_auth_oauthlib.flow import InstalledAppFlow

class AuthManager:
    def __init__(self, config_manager, success_callback=None):
        self.config_manager = config_manager
        self.success_callback = success_callback
        self.token = None
        self.credentials = None

    def start_login_flow(self):
        # Executa o fluxo em uma thread separada para não travar a interface do PyQt6
        threading.Thread(target=self._run_flow, daemon=True).start()

    def _run_flow(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Este é o arquivo que você vai baixar do Google Cloud Console
            creds_path = os.path.join(current_dir, "client_secret.json")
            
            if not os.path.exists(creds_path):
                print("[ERRO] Arquivo client_secret.json não encontrado na pasta core!")
                return

            # Escopos básicos para ler o perfil e e-mail do usuário
            scopes = [
                'openid', 
                'https://www.googleapis.com/auth/userinfo.email', 
                'https://www.googleapis.com/auth/userinfo.profile'
            ]
            
            # Inicializa o fluxo OAuth2
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
            
            # Abre o navegador padrão do Windows e cria o servidor local temporário
            # port=0 faz com que o Python escolha qualquer porta livre no computador
            self.credentials = flow.run_local_server(port=0)
            
            # Salva o token gerado para manter o usuário logado
            self.save_session(self.credentials.token)
            
            # Avisa a interface gráfica que o login terminou com sucesso
            if self.success_callback:
                self.success_callback()
                
        except Exception as e:
            print(f"[ERRO] Falha no fluxo de autenticação: {e}")

    def save_session(self, token):
        self.token = token
        data = self.config_manager.load()
        data['auth_token'] = token
        self.config_manager.save(data)
        print("Sessão salva com sucesso!")

    def logout(self):
        self.token = None
        self.credentials = None
        data = self.config_manager.load()
        if 'auth_token' in data:
            del data['auth_token']
            self.config_manager.save(data)
            print("Usuário deslogado. Token removido.")