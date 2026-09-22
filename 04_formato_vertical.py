import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

def crear_imagen_titulo(texto, ancho, alto=300, ruta_salida="temp_titulo.png"):
    """
    Crea una imagen transparente con el texto estilizado (estilo viral) usando Pillow.
    """
    # Crear imagen transparente
    img = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Intentar cargar una fuente gruesa (Impact o Arial Black)
    try:
        # En Windows, Impact suele estar aquí
        font = ImageFont.truetype("impact.ttf", 90)
    except IOError:
        try:
            font = ImageFont.truetype("arialbd.ttf", 80) # Arial Bold
        except IOError:
            font = ImageFont.load_default()
            
    # Calcular tamaño del texto para centrarlo
    # Usamos textbbox en lugar de textsize (que está deprecado en Pillow nuevo)
    try:
        bbox = draw.textbbox((0, 0), texto, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback para versiones antiguas de Pillow
        text_width, text_height = draw.textsize(texto, font=font)
        
    x = (ancho - text_width) / 2
    y = (alto - text_height) / 2
    
    # Colores estilo viral
    color_texto = (255, 255, 0, 255) # Amarillo brillante
    color_borde = (0, 0, 0, 255)     # Negro
    grosor_borde = 5
    
    # Dibujar el borde (stroke) dibujando el texto desplazado en varias direcciones
    for adj_x in range(-grosor_borde, grosor_borde + 1):
        for adj_y in range(-grosor_borde, grosor_borde + 1):
            draw.text((x + adj_x, y + adj_y), texto, font=font, fill=color_borde)
            
    # Dibujar el texto principal encima
    draw.text((x, y), texto, font=font, fill=color_texto)
    
    # Guardar la imagen temporalmente para que FFmpeg la use
    img.save(ruta_salida)
    return ruta_salida

def crear_video_vertical(ruta_clip, titulo_o_imagen, nombre_salida, carpeta_destino="clips_finales", ruta_logo=None, es_imagen_titulo=False):
    """
    Toma un clip horizontal, lo pone en un lienzo vertical (9:16) con fondo negro,
    le añade un título (texto o imagen) en la parte superior y opcionalmente un logo en la esquina inferior derecha.
    Limpia todos los metadatos para evitar detección en TikTok.
    """
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"Carpeta '{carpeta_destino}' creada.")

    ruta_salida = os.path.join(carpeta_destino, nombre_salida)
    ruta_titulo_temp = "temp_titulo.png"
    
    print(f"Procesando {ruta_clip} a formato vertical (Modo Ultra Rápido)...")
    try:
        # 1. Preparar la imagen del título (generada o proporcionada por el usuario)
        if es_imagen_titulo and os.path.exists(titulo_o_imagen):
            # Usar la imagen proporcionada por el usuario
            ruta_titulo_final = titulo_o_imagen
        else:
            # Generar la imagen con texto
            crear_imagen_titulo(titulo_o_imagen, 1080, 300, ruta_titulo_temp)
            ruta_titulo_final = ruta_titulo_temp
        
        # 2. Construir el comando FFmpeg
        comando = [
            "ffmpeg",
            "-y", # Sobrescribir
            "-i", ruta_clip, # Entrada 0: El video
            "-i", ruta_titulo_final, # Entrada 1: El título (texto o imagen)
        ]
        
        # Ajustar el overlay del título dependiendo de si es imagen o texto
        # Si es imagen personalizada, la escalamos a 1080 de ancho y la ponemos hasta arriba (y=0)
        # Si es texto generado, lo ponemos un poco más abajo (y=150)
        escala_titulo = "[1:v]scale=1080:-1[tit_escalado];" if es_imagen_titulo else ""
        entrada_titulo = "[tit_escalado]" if es_imagen_titulo else "[1:v]"
        pos_y_titulo = "0" if es_imagen_titulo else "150"

        # Si hay logo, lo añadimos como entrada 2
        if ruta_logo and os.path.exists(ruta_logo):
            comando.extend(["-i", ruta_logo])
            filter_complex = (
                f"[0:v]scale=1080:-1[vid];"
                f"color=c=black:s=1080x1920[bg];"
                f"{escala_titulo}"
                f"[bg][vid]overlay=0:(H-h)/2:shortest=1[bg_vid];"
                f"[bg_vid]{entrada_titulo}overlay=0:{pos_y_titulo}[bg_vid_tit];"
                f"[2:v]scale=200:-1[logo];"
                f"[bg_vid_tit][logo]overlay=W-w-50:H-h-50"
            )
        else:
            # Filter complex sin logo
            filter_complex = (
                f"[0:v]scale=1080:-1[vid];"
                f"color=c=black:s=1080x1920[bg];"
                f"{escala_titulo}"
                f"[bg][vid]overlay=0:(H-h)/2:shortest=1[bg_vid];"
                f"[bg_vid]{entrada_titulo}overlay=0:{pos_y_titulo}"
            )
            
        comando.extend([
            "-filter_complex", filter_complex,
            "-c:v", "libx264", # Codec de video
            "-preset", "ultrafast", # Renderizado súper rápido
            "-c:a", "copy", # Copiar el audio tal cual
            "-map_metadata", "-1", # ¡CRÍTICO! Borrar todos los metadatos para TikTok
            ruta_salida
        ])
        
        print("Renderizando con FFmpeg...")
        # Ejecutar FFmpeg
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Limpiar archivo temporal (solo si se generó texto)
        if not es_imagen_titulo and os.path.exists(ruta_titulo_temp):
            os.remove(ruta_titulo_temp)
            
        print(f"¡Video vertical creado exitosamente en: {ruta_salida}!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error de FFmpeg al crear el video vertical.")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

