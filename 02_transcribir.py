import os
import whisper
import json
import warnings

# Suprimir advertencias de FP16 si se usa CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

def transcribir_video(ruta_video, carpeta_destino="transcripciones", modelo_tamano="base"):
    """
    Transcribe el audio de un video usando Whisper y guarda el resultado con marcas de tiempo.
    """
    if not os.path.exists(ruta_video):
        print(f"Error: No se encontró el archivo {ruta_video}")
        return

    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"Carpeta '{carpeta_destino}' creada.")

    print(f"Cargando el modelo Whisper '{modelo_tamano}' (esto puede tardar la primera vez)...")
    # Modelos disponibles: tiny, base, small, medium, large
    modelo = whisper.load_model(modelo_tamano)

    print(f"Iniciando transcripción de: {ruta_video}")
    print("Por favor, espera. Esto puede tomar varios minutos dependiendo de la duración del video y tu computadora.")
    
    try:
        # Transcribir el audio
        resultado = modelo.transcribe(ruta_video, verbose=False)
        
        # Preparar el nombre del archivo de salida
        nombre_base = os.path.splitext(os.path.basename(ruta_video))[0]
        ruta_salida = os.path.join(carpeta_destino, f"{nombre_base}.json")

        # Guardar el resultado completo (incluyendo segmentos con tiempos) en un JSON
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=4)

        print(f"¡Transcripción completada! Guardada en: {ruta_salida}")
        
        # Mostrar un pequeño resumen
        print("\n--- Resumen de la transcripción ---")
        print(f"Texto detectado (primeros 200 caracteres): {resultado['text'][:200]}...")
        print(f"Idioma detectado: {resultado.get('language', 'Desconocido')}")
        print("-----------------------------------\n")

    except Exception as e:
        print(f"Ocurrió un error durante la transcripción: {e}")

if __name__ == "__main__":
    print("=== Transcriptor de Videos con IA (Whisper) ===")
    carpeta_videos = "videos_originales"
    
    if not os.path.exists(carpeta_videos) or not os.listdir(carpeta_videos):
        print(f"No hay videos en la carpeta '{carpeta_videos}'. Ejecuta 01_descargar.py primero.")
    else:
        print("Videos disponibles:")
        videos = [f for f in os.listdir(carpeta_videos) if f.endswith(('.mp4', '.mkv', '.webm'))]
        
        for i, video in enumerate(videos):
            print(f"{i + 1}. {video}")
            
        seleccion = input("\nIngresa el número del video que deseas transcribir: ")
        
        try:
            indice = int(seleccion) - 1
            if 0 <= indice < len(videos):
                ruta_completa = os.path.join(carpeta_videos, videos[indice])
                # Usamos el modelo 'base' por defecto, es un buen equilibrio entre velocidad y precisión
                transcribir_video(ruta_completa, modelo_tamano="base")
            else:
                print("Número inválido.")
        except ValueError:
            print("Por favor, ingresa un número válido.")
