import os
import yt_dlp

def descargar_video(url, carpeta_destino="videos_originales"):
    """
    Descarga un video de YouTube en la mejor calidad disponible (video + audio).
    """
    # Crear la carpeta si no existe
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"Carpeta '{carpeta_destino}' creada.")

    # Configuración de yt-dlp
    ydl_opts = {
        # Al no especificar 'format', yt-dlp descargará automáticamente la mejor calidad 
        # de video y audio y los unirá usando FFmpeg (que ya tienes instalado).
        'outtmpl': os.path.join(carpeta_destino, '%(title)s.%(ext)s'), # Nombre del archivo
        'noplaylist': True, # Descargar solo el video, no la lista de reproducción
        'nocheckcertificate': True, # Ignorar errores de certificado SSL
    }

    print(f"Iniciando descarga de: {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("¡Descarga completada con éxito!")
    except Exception as e:
        print(f"Ocurrió un error durante la descarga: {e}")

if __name__ == "__main__":
    print("=== Descargador de Videos para Clips ===")
    url_video = input("Pega el enlace del video de YouTube: ")
    
    if url_video.strip():
        descargar_video(url_video)
    else:
        print("No ingresaste un enlace válido.")
