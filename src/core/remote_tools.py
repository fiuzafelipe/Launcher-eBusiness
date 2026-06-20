import os
import subprocess

def launch_remote_tool(tool_name, target_id=""):
    """
    Dispara o AnyDesk ou UltraViewer local via linha de comando (CLI).
    """
    if tool_name.lower() == "anydesk":
        # Caminho padrão de instalação do AnyDesk no Windows
        path = r"C:\Program Files (x86)\AnyDesk\AnyDesk.exe"
        if os.path.exists(path):
            cmd = [path]
            if target_id:
                cmd.append(target_id)
            subprocess.Popen(cmd)
            return True
        else:
            # Tenta executar caso esteja mapeado nas variáveis de ambiente
            try:
                subprocess.Popen(["anydesk" if not target_id else f"anydesk {target_id}"])
                return True
            except FileNotFoundError:
                return False
                
    elif tool_name.lower() == "ultraviewer":
        # Caminho padrão do UltraViewer
        path = r"C:\Program Files (x86)\UltraViewer\UltraViewer_Desktop.exe"
        if os.path.exists(path):
            subprocess.Popen([path])
            return True
    return False