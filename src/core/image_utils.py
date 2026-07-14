import os
from PyQt6.QtGui import QImage, QColor
from PyQt6.QtCore import Qt

def process_and_save_icon(source_path, dest_path, target_size=72, tolerance=25, transparent=False):
    """
    Carrega uma imagem, opcionalmente remove o fundo com base no tom do pixel (0,0),
    redimensiona e salva em formato PNG.
    """
    image = QImage(source_path)
    if image.isNull():
        print(f"[ImageUtils] Erro: Não foi possível carregar a imagem em '{source_path}'")
        return False

    # Redimensionamento inteligente
    image = image.scaled(
        target_size, 
        target_size, 
        Qt.AspectRatioMode.KeepAspectRatio, 
        Qt.TransformationMode.SmoothTransformation
    )
    
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    
    # ----------------------------------------------------
    # NOVA LÓGICA: SÓ REMOVE O FUNDO SE TRANSPARENT=TRUE
    # ----------------------------------------------------
    if transparent:
        bg_color = image.pixelColor(0, 0)
        for y in range(image.height()):
            for x in range(image.width()):
                pixel_color = image.pixelColor(x, y)
                if (abs(pixel_color.red() - bg_color.red()) <= tolerance and
                    abs(pixel_color.green() - bg_color.green()) <= tolerance and
                    abs(pixel_color.blue() - bg_color.blue()) <= tolerance):
                    image.setPixelColor(x, y, QColor(0, 0, 0, 0)) 
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    success = image.save(dest_path, "PNG")
    if success:
        print(f"[ImageUtils] Ícone salvo com sucesso em: '{dest_path}'")
    else:
        print(f"[ImageUtils] Erro crítico ao tentar gravar: '{dest_path}'")
        
    return success