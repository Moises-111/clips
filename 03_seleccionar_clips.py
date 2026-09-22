import os
import json
import subprocess

def convertir_tiempo_a_segundos(tiempo_str):
    """
    Convierte un string de tiempo en formato MM.SS o segundos a segundos totales (float).
    Ejemplos:
    '1.45' -> 1 minuto y 45 segundos -> 105.0 segundos
    '0.4'  -> 0 minutos y 4 segundos -> 4.0 segundos
    '45'   -> 45 segundos -> 45.0 segundos
    """
    try:
        # Si el usuario ingresa un número con punto (ej. 1.45)
        if '.' in tiempo_str:
            partes = tiempo_str.split('.')
            minutos = int(partes[0])
            # Si ingresa '0.4', lo tratamos como 4 segundos, no 40.
            # Si ingresa '1.45', son 45 segundos.
            segundos = int(partes[1])
            return float(minutos * 60 + segundos)
        else:
            # Si ingresa solo un número entero (ej. 45)
            return float(tiempo_str)
    except ValueError:
        raise ValueError("Formato de tiempo inválido.")

def extraer_clip(ruta_video, tiempo_inicio, tiempo_fin, nombre_salida, carpeta_destino="clips_recortados"):
    """
    Recorta un fragmento de video usando FFmpeg directamente para asegurar que el audio se mantenga
    y para que el proceso sea casi instantáneo.
    """
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"Carpeta '{carpeta_destino}' creada.")

    ruta_salida = os.path.join(carpeta_destino, nombre_salida)
    duracion = tiempo_fin - tiempo_inicio
    
    print(f"Extrayendo clip desde {tiempo_inicio}s hasta {tiempo_fin}s usando FFmpeg...")
    try:
        # Comando FFmpeg para recortar copiando el video (rápido) pero convirtiendo el audio a AAC
        # Esto soluciona el problema de los archivos .webm que usan audio Opus incompatible con MP4
        comando = [
            "ffmpeg",
            "-y", # Sobrescribir si existe
            "-ss", str(tiempo_inicio), # Tiempo de inicio
            "-i", ruta_video, # Archivo de entrada
            "-t", str(duracion), # Duración del clip
            "-c:v", "copy", # Copiar el video sin re-renderizar (súper rápido)
            "-c:a", "aac", # Convertir el audio a AAC (formato universal para MP4)
            "-b:a", "192k", # Calidad de audio alta
            ruta_salida
        ]
        
        # Ejecutar el comando de forma silenciosa
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"¡Clip guardado exitosamente en: {ruta_salida}!")
        return True
    except subprocess.CalledProcessError:
        print("Error: FFmpeg falló al intentar copiar los streams. Intentando re-codificar...")
        try:
            # Plan B: Si la copia directa falla (a veces pasa con webm a mp4), re-codificamos rápido
            comando_recode = [
                "ffmpeg",
                "-y",
                "-ss", str(tiempo_inicio),
                "-i", ruta_video,
                "-t", str(duracion),
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-c:a", "aac",
                ruta_salida
            ]
            subprocess.run(comando_recode, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"¡Clip guardado exitosamente (re-codificado) en: {ruta_salida}!")
            return True
        except Exception as e:
            print(f"Error crítico al extraer el clip: {e}")
            return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

def mostrar_segmentos_transcripcion(ruta_json):
    """
    Lee el archivo JSON de Whisper y muestra los segmentos de texto con sus tiempos.
    """
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            
        print("\n--- Segmentos de la transcripción ---")
        for i, segmento in enumerate(datos['segments']):
            inicio = round(segmento['start'], 2)
            fin = round(segmento['end'], 2)
            texto = segmento['text'].strip()
            print(f"[{i}] {inicio}s - {fin}s: {texto}")
        print("-------------------------------------\n")
        return datos['segments']
    except Exception as e:
        print(f"Error al leer la transcripción: {e}")
        return None

if __name__ == "__main__":
    print("=== Selector y Recortador de Clips ===")
    carpeta_videos = "videos_originales"
    carpeta_transcripciones = "transcripciones"
    
    if not os.path.exists(carpeta_videos) or not os.listdir(carpeta_videos):
        print(f"No hay videos en '{carpeta_videos}'.")
        exit()
        
    # Listar videos disponibles
    print("Videos disponibles:")
    videos = [f for f in os.listdir(carpeta_videos) if f.endswith(('.mp4', '.mkv', '.webm'))]
    for i, video in enumerate(videos):
        print(f"{i + 1}. {video}")
        
    seleccion_video = input("\nIngresa el número del video del que quieres extraer clips: ")
    
    try:
        indice_video = int(seleccion_video) - 1
        if 0 <= indice_video < len(videos):
            nombre_video = videos[indice_video]
            ruta_video = os.path.join(carpeta_videos, nombre_video)
            nombre_base = os.path.splitext(nombre_video)[0]
            ruta_json = os.path.join(carpeta_transcripciones, f"{nombre_base}.json")
            
            # Verificar si existe la transcripción
            if os.path.exists(ruta_json):
                print("\n¡Transcripción encontrada! Mostrando segmentos para ayudarte a elegir:")
                mostrar_segmentos_transcripcion(ruta_json)
            else:
                print("\n[Aviso] No se encontró transcripción para este video.")
                print("Modo manual activado (ideal para gameplays o videos sin voz).")
                
            print("\nPuedes crear un clip ingresando el tiempo en formato MINUTOS.SEGUNDOS (ej. 1.45) o solo segundos (ej. 105).")
            print("Ejemplo: Para 1 minuto y 45 segundos, ingresa '1.45'. Para 4 segundos, ingresa '0.4'.")
            
            while True:
                    try:
                        entrada_inicio = input("\nTiempo de INICIO (ej. 1.45, o '0' para salir): ")
                        if entrada_inicio == '0':
                            break
                            
                        t_inicio = convertir_tiempo_a_segundos(entrada_inicio)
                        
                        entrada_fin = input("Tiempo de FIN (ej. 2.15): ")
                        t_fin = convertir_tiempo_a_segundos(entrada_fin)
                        
                        if t_fin <= t_inicio:
                            print("El tiempo de fin debe ser mayor al tiempo de inicio.")
                            continue
                            
                        nombre_clip = input("Nombre para este clip (ej. clip1.mp4): ")
                        if not nombre_clip.endswith('.mp4'):
                            nombre_clip += '.mp4'
                            
                        extraer_clip(ruta_video, t_inicio, t_fin, nombre_clip)
                        
                        continuar = input("¿Quieres extraer otro clip de este video? (s/n): ")
                        if continuar.lower() != 's':
                            break
                            
                    except ValueError:
                        print("Por favor, ingresa números válidos para los tiempos.")
        else:
            print("Número de video inválido.")
    except ValueError:
        print("Por favor, ingresa un número válido.")
