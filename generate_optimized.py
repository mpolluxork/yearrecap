"""
Optimized video generation with caching and incremental processing
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
from pathlib import Path

from config import MEDIA_ASSIGNMENT_JSON, PROCESSED_FOLDER, OUTPUT_VIDEO_FOLDER, CHECKPOINT_FILE
from utils import setup_logging
from checkpoint import CheckpointManager


def get_processed_clips() -> Dict[str, str]:
    """
    Get list of already processed clips
    Returns dict mapping source filename to processed clip path
    """
    processed = {}
    
    if not os.path.exists(PROCESSED_FOLDER):
        return processed
    
    for filename in os.listdir(PROCESSED_FOLDER):
        if filename.endswith('.mp4') and not filename.startswith('separator_'):
            # Extract original filename from processed name (format: XXXX_originalname.mp4)
            if '_' in filename:
                original_part = '_'.join(filename.split('_')[1:])
                original_name = original_part.replace('.mp4', '')
                processed[original_name] = os.path.join(PROCESSED_FOLDER, filename)
    
    return processed


def should_process_clip(media_info: Dict, processed_clips: Dict[str, str]) -> bool:
    """
    Check if a clip needs to be processed
    
    Args:
        media_info: Media information
        processed_clips: Dict of already processed clips
        
    Returns:
        True if needs processing, False if can skip
    """
    filename_base = os.path.splitext(media_info['filename'])[0]
    
    # Check if already processed
    if filename_base in processed_clips:
        processed_path = processed_clips[filename_base]
        
        # Verify file still exists
        if os.path.exists(processed_path):
            return False  # Skip, already processed
    
    return True  # Needs processing


def generate_month_video(month: int, assignments: Dict, generator, output_path: str, all_assignments: Dict) -> str:
    """
    Generate video for a single month
    
    Args:
        month: Month number (1-12)
        assignments: Month-specific media assignments
        generator: VideoGenerator instance
        output_path: Where to save month video
        all_assignments: Full year assignments (for context)
        
    Returns:
        Path to generated month video
    """
    from config import MONTH_NAMES
    
    logging.info(f"\n{'='*60}")
    logging.info(f"📅 Procesando {MONTH_NAMES[month-1]} (Mes {month}/12)")
    logging.info(f"{'='*60}")

    
    # Filter assignments for this month
    month_dates = [d for d in sorted(assignments.keys()) 
                   if d.startswith(f"2025-{month:02d}")]
    
    if not month_dates:
        logging.info(f"No media for {MONTH_NAMES[month-1]}, skipping...")
        return None
    
    logging.info(f"Found {len(month_dates)} days with media")
    
    # Month separator
    separator_path = os.path.join(PROCESSED_FOLDER, f"separator_{month:02d}.mp4")
    if not os.path.exists(separator_path):
        generator.create_month_separator(month, separator_path)
    month_clips = [separator_path]
    month_clip_dates = [None]
    
    # Get already processed clips (search by filename, not index)
    processed_clips_cache = get_processed_clips()
    
    # Process media for this month
    clip_index = (month - 1) * 1000
    
    for date_str in month_dates:
        media_list = assignments[date_str]
        
        for media_info in media_list:
            filename_base = os.path.splitext(media_info['filename'])[0]
            
            # Check if already processed (search by filename, ignore index)
            if filename_base in processed_clips_cache:
                # Reuse existing processed clip regardless of its original index
                processed_clip = processed_clips_cache[filename_base]
                logging.info(f"Using cached: {media_info['filename']} -> {os.path.basename(processed_clip)}")
            else:
                # Need to process this file
                logging.info(f"Processing: {media_info['filename']}")
                processed_clip = generator.process_media_file(media_info, clip_index)
            
            if processed_clip:
                month_clips.append(processed_clip)
                month_clip_dates.append(date_str)
                clip_index += 1
    
    # Videos need normalization, images are already pre-normalized
    # Add captions to all clips - IMPORTANT: Copy to temp first to avoid modifying cached clips!
    logging.info(f"\nPreparing {len(month_clips)-1} clips for {MONTH_NAMES[month-1]}...")
    
    from config import TEMP_FOLDER
    import shutil
    month_temp_folder = os.path.join(TEMP_FOLDER, f"month_{month:02d}")
    os.makedirs(month_temp_folder, exist_ok=True)
    
    # Create working copies with captions
    final_clips_for_month = [month_clips[0]]  # Keep separator as-is
    
    for i in range(1, len(month_clips)):
        clip = month_clips[i]
        date_str = month_clip_dates[i]
        
        if not date_str:
            final_clips_for_month.append(clip)
            continue
        
        # Find original media type to know if normalization is needed
        media_info = None
        for m in assignments[date_str]:
            if os.path.basename(clip).endswith(f"_{os.path.splitext(m['filename'])[0]}.mp4"):
                media_info = m
                break
        
        # Copy to temp folder to avoid modifying cached processed clips
        temp_clip_name = f"{i:04d}_{os.path.basename(clip)}"
        temp_clip_path = os.path.join(month_temp_folder, temp_clip_name)
        shutil.copy2(clip, temp_clip_path)
        
        # Only normalize videos/GIFs (images are pre-normalized)
        if media_info and media_info['type'] in ['video', 'gif']:
            logging.debug(f"Normalizing: {os.path.basename(clip)}")
            generator.normalize_clip(temp_clip_path)
        
        # Add caption with CURRENT date (not cached date)
        generator.add_date_caption(temp_clip_path, date_str)
        
        final_clips_for_month.append(temp_clip_path)
    
    # Compile month video
    logging.info(f"Compiling {MONTH_NAMES[month-1]} video ({len(final_clips_for_month)-1} clips)...")
    generator.compile_final_video(final_clips_for_month, output_path)
    
    return output_path


def generate_optimized(checkpoint_manager: CheckpointManager = None):
    """Generate video with all optimizations and checkpoint support"""
    setup_logging("INFO")
    from generate_video import VideoGenerator
    from config import MONTH_NAMES, FINAL_VIDEO
    
    # Initialize checkpoint manager if not provided
    if checkpoint_manager is None:
        checkpoint_manager = CheckpointManager(CHECKPOINT_FILE)
    
    # Ensure output folder exists
    os.makedirs(OUTPUT_VIDEO_FOLDER, exist_ok=True)
    
    generator = VideoGenerator()
    
    # Load assignments
    assignments = generator.load_assignments()
    
    # Generate video for each month
    month_videos = []
    completed_months = checkpoint_manager.get_completed_months()
    
    for month in range(1, 13):
        month_output = os.path.join(OUTPUT_VIDEO_FOLDER, f"month_{month:02d}_{MONTH_NAMES[month-1]}.mp4")
        
        # Skip if already processed and file exists
        if checkpoint_manager.is_month_complete(month) and os.path.exists(month_output):
            logging.info(f"\n{'='*60}")
            logging.info(f"Skipping {MONTH_NAMES[month-1]} (already processed)")
            logging.info(f"{'='*60}")
            month_videos.append(month_output)
            continue
        
        month_video = generate_month_video(month, assignments, generator, month_output, assignments)
        
        if month_video:
            month_videos.append(month_video)
            checkpoint_manager.mark_month_complete(month)
    
    # Concatenate all month videos
    logging.info(f"\n{'='*60}")
    logging.info("🎬 CONCATENANDO VIDEOS MENSUALES EN VIDEO FINAL")
    logging.info(f"{'='*60}")
    logging.info(f"📊 Total de videos a unir: {len(month_videos)}")
    logging.info(f"🎯 Destino: {FINAL_VIDEO}")
    logging.info("")
    logging.info("⏳ Esto puede tomar varios minutos dependiendo del tamaño...")
    logging.info("   Por favor espera mientras FFmpeg une todos los videos...")
    
    generator.compile_final_video(month_videos, FINAL_VIDEO)
    
    logging.info(f"\n✅ Final video: {FINAL_VIDEO}")
    
    return FINAL_VIDEO


if __name__ == "__main__":
    generate_optimized()
