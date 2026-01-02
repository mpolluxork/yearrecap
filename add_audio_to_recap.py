#!/usr/bin/env python3
"""
Add Audio to Recap Video
========================
Lee los videos mensuales, mide su duración, extrae fragmentos de cada MP3
correspondiente, los une con crossfade y los pega al video final.
"""

import os
import subprocess
import json
from pathlib import Path
import config

# Configuración
OUTPUT_FOLDER = "output"
AUDIO_FOLDER = "audio"
CROSSFADE_DURATION = config.MONTH_SEPARATOR_DURATION  # Segundos de crossfade entre canciones

# Mapeo de meses a patrones de archivos de audio (en orden de las URLs)
# Usamos patrones parciales para evitar problemas con caracteres especiales
MONTH_AUDIO_PATTERNS = {
    1: "01",
    2: "02",
    3: "03",
    4: "04", 
    5: "05",
    6: "06",
    7: "07",
    8: "08",
    9: "09",
    10: "10",
    11: "11",
    12: "12",
}


def find_audio_file(pattern: str, folder: str) -> str:
    """Buscar archivo de audio que contenga el patrón"""
    import glob
    for f in os.listdir(folder):
        if pattern.lower() in f.lower() and f.endswith('.mp3'):
            return os.path.join(folder, f)
    return None


