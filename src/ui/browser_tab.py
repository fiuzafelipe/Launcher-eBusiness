from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QColor

class BrowserTab(QWebEngineView):
    def __init__(self, hub, profile, url, title, is_pinned=False, lazy_load=False):
        super().__init__(hub)
        self.hub = hub
        self.web_page = QWebEnginePage(profile, self)
        
        # Permissões vitais para Lives e Vídeos funcionarem
        settings = self.web_page.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        
        self.setPage(self.web_page)
        
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
        
        self.titleChanged.connect(self.handle_title_changed)
        self.page().zoomFactorChanged.connect(self.handle_zoom_changed)
        self.loadFinished.connect(self.apply_whatsapp_theme)
        
        # --- NOVO: Escuta o áudio da aba ---
        self.page().recentlyAudibleChanged.connect(self.handle_audio_changed)
        
        if not lazy_load:
            self.setUrl(QUrl(url))
            if url in self.hub.zoom_settings:
                self.setZoomFactor(self.hub.zoom_settings[url])
        
        self.page().fullScreenRequested.connect(self.handle_fullscreen)

    def handle_fullscreen(self, request):
        if request.toggleOn():
            # Salva o estado atual (se estava maximizado ou normal)
            self.previous_state = self.hub.windowState()
            self.hub.showFullScreen() # Isso coloca o HUB inteiro em Fullscreen
            request.accept()
        else:
            self.hub.showNormal() # Tira do modo fullscreen forçado
            # Restaura o estado anterior (se era maximizado, volta a ser)
            if hasattr(self, 'previous_state'):
                self.hub.setWindowState(self.previous_state)
            request.accept()

    def handle_title_changed(self, title):
        self.hub.update_tab_title(self, title)

    def handle_zoom_changed(self, factor):
        try:
            url = self.property("original_url") or self.url().toString()
            if url and url != "about:blank":
                self.hub.zoom_settings[url] = factor
                if getattr(self.hub, 'save_tabs_enabled', False):
                    self.hub.save_settings(force=True)
        except RuntimeError:
            pass

    def apply_whatsapp_theme(self, ok=True):
        if ok and "whatsapp.com" in self.url().toString():
            is_light = QColor(self.hub.get_active_theme_color()).lightness() > 128
            theme_class = 'light' if is_light else 'dark'
            script = f"(function() {{ document.body.classList.remove('theme-light', 'theme-dark'); document.body.classList.add('theme-{theme_class}'); document.documentElement.style.colorScheme = '{theme_class}'; }})();"
            self.page().runJavaScript(script)

    # --- NOVO: Função do Áudio ---
    def handle_audio_changed(self, audible):
        self.hub.update_tab_audio_indicator(self, audible)