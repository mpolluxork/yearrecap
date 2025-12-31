#!/usr/bin/env python3
"""
Regenera un mes específico y vuelve a concatenar el video final.
ESCANEA ARCHIVOS NUEVOS para el mes antes de regenerar.

Uso: python regenerate_month.py 7        # Regenera Julio
     python regenerate_month.py 7 10 11  # Regenera Julio, Octubre y Noviembre
"""
import sys
import os
import json
import argparse

from config import (
    CHECKPOINT_FILE, OUTPUT_VIDEO_FOLDER, MONTH_NAMES, 
    INPUT_FOLDER, MEDIA_ASSIGNMENT_JSON, TARGET_YEAR
)
from checkpoint import CheckpointManager
from generate_optimized import generate_optimized
from assign_media import scan_media_folder, assign_media_to_days
from utils import setup_logging, get_media_date


def rescan_month_files(months_to_scan: list) -> dict:
    """
    Re-escanea archivos de la carpeta de entrada para los meses especificados
    y actualiza el media_assignment.json
    
    Args:
        months_to_scan: Lista de números de mes (1-12)
        
    Returns:
        Dict con los archivos nuevos encontrados por mes
    """
    print(f"📂 Escaneando archivos para los meses: {[MONTH_NAMES[m-1] for m in months_to_scan]}")
    
    # Cargar asignaciones existentes
    existing_assignments = {}
    if os.path.exists(MEDIA_ASSIGNMENT_JSON):
        with open(MEDIA_ASSIGNMENT_JSON, 'r', encoding='utf-8') as f:
            existing_assignments = json.load(f)
    
    # Obtener archivos existentes por filepath para evitar duplicados
    existing_files = set()
    for date_key, media_list in existing_assignments.items():
        for media_info in media_list:
            existing_files.add(media_info['filepath'])
    
    # Escanear carpeta de entrada
    all_files = scan_media_folder(INPUT_FOLDER)
    
    # Filtrar solo los archivos nuevos
    new_files = [f for f in all_files if f not in existing_files]
    
    if not new_files:
        print("   ✓ No hay archivos nuevos")
        return {}
    
    print(f"   🆕 Encontrados {len(new_files)} archivos nuevos")
    
    # Asignar los archivos nuevos a días
    new_assignments = assign_media_to_days(new_files)
    
    # Filtrar solo los que corresponden a los meses que queremos
    new_for_months = {}
    for date_key, media_list in new_assignments.items():
        month = int(date_key.split('-')[1])
        if month in months_to_scan:
            new_for_months[date_key] = media_list
            print(f"   📅 {date_key}: {len(media_list)} archivo(s) nuevo(s)")
    
    if not new_for_months:
        print(f"   ✓ No hay archivos nuevos para los meses seleccionados")
        return {}
    
    # Mergear con asignaciones existentes
    for date_key, media_list in new_for_months.items():
        if date_key in existing_assignments:
            # Agregar a la lista existente
            existing_assignments[date_key].extend(media_list)
            # Re-ordenar por fecha/hora
            existing_assignments[date_key].sort(key=lambda x: x['date'])
        else:
            existing_assignments[date_key] = media_list
    
    # Guardar asignaciones actualizadas
    with open(MEDIA_ASSIGNMENT_JSON, 'w', encoding='utf-8') as f:
        json.dump(existing_assignments, f, indent=2, ensure_ascii=False)
    
    print(f"   💾 Actualizado: {MEDIA_ASSIGNMENT_JSON}")
    
    return new_for_months


def main():
    setup_logging("INFO")
    
    parser = argparse.ArgumentParser(
        description='Regenerar meses específicos del video recap',
        epilog='Ejemplo: python regenerate_month.py 7 (para Julio)'
    )
    parser.add_argument(
        'months', 
        type=int, 
        nargs='+',
        help='Número(s) de mes a regenerar (1-12). Ej: 7 para Julio, o 7 10 11 para varios.'
    )
    parser.add_argument(
        '--no-scan',
        action='store_true',
        help='No escanear archivos nuevos, solo regenerar con los existentes'
    )
    
    args = parser.parse_args()
    
    # Validar meses
    for month in args.months:
        if month < 1 or month > 12:
            print(f"❌ Error: {month} no es un mes válido (debe ser 1-12)")
            sys.exit(1)
    
    print("=" * 60)
    print("🔄 REGENERADOR DE MESES")
    print("=" * 60)
    
    # Mostrar qué meses se van a regenerar
    month_names = [MONTH_NAMES[m-1] for m in args.months]
    print(f"📅 Meses a regenerar: {', '.join(month_names)}")
    print()
    
    # PASO 1: Escanear archivos nuevos (a menos que --no-scan)
    if not args.no_scan:
        new_files = rescan_month_files(args.months)
        if new_files:
            print(f"\n✓ Se agregaron archivos nuevos al assignment\n")
    
    # Cargar checkpoint
    checkpoint = CheckpointManager(CHECKPOINT_FILE)
    
    # PASO 2: Invalidar los meses seleccionados
    for month in args.months:
        # Borrar el archivo de video del mes si existe
        month_video = os.path.join(OUTPUT_VIDEO_FOLDER, f"month_{month:02d}_{MONTH_NAMES[month-1]}.mp4")
        if os.path.exists(month_video):
            os.remove(month_video)
            print(f"🗑️  Borrado: {os.path.basename(month_video)}")
        
        # Invalidar en checkpoint
        checkpoint.invalidate_month(month)
    
    print()
    print("🎬 Iniciando regeneración...")
    print()
    
    # PASO 3: Ejecutar generación (solo regenerará los meses invalidados)
    generate_optimized(checkpoint)
    
    print()
    print("=" * 60)
    print("✅ ¡Regeneración completa!")
    print("=" * 60)


if __name__ == "__main__":
    main()
