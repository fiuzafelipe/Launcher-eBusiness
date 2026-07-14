from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt6.QtCore import QByteArray

class AppInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.modern_ua = b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        
        # Lista de domínios para bloquear anúncios
        self.blocked_domains = [
            "doubleclick.net", "googleadservices.com", "adservice.google.com",
            "tpc.googlesyndication.com", "ads.youtube.com", "pagead2.googlesyndication.com",
            "static.doubleclick.net", "ad.doubleclick.net"
        ]
        
        # Lista de sites que precisam de UA moderno
        self.media_sites = ["youtube.com", "twitch.tv", "ytimg.com", "ggpht.com"]

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        # Bloqueio agressivo
        blocked_domains = [
            "doubleclick.net", "googleadservices.com", "adservice.google.com",
            "tpc.googlesyndication.com", "ads.youtube.com", "pagead2.googlesyndication.com",
            "static.doubleclick.net", "ad.doubleclick.net", "s.youtube.com/api/stats/ads"
        ]
        if any(domain in url for domain in blocked_domains):
            info.block(True)
            return
            
        # 2. INJEÇÃO DE USER-AGENT
        # Se for um site de mídia, aplicamos o UA moderno
        if any(site in url for site in self.media_sites):
            info.setHttpHeader(b"User-Agent", self.modern_ua)