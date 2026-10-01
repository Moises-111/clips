import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

import textwrap

def crear_imagen_titulo(texto, ancho, alto=300, ruta_salida="temp_titulo.png"):
    """
    Crea una imagen transparente con el texto estilizado (estilo viral) usando Pillow.
    Ajusta automáticamente el texto largo en varias líneas para que no se corte.
    """
    # Crear imagen transparente
    img = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Intentar cargar una fuente gruesa (Impact o Arial Black)
    tamano_fuente = 90
    try:
        font = ImageFont.truetype("impact.ttf", tamano_fuente)
    except IOError:
        try:
            font = ImageFont.truetype("arialbd.ttf", 80)
            tamano_fuente = 80
        except IOError:
            font = ImageFont.load_default()
            tamano_fuente = 20

    # Dividir el texto en líneas si es muy largo (aprox 20 caracteres por línea para tamaño 90)
    # Ajustamos el ancho de envoltura dependiendo de la longitud del texto
    caracteres_por_linea = 22
    if len(texto) > caracteres_por_linea:
        lineas = textwrap.wrap(texto, width=caracteres_por_linea)
    else:
        lineas = [texto]

    # Colores estilo viral
    color_texto = (255, 255, 0, 255) # Amarillo brillante
    color_borde = (0, 0, 0, 255)     # Negro
    grosor_borde = 5

    # Calcular la altura total de todas las líneas para centrarlas verticalmente
    altura_total = 0
    alturas_lineas = []
    
    for linea in lineas:
        try:
            bbox = draw.textbbox((0, 0), linea, font=font)
            h = bbox[3] - bbox[1]
        except AttributeError:
            _, h = draw.textsize(linea, font=font)
        alturas_lineas.append(h)
        altura_total += h + 10 # 10px de espacio entre líneas

    # Posición Y inicial para que el bloque de texto quede centrado verticalmente
    y_actual = (alto - altura_total) / 2

    # Dibujar cada línea centrada horizontalmente
    for i, linea in enumerate(lineas):
        try:
            bbox = draw.textbbox((0, 0), linea, font=font)
            text_width = bbox[2] - bbox[0]
        except AttributeError:
            text_width, _ = draw.textsize(linea, font=font)
            
        x = (ancho - text_width) / 2
        
        # Dibujar el borde (stroke)
        for adj_x in range(-grosor_borde, grosor_borde + 1):
            for adj_y in range(-grosor_borde, grosor_borde + 1):
                draw.text((x + adj_x, y_actual + adj_y), linea, font=font, fill=color_borde)
                
        # Dibujar el texto principal encima
        draw.text((x, y_actual), linea, font=font, fill=color_texto)
        
        # Mover Y para la siguiente línea
        y_actual += alturas_lineas[i] + 10
    
    # Guardar la imagen temporalmente para que FFmpeg la use
    img.save(ruta_salida)
    return ruta_salida

def crear_video_vertical(ruta_clip, titulo_o_imagen, nombre_salida, carpeta_destino="clips_finales", es_imagen_titulo=False, modo_audio="original", ruta_audio=None):
    """
    Toma un clip horizontal, lo pone en un lienzo vertical (9:16) con fondo borroso (blur) dinámico,
    le añade un título (texto o imagen) en la parte superior.
    Limpia todos los metadatos para evitar detección en TikTok.
    """
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"Carpeta '{carpeta_destino}' creada.")

    if modo_audio not in ("original", "silencio", "reemplazar"):
        print("Modo de audio inválido.")
        return False
    if modo_audio == "reemplazar" and (not ruta_audio or not os.path.isfile(ruta_audio)):
        print(f"No se encontró el archivo de audio: {ruta_audio}")
        return False

    ruta_salida = os.path.join(carpeta_destino, nombre_salida)
    ruta_titulo_temp = "temp_titulo.png"
    
    print(f"Procesando {ruta_clip} a formato vertical (Modo Acelerado)...")
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
        if modo_audio == "reemplazar":
            comando.extend(["-stream_loop", "-1", "-i", ruta_audio])
        
        # Ajustar el overlay del título dependiendo de si es imagen o texto
        escala_titulo = "[1:v]scale=1080:-1[tit_escalado];" if es_imagen_titulo else ""
        entrada_titulo = "[tit_escalado]" if es_imagen_titulo else "[1:v]"
        pos_y_titulo = "0" if es_imagen_titulo else "150"

        # Filter complex ANTI-BANEO TIKTOK (Versión fluida):
        # 1. Procesa el fondo a media resolución antes de ampliarlo para reducir el coste del desenfoque
        # 2. [0:v]scale=1080:-1[vid] -> Escala el video principal (sin zoom para evitar lentitud)
        # 3. [bg][vid]overlay=0:(H-h)/2:shortest=1[bg_vid] -> Pone el video sobre el fondo borroso
        # 4. [bg_vid]{entrada_titulo}overlay=0:{pos_y_titulo} -> Pone el título
        filter_complex = (
            f"[0:v]scale=540:960:force_original_aspect_ratio=increase,crop=540:960,boxblur=10:10,scale=1080:1920[bg];"
            f"[0:v]scale=1080:-1[vid];"
            f"{escala_titulo}"
            f"[bg][vid]overlay=0:(H-h)/2:shortest=1[bg_vid];"
            f"[bg_vid]{entrada_titulo}overlay=0:{pos_y_titulo}[vout]"
        )
            
        comando.extend([
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-c:v", "libx264",
            "-preset", "ultrafast",
        ])
        if modo_audio == "silencio":
            comando.append("-an")
        elif modo_audio == "reemplazar":
            comando.extend(["-map", "2:a:0", "-c:a", "aac", "-b:a", "192k", "-shortest"])
        else:
            comando.extend(["-map", "0:a?", "-c:a", "copy"])
        comando.extend(["-map_metadata", "-1", ruta_salida])
        
        print("Renderizando con FFmpeg...")
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        
        # Limpiar archivo temporal (solo si se generó texto)
        if not es_imagen_titulo and os.path.exists(ruta_titulo_temp):
            os.remove(ruta_titulo_temp)
            
        print(f"¡Video vertical creado exitosamente en: {ruta_salida}!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error de FFmpeg al crear el video vertical.")
        if e.stderr:
            print("Detalle de FFmpeg:\n" + "\n".join(e.stderr.splitlines()[-12:]))
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

            print("\nOpciones de audio:")
            print("1. Conservar el audio original")
            print("2. Silenciar el video")
            print("3. Reemplazarlo con una pista propia o con licencia")
            opcion_audio = input("Elige una opción (1, 2 o 3): ").strip()
            modo_audio = {"1": "original", "2": "silencio", "3": "reemplazar"}.get(opcion_audio, "original")
            ruta_audio = None
            if modo_audio == "reemplazar":
                ruta_audio = input("Ingresa la ruta del archivo de audio autorizado: ").strip().strip('"')
            
            nombre_salida = f"vertical_{nombre_clip}"
            
            print("\n[INFO] Aplicando técnicas anti-baneo de TikTok (Fondo borroso dinámico, sin metadatos)...")
            crear_video_vertical(ruta_clip, titulo, nombre_salida, es_imagen_titulo=es_imagen_titulo, modo_audio=modo_audio, ruta_audio=ruta_audio)
        else:
            print("Número de clip inválido.")
    except ValueError:
        print("Por favor, ingresa un número válido.")
