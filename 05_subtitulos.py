import os
import subprocess
import whisper

def format_time_ass(seconds):
    """Convierte segundos a formato de tiempo ASS (H:MM:SS.cc)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int(round((seconds - int(seconds)) * 100))
    if centisecs == 100:
        secs += 1
        centisecs = 0
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

def generar_archivo_ass(segmentos, ruta_ass, fuente="Impact", color_texto="&H0000FFFF", color_borde="&H00000000"):
    """
    Genera un archivo de subtítulos .ass con estilos personalizados.
    Colores en ASS son BGR (Blue, Green, Red) en formato hexadecimal: &H00BBGGRR
    Amarillo: &H0000FFFF
    Blanco: &H00FFFFFF
    Negro: &H00000000
    """
    # Cabecera del archivo ASS
    # Alignment 2 = Bottom Center. 
    # MarginV = 500 (distancia desde abajo, para que quede justo debajo del video central)
    # Outline = 8 (grosor del borde negro)
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralStyle,{fuente},80,{color_texto},&H000000FF,{color_borde},&H00000000,-1,0,0,0,100,100,0,0,1,8,0,2,10,10,500,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    for seg in segmentos:
        inicio = format_time_ass(seg['start'])
        fin = format_time_ass(seg['end'])
        texto = seg['text'].strip()
        # Limpiar saltos de línea
        texto = texto.replace('\n', ' ')
        ass_content += f"Dialogue: 0,{inicio},{fin},ViralStyle,,0,0,0,,{texto}\n"

    with open(ruta_ass, 'w', encoding='utf-8') as f:
        f.write(ass_content)

def quemar_subtitulos(ruta_video, ruta_ass, ruta_salida):
    """Usa FFmpeg para incrustar los subtítulos en el video."""
    print("Quemando subtítulos en el video (esto puede tardar un poco)...")
    
    comando = [
        "ffmpeg",
        "-y",
        "-i", ruta_video,
        "-vf", f"ass={ruta_ass}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "copy",
        ruta_salida
    ]
    
    try:
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al quemar subtítulos. Asegúrate de que FFmpeg esté bien instalado.")
        return False

if __name__ == "__main__":
    print("=== Generador de Subtítulos Virales ===")
    carpeta_clips = "clips_finales"
    carpeta_salida = "clips_subtitulados"
    
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)
        
    if not os.path.exists(carpeta_clips) or not os.listdir(carpeta_clips):
        print(f"No hay videos en '{carpeta_clips}'. Ejecuta 04_formato_vertical.py primero.")
        exit()

    print("Videos disponibles:")
    videos = [f for f in os.listdir(carpeta_clips) if f.endswith(('.mp4', '.mkv', '.webm'))]
    for i, video in enumerate(videos):
        print(f"{i + 1}. {video}")
        
    seleccion = input("\nIngresa el número del video al que quieres añadir subtítulos: ")
    
    try:
        indice = int(seleccion) - 1
        if 0 <= indice < len(videos):
            nombre_video = videos[indice]
            ruta_video = os.path.join(carpeta_clips, nombre_video)
            
            print("\nOpciones de estilo:")
            print("1. Letra Impact (Gruesa, ideal para TikTok)")
            print("2. Letra Arial (Clásica)")
            opcion_fuente = input("Elige la fuente (1 o 2): ")
            fuente = "Impact" if opcion_fuente == '1' else "Arial"
            
            print("\nColor del texto:")
            print("1. Amarillo (Viral)")
            print("2. Blanco")
            opcion_color = input("Elige el color (1 o 2): ")
            color_texto = "&H0000FFFF" if opcion_color == '1' else "&H00FFFFFF"
            
            print("\nCargando modelo de IA (Whisper) para transcribir el clip...")
            # Usamos el modelo 'base' para que sea rápido
            modelo = whisper.load_model("base")
            
            print("Transcribiendo el audio... (esto puede tomar unos segundos)")
            resultado = modelo.transcribe(ruta_video, language="es")
            
            ruta_ass = "temp_subs.ass"
            generar_archivo_ass(resultado['segments'], ruta_ass, fuente=fuente, color_texto=color_texto)
            
            nombre_salida = f"sub_{nombre_video}"
            ruta_salida = os.path.join(carpeta_salida, nombre_salida)
            
            exito = quemar_subtitulos(ruta_video, ruta_ass, ruta_salida)
            
            if exito:
                print(f"\n¡Éxito! Video con subtítulos guardado en: {ruta_salida}")
                # Limpiar archivo temporal
                if os.path.exists(ruta_ass):
                    os.remove(ruta_ass)
            else:
                print("\nHubo un problema al generar el video final.")
                
        else:
            print("Número inválido.")
    except ValueError:
        print("Por favor, ingresa un número válido.")
