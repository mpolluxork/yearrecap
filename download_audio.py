#!/usr/bin/env python3
"""
YouTube Audio Downloader
Lee URLs de un archivo de texto y descarga el audio en MP3
"""

import os
import subprocess
import sys
from pathlib import Path

# Configuración
URLS_FILE = "urls.txt"  # Archivo con URLs (una por línea)
OUTPUT_FOLDER = "audio"  # Carpeta de salida


def check_ytdlp():
    """Verificar si yt-dlp está instalado"""
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def download_audio(url: str, output_folder: str, index: int) -> bool:
    """
    Descargar audio de una URL de YouTube
    
    Args:
        url: URL de YouTube
        output_folder: Carpeta de destino
        index: Número de orden (1, 2, 3...) para nombrar el archivo
        
    Returns:
        True si se descargó correctamente
    """
    try:
        # Nombre del archivo basado en el índice: 01.mp3, 02.mp3, etc.
        output_filename = f"{index:02d}.mp3"
        output_path = os.path.join(output_folder, output_filename)
        
        cmd = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", "mp3",
            "--audio-quality", "0",  # Best quality
            "-o", f"{output_folder}/{index:02d}.%(ext)s",  # Nombre numérico
            "--no-playlist",  # Solo el video, no toda la playlist
            "--ignore-errors",
            url.strip()
        ]
        
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode == 0
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    # Verificar yt-dlp
    if not check_ytdlp():
        print("❌ yt-dlp no está instalado.")
        print("   Instálalo con: pip install yt-dlp")
        print("   O en Linux:    sudo apt install yt-dlp")
        sys.exit(1)
    
    # Verificar archivo de URLs
    if not os.path.exists(URLS_FILE):
        print(f"❌ No se encontró el archivo: {URLS_FILE}")
        print(f"   Crea un archivo '{URLS_FILE}' con una URL por línea")
        
        # Crear archivo de ejemplo
        with open(URLS_FILE, 'w') as f:
            f.write("# URLs de YouTube (una por línea)\n")
            f.write("# Ejemplo:\n")
            f.write("# https://www.youtube.com/watch?v=dQw4w9WgXcQ\n")
        
        print(f"   Se creó un archivo de ejemplo: {URLS_FILE}")
        sys.exit(1)
    
    # Crear carpeta de salida
    Path(OUTPUT_FOLDER).mkdir(exist_ok=True)
    
    # Leer URLs
    with open(URLS_FILE, 'r') as f:
        urls = [line.strip() for line in f 
                if line.strip() and not line.startswith('#')]
    
    if not urls:
        print(f"❌ No hay URLs válidas en {URLS_FILE}")
        sys.exit(1)
    
    print(f"🎵 Descargando {len(urls)} audios a '{OUTPUT_FOLDER}/'")
    print("=" * 50)
    
    success = 0
    failed = 0
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Descargando como {i:02d}.mp3...")
        print(f"  URL: {url[:60]}...")
        
        if download_audio(url, OUTPUT_FOLDER, i):
            print(f"  ✅ Guardado como {i:02d}.mp3")
            success += 1
        else:
            print(f"  ❌ Falló")
            failed += 1
    
    # Resumen
    print("\n" + "=" * 50)
    print(f"✅ Descargados: {success}")
    if failed:
        print(f"❌ Fallidos: {failed}")
    print(f"📁 Archivos en: {OUTPUT_FOLDER}/")


if __name__ == "__main__":
    main()