def get_duration(filepath: str) -> float:
    """Obtener duración de un archivo multimedia en segundos"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "json",
        filepath
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])


def extract_audio_segment(input_audio: str, output_audio: str, duration: float, 
                          crossfade_compensation: float = 0):
    """
    Extraer un segmento de audio de la duración especificada desde un punto aleatorio.
    
    Args:
        input_audio: Archivo de audio fuente
        output_audio: Archivo de salida
        duration: Duración deseada del segmento
        crossfade_compensation: Segundos extra para compensar el crossfade
    """
    import random
    
    # Obtener duración total del audio
    audio_duration = get_duration(input_audio)
    
    # Duración real a extraer (compensando crossfade)
    extract_duration = duration + crossfade_compensation
    
    # Calcular punto de inicio aleatorio
    # El inicio máximo es: duración_audio - duración_a_extraer
    # Esto garantiza que siempre haya suficiente audio después del punto de inicio
    if audio_duration >= extract_duration:
        max_start = audio_duration - extract_duration
        start_time = random.uniform(0, max_start)
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),  # Punto de inicio aleatorio
            "-i", input_audio,
            "-t", str(extract_duration),
            "-c:a", "libmp3lame",
            "-q:a", "2",
            output_audio
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"  ✓ Extraído: {extract_duration:.1f}s (desde {start_time:.1f}s)")
    else:
        # Audio más corto que lo necesario - hacer loop
        print(f"  ⚠️ Audio ({audio_duration:.1f}s) más corto que requerido ({extract_duration:.1f}s), haciendo loop...")
        
        # Usar filtro aloop para repetir el audio las veces necesarias
        loops_needed = int(extract_duration / audio_duration) + 1
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_audio,
            "-af", f"aloop=loop={loops_needed}:size={int(audio_duration * 48000)},atrim=0:{extract_duration}",
            "-c:a", "libmp3lame",
            "-q:a", "2",
            output_audio
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"  ✓ Extraído con loop: {extract_duration:.1f}s")


def concatenate_with_crossfade(audio_files: list, output_file: str, crossfade: float):
    """Concatenar audios con crossfade usando ffmpeg"""
    if len(audio_files) == 0:
        return
    
    if len(audio_files) == 1:
        # Solo un archivo, copiar directamente
        subprocess.run(["cp", audio_files[0], output_file], check=True)
        return
    
    # Construir filtro complejo para crossfade
    # [0][1]acrossfade=d=X[a01]; [a01][2]acrossfade=d=X[a012]; ...
    
    inputs = []
    for f in audio_files:
        inputs.extend(["-i", f])
    
    # Construir el filtro
    filter_parts = []
    current_label = "[0]"
    
    for i in range(1, len(audio_files)):
        next_input = f"[{i}]"
        output_label = f"[a{i}]" if i < len(audio_files) - 1 else ""
        
        filter_parts.append(
            f"{current_label}{next_input}acrossfade=d={crossfade}:c1=tri:c2=tri{output_label}"
        )
        current_label = f"[a{i}]"
    
    filter_complex = ";".join(filter_parts)
    
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-c:a", "libmp3lame",
        "-q:a", "2",
        output_file
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)


def merge_audio_video(video_path: str, audio_path: str, output_path: str):
    """Combinar video con audio"""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",  # No re-encodear video
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",  # Video del primer input
        "-map", "1:a:0",  # Audio del segundo input
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def main():
    print("=" * 60)
    print("🎵 AGREGANDO AUDIO AL VIDEO RECAP")
    print("=" * 60)
    
    # Crear carpeta temporal
    temp_folder = Path("temp_audio")
    temp_folder.mkdir(exist_ok=True)
    
    # Paso 1: Obtener duración de cada video mensual
    print("\n📊 Analizando duración de videos mensuales...")
    month_durations = {}
    
    for month in range(1, 13):
        month_names = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        video_path = os.path.join(OUTPUT_FOLDER, f"month_{month:02d}_{month_names[month-1]}.mp4")
        
        if os.path.exists(video_path):
            duration = get_duration(video_path)
            month_durations[month] = duration
            print(f"  {month_names[month-1]}: {duration:.1f}s")
        else:
            print(f"  ⚠️ No encontrado: {video_path}")
    
    # Paso 2: Extraer segmentos de audio para cada mes
    print("\n🎵 Extrayendo segmentos de audio...")
    audio_segments = []
    
    for month in range(1, 13):
        if month not in month_durations:
            continue
            
        duration = month_durations[month]
        pattern = MONTH_AUDIO_PATTERNS.get(month)
        
        if not pattern:
            print(f"  ⚠️ Sin audio para mes {month}")
            continue
        
        audio_path = find_audio_file(pattern, AUDIO_FOLDER)
        if not audio_path:
            print(f"  ⚠️ No encontrado audio con patrón: {pattern}")
            continue
        
        month_names = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        print(f"  {month_names[month-1]}:", end=" ")
        
        # Extraer segmento (con compensación de crossfade excepto el último)
        segment_path = str(temp_folder / f"segment_{month:02d}.mp3")
        # Todos los segmentos excepto el último necesitan compensación por crossfade
        is_last = (month == 12)
        compensation = 0 if is_last else CROSSFADE_DURATION
        extract_audio_segment(audio_path, segment_path, duration, compensation)
        audio_segments.append(segment_path)
    
    # Paso 3: Concatenar con crossfade
    print(f"\n🔀 Concatenando {len(audio_segments)} segmentos con crossfade de {CROSSFADE_DURATION}s...")
    combined_audio_raw = str(temp_folder / "combined_audio_raw.mp3")
    concatenate_with_crossfade(audio_segments, combined_audio_raw, CROSSFADE_DURATION)
    print("  ✓ Audio combinado creado")
    
    # Paso 3.5: Agregar fade in/out global
    print("\n🎚️ Aplicando fade in/out global...")
    combined_audio = str(temp_folder / "combined_audio.mp3")
    audio_total_duration = get_duration(combined_audio_raw)
    fade_global = 2.0  # 2 segundos de fade in al inicio y fade out al final
    
    fade_cmd = [
        "ffmpeg", "-y",
        "-i", combined_audio_raw,
        "-af", f"afade=t=in:st=0:d={fade_global},afade=t=out:st={audio_total_duration - fade_global}:d={fade_global}",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        combined_audio
    ]
    subprocess.run(fade_cmd, capture_output=True, check=True)
    print(f"  ✓ Fade in/out aplicado ({fade_global}s)")
    
    # Paso 4: Combinar con el video final
    print("\n🎬 Combinando audio con video...")
    input_video = os.path.join(OUTPUT_FOLDER, "2025_recap.mp4")
    output_video = os.path.join(OUTPUT_FOLDER, "2025_recap_with_audio.mp4")
    
    if not os.path.exists(input_video):
        print(f"  ❌ No se encontró el video: {input_video}")
        return
    
    merge_audio_video(input_video, combined_audio, output_video)
    
    # Limpiar temporales
    print("\n🧹 Limpiando archivos temporales...")
    import shutil
    shutil.rmtree(temp_folder)
    
    # Resultado final
    final_duration = get_duration(output_video)
    file_size = os.path.getsize(output_video) / (1024 * 1024)
    
    print("\n" + "=" * 60)
    print("✨ ¡VIDEO CON AUDIO CREADO!")
    print("=" * 60)
    print(f"📁 Archivo: {output_video}")
    print(f"⏱️  Duración: {final_duration/60:.1f} minutos")
    print(f"💾 Tamaño: {file_size:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
