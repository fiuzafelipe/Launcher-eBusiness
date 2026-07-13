import os
import shutil
from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEngineSettings, 
                                   QWebEngineUrlRequestInterceptor)

class HeaderInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        info.setHttpHeader(b"Accept-Language", b"pt-BR,pt;q=0.9,en-US;q=0.8")
        info.setHttpHeader(b"sec-ch-ua-platform", b'"Windows"')

class BrowserEngine:
    def __init__(self, parent_window):
        self.parent = parent_window
        app_data = os.getenv("LOCALAPPDATA")

        # Caminhos originais intocados
        self.old_storage_path = os.path.join(app_data, "FiuzaTechnology", "StandaloneHub", "BrowserSession")
        self.storage_path = os.path.join(app_data, "FiuzaTechnology", "CustomExplorer", "BrowserSession")

        self._migrate_session()

        # Criação do Profile exato
        self.profile = QWebEngineProfile("CustomExplorer", self.parent)
        self.profile.setPersistentStoragePath(self.storage_path)
        self.profile.setCachePath(os.path.join(self.storage_path, "cache"))

        # Mantém login Google (Intocado)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.profile.setPersistentPermissionsPolicy(QWebEngineProfile.PersistentPermissionsPolicy.StoreOnDisk)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        
        self.profile.setHttpUserAgent(QWebEngineProfile.defaultProfile().httpUserAgent())
        self.profile.setHttpAcceptLanguage("pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7")
        
        self.interceptor = HeaderInterceptor()
        self.profile.setUrlRequestInterceptor(self.interceptor)

        self._apply_security_settings()
        
        print("[SESSION] Custom Explorer profile persistente carregado:", self.storage_path)

    def _migrate_session(self):
        if os.path.exists(self.old_storage_path) and not os.path.exists(self.storage_path):
            try:
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                shutil.copytree(self.old_storage_path, self.storage_path)
                print("[SESSION] Sessão antiga migrada para Custom Explorer")
            except Exception as e:
                print("[SESSION MIGRATION ERROR]", e)
        os.makedirs(self.storage_path, exist_ok=True)

    def _apply_security_settings(self):
        settings = self.profile.settings()
        # Exatamente os mesmos parâmetros de segurança
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)

    def get_profile(self):
        """Retorna o profile configurado para ser usado nas abas."""
        return self.profile