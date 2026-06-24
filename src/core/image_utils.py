import os
from PyQt6.QtGui import QImage, QColor
from PyQt6.QtCore import Qt

def process_and_save_icon(source_path, dest_path, target_size=72, tolerance=25):
    """
    Carrega uma imagem, remove o fundo com base no tom do pixel superior esquerdo (0,0)
    dentro de uma faixa de tolerância, redimensiona e salva em formato PNG transparente.
    
    :param source_path: Caminho do arquivo de imagem original.
    :param dest_path: Caminho completo onde o ícone processado será salvo.
    :param target_size: Tamanho máximo (largura/altura) do ícone final.
    :param tolerance: Tolerância para a remoção da cor de fundo.
    :return: True se a imagem foi salva com sucesso, False caso contrário.
    """
    image = QImage(source_path)
    if image.isNull():
        print(f"[ImageUtils] Erro: Não foi possível carregar a imagem em '{source_path}'")
        return False

    # Redimensionamento inteligente mantendo a proporção e aplicando anti-aliasing (SmoothTransformation)
    image = image.scaled(
        target_size, 
        target_size, 
        Qt.AspectRatioMode.KeepAspectRatio, 
        Qt.TransformationMode.SmoothTransformation
    )
    
    # Converte para o formato ARGB de 32 bits que dá suporte a canal Alpha (transparência)
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    
    # Define o pixel de referência para a cor que será removida (geralmente o fundo)
    bg_color = image.pixelColor(0, 0)
    
    # Varre a matriz de pixels aplicando a máscara de transparência
    for y in range(image.height()):
        for x in range(image.width()):
            pixel_color = image.pixelColor(x, y)
            
            # Verifica se a cor do pixel atual está dentro da tolerância da cor de fundo
            if (abs(pixel_color.red() - bg_color.red()) <= tolerance and
                abs(pixel_color.green() - bg_color.green()) <= tolerance and
                abs(pixel_color.blue() - bg_color.blue()) <= tolerance):
                
                # Substitui por um pixel totalmente transparente (Alpha = 0)
                image.setPixelColor(x, y, QColor(0, 0, 0, 0)) 
                
    # Garante que a pasta de destino exista antes de tentar salvar
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # Salva o arquivo final em formato PNG
    success = image.save(dest_path, "PNG")
    if success:
        print(f"[ImageUtils] Ícone processado e salvo com sucesso em: '{dest_path}'")
    else:
        print(f"[ImageUtils] Erro crítico ao tentar gravar o arquivo em: '{dest_path}'")
        
    return success