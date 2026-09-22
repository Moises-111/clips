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

def crear_video_vertical(ruta_clip, titulo, nombre_salida, carpeta_destino="clips_finales"):
    """
    Toma un clip horizontal, lo pone en un lienzo vertical (9:16) con fondo negro,
    y le añade un título en la parte superior usando FFmpeg directamente (Súper rápido).
    """
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"Carpeta '{carpeta_destino}' creada.")

    ruta_salida = os.path.join(carpeta_destino, nombre_salida)
    ruta_titulo_temp = "temp_titulo.png"
    
    print(f"Procesando {ruta_clip} a formato vertical (Modo Ultra Rápido)...")
    try:
        # 1. Crear la imagen del título
        crear_imagen_titulo(titulo, 1080, 300, ruta_titulo_temp)
        
        # 2. Comando FFmpeg complejo (Filter Complex)
        # - Escala el video a 1080 de ancho manteniendo proporción
        # - Crea un fondo negro de 1080x1920
        # - Pone el video en el centro del fondo negro
        # - Pone el título en la parte superior (y=150)
        # - shortest=1 asegura que el video termine cuando termine el clip original
        comando = [
            "ffmpeg",
            "-y", # Sobrescribir
            "-i", ruta_clip, # Entrada 0: El video
            "-i", ruta_titulo_temp, # Entrada 1: El título
            "-filter_complex", 
            "[0:v]scale=1080:-1[vid];" + # Escalar video
            "color=c=black:s=1080x1920[bg];" + # Crear fondo negro
            "[bg][vid]overlay=0:(H-h)/2:shortest=1[bg_vid];" + # Centrar video y detener al terminar el clip
            "[bg_vid][1:v]overlay=0:150", # Poner título arriba
            "-c:v", "libx264", # Codec de video
            "-preset", "ultrafast", # Renderizado súper rápido
            "-c:a", "copy", # Copiar el audio tal cual (instantáneo)
            ruta_salida
        ]
        
        print("Renderizando con FFmpeg...")
        # Ejecutar FFmpeg
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Limpiar archivo temporal
        if os.path.exists(ruta_titulo_temp):
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
            
            titulo = input("Ingresa el título llamativo para la parte superior del video: ")
            
            nombre_salida = f"vertical_{nombre_clip}"
            
            crear_video_vertical(ruta_clip, titulo, nombre_salida)
        else:
            print("Número de clip inválido.")
    except ValueError:
        print("Por favor, ingresa un número válido.")
