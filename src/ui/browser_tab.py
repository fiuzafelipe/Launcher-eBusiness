from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QColor

class BrowserTab(QWebEngineView):
    def __init__(self, hub, profile, url, title, is_pinned=False, lazy_load=False):
        super().__init__(hub)
        self.hub = hub
        
        # Cria a página associada ao profile persistente (que contém a sessão Google)
        self.web_page = QWebEnginePage(profile, self)
        self.setPage(self.web_page)
        
        # =================================================================
        # CONFIGURAÇÕES ESPECÍFICAS (INTOCADAS)
        # =================================================================
        if "whatsapp.com" in url:
            self.web_page.profile().setHttpUserAgent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
            
        self.setProperty("original_url", url)
        self.setProperty("original_label", title)
        self.setProperty("is_pinned", is_pinned)
        self.setProperty("needs_load", lazy_load)
        
        # Conecta os sinais da aba diretamente aos métodos da própria classe
        self.titleChanged.connect(self.handle_title_changed)
        self.page().zoomFactorChanged.connect(self.handle_zoom_changed)
        self.loadFinished.connect(self.apply_whatsapp_theme)
        
        # Controle de carregamento (Lazy Load para otimização de memória)
        if not lazy_load:
            self.setUrl(QUrl(url))
            if url in self.hub.zoom_settings:
                self.setZoomFactor(self.hub.zoom_settings[url])

    def handle_title_changed(self, title):
        """Avisa a janela principal que o título mudou para atualizar o texto da aba"""
        self.hub.update_tab_title(self, title)

    def handle_zoom_changed(self, factor):
        """Salva o zoom de forma independente"""
        try:
            url = self.property("original_url") or self.url().toString()
            if url and url != "about:blank":
                self.hub.zoom_settings[url] = factor
                if getattr(self.hub, 'save_tabs_enabled', False):
                    self.hub.save_settings(force=True)
        except RuntimeError:
            pass

    def apply_whatsapp_theme(self, ok=True):
        """Injeta o tema (Claro/Escuro) automaticamente assim que o WhatsApp carrega"""
        if ok and "whatsapp.com" in self.url().toString():
            # Verifica o brilho da cor base do tema ativo no hub
            is_light = QColor(self.hub.get_active_theme_color()).lightness() > 128
            theme_class = 'light' if is_light else 'dark'
            
            script = f"(function() {{ document.body.classList.remove('theme-light', 'theme-dark'); document.body.classList.add('theme-{theme_class}'); document.documentElement.style.colorScheme = '{theme_class}'; }})();"
            self.page().runJavaScript(script)