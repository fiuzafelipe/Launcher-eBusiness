import os

def launch_remote_tool(tool_name):
    """
    Módulo dedicado para lidar com integrações do Windows 
    (ex: abrir o AnyDesk localmente via remote://anydesk)
    """
    print(f"Tentando iniciar ferramenta local: {tool_name}")
    # Insira aqui os códigos os.system ou subprocess para rodar .exe locais