if __name__ == "__main__":
    print("=== Creador de Formato Vertical (TikTok/Shorts/Reels) ===")
    carpeta_clips = "clips_recortados"
    
    if not os.path.exists(carpeta_clips) or not os.listdir(carpeta_clips):
        print(f"No hay clips en '{carpeta_clips}'. Ejecuta 03_seleccionar_clips.py primero.")
        exit()

    # Listar clips disponibles
    print("Clips disponibles:")
    clips = [f for f in os.listdir(carpeta_clips) if f.endswith(('.mp4', '.mkv', '.webm'))]
    for i, clip in enumerate(clips):
        print(f"{i + 1}. {clip}")
        
    seleccion_clip = input("\nIngresa el número del clip que quieres convertir a vertical: ")
    
    try:
        indice_clip = int(seleccion_clip) - 1
        if 0 <= indice_clip < len(clips):
            nombre_clip = clips[indice_clip]
            ruta_clip = os.path.join(carpeta_clips, nombre_clip)
            
            print("\nOpciones para el título superior:")
            print("1. Escribir un texto (se generará automáticamente)")
            print("2. Usar una imagen personalizada (ej. mi_titulo.jpg)")
            opcion_titulo = input("Elige una opción (1 o 2): ")
            
            es_imagen_titulo = False
            if opcion_titulo == '2':
                titulo = input("Ingresa el nombre de tu imagen (ej. mi_titulo.jpg): ")
                if not os.path.exists(titulo):
                    print(f"Error: No se encontró la imagen '{titulo}'. Se usará texto por defecto.")
                    titulo = "CLIP VIRAL"
                else:
                    es_imagen_titulo = True
            else:
                titulo = input("Ingresa el título llamativo para la parte superior del video: ")
            
            # Preguntar por el logo
            usar_logo = input("\n¿Quieres añadir tu logo 'imagenpersonal.jpg' en la esquina inferior derecha? (s/n): ").lower()
            ruta_logo = "imagenpersonal.jpg" if usar_logo == 's' else None
            
            if ruta_logo and not os.path.exists(ruta_logo):
                print(f"Advertencia: No se encontró el archivo '{ruta_logo}'. Se continuará sin logo.")
                ruta_logo = None
            
            nombre_salida = f"vertical_{nombre_clip}"
            
            crear_video_vertical(ruta_clip, titulo, nombre_salida, ruta_logo=ruta_logo, es_imagen_titulo=es_imagen_titulo)
        else:
            print("Número de clip inválido.")
    except ValueError:
        print("Por favor, ingresa un número válido.")
