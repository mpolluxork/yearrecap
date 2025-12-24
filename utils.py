"""
Utility functions for media processing and metadata extraction
"""
import os
import logging
from datetime import datetime
from typing import Optional, Tuple
import exifread
from PIL import Image
import subprocess
import json

# Try to import pillow_heif for HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORTED = True
except ImportError:
    HEIF_SUPPORTED = False
    logging.warning("pillow-heif not installed. HEIC files will use fallback method.")


def setup_logging(log_level: str = "INFO"):
    """Configure logging for the application"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def get_image_exif_date(filepath: str) -> Optional[datetime]:
    """
    Extract date taken from image EXIF data
    
    Args:
        filepath: Path to image file
        
    Returns:
        datetime object or None if not found
    """
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, stop_tag='DateTimeOriginal')
            
            # Try different EXIF date tags
            date_tags = [
                'EXIF DateTimeOriginal',
                'EXIF DateTimeDigitized',
                'Image DateTime'
            ]
            
            for tag in date_tags:
                if tag in tags:
                    date_str = str(tags[tag])
                    try:
                        # EXIF format: "YYYY:MM:DD HH:MM:SS"
                        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        continue
    except Exception as e:
        logging.debug(f"Error reading EXIF from {os.path.basename(filepath)}: {e}")
    
    return None


def get_video_metadata_date(filepath: str) -> Optional[datetime]:
    """
    Extract creation date from video metadata using ffprobe
    
    Args:
        filepath: Path to video file
        
    Returns:
        datetime object or None if not found
    """
    try:
        # Use ffprobe to get metadata in JSON format
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_entries', 'format_tags=creation_time',
            filepath
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            creation_time = data.get('format', {}).get('tags', {}).get('creation_time')
            
            if creation_time:
                # Parse ISO 8601 format
                # Handle both with and without microseconds
                for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        return datetime.strptime(creation_time, fmt)
                    except ValueError:
                        continue
    except Exception as e:
        logging.debug(f"Error reading video metadata from {os.path.basename(filepath)}: {e}")
    
    return None


def get_file_modification_date(filepath: str) -> datetime:
    """
    Get file modification date as fallback
    
    Args:
        filepath: Path to file
        
    Returns:
        datetime object
    """
    timestamp = os.path.getmtime(filepath)
    return datetime.fromtimestamp(timestamp)


def extract_date_from_filename(filename: str) -> Optional[datetime]:
    """
    Try to extract date and time from filename patterns like:
    - 20250102_161334.jpg (with time)
    - IMG-20250105-WA0010.jpg
    - IMG_20251212.jpg
    - VID_20250323_181709.mp4 (with time)
    - Screenshot_20250323_181709_AppSheet.jpg (with time)
    - 2025-03-14_photo.jpg
    
    Args:
        filename: Filename to parse
        
    Returns:
        datetime object or None if pattern not found
    """
    import re
    
    # Pattern 1: YYYYMMDD_HHMMSS (date with time) - try this FIRST
    pattern_with_time = r'(\d{8})_(\d{6})'
    match_time = re.search(pattern_with_time, filename)
    
    if match_time:
        date_str, time_str = match_time.groups()
        try:
            # Parse date and time together
            parsed_date = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            if 2000 <= parsed_date.year <= 2030:
                return parsed_date
        except ValueError:
            pass
    
    # Pattern 2: YYYYMMDD anywhere in filename (8 consecutive digits)
    pattern = r'(\d{8})'
    match = re.search(pattern, filename)
    
    if match:
        date_str = match.group(1)
        try:
            # Validate it's a reasonable date
            parsed_date = datetime.strptime(date_str, "%Y%m%d")
            # Basic sanity check: year should be between 2000 and 2030
            if 2000 <= parsed_date.year <= 2030:
                return parsed_date
        except ValueError:
            pass
    
    # Pattern 3: YYYY-MM-DD format
    pattern2 = r'(\d{4})-(\d{2})-(\d{2})'
    match2 = re.search(pattern2, filename)
    
    if match2:
        try:
            year, month, day = match2.groups()
            parsed_date = datetime(int(year), int(month), int(day))
            if 2000 <= parsed_date.year <= 2030:
                return parsed_date
        except (ValueError, TypeError):
            pass
    
    return None



def get_media_date(filepath: str, target_year: Optional[int] = None) -> Tuple[datetime, str]:
    """
    Get the best available date for a media file, trying multiple methods.
    Compares filename date with metadata date and chooses the most reliable one.
    
    Priority logic:
    1. If both filename and metadata have dates in target_year, choose the OLDER one
    2. If only one has a date in target_year, use that one
    3. If filename has date but metadata doesn't, use filename
    4. Otherwise fall back to metadata or file modification time
    
    Args:
        filepath: Path to media file
        target_year: Target year to validate against (optional)
        
    Returns:
        Tuple of (datetime object, source method)
    """
    from config import TARGET_YEAR
    if target_year is None:
        target_year = TARGET_YEAR
    
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()
    
    # Extract dates from different sources
    date_from_filename = extract_date_from_filename(filename)
    date_from_metadata = None
    metadata_source = None
    
    # Try to get metadata date based on file type
    if ext in {'.jpg', '.jpeg', '.png', '.heic'}:
        date_from_metadata = get_image_exif_date(filepath)
        metadata_source = 'exif'
    elif ext in {'.mp4', '.mov', '.avi', '.mkv'}:
        date_from_metadata = get_video_metadata_date(filepath)
        metadata_source = 'video_metadata'
    
    # Decision logic: Compare and select best date
    filename_valid = date_from_filename and date_from_filename.year == target_year
    metadata_valid = date_from_metadata and date_from_metadata.year == target_year
    
    if filename_valid and metadata_valid:
        # Both dates are valid for target year - choose the OLDER one
        # (more likely to be the actual capture date vs download date)
        if date_from_filename <= date_from_metadata:
            return (date_from_filename, 'filename')
        else:
            return (date_from_metadata, metadata_source)
    
    elif filename_valid:
        # Only filename date is valid for target year
        return (date_from_filename, 'filename')
    
    elif metadata_valid:
        # Only metadata date is valid for target year
        return (date_from_metadata, metadata_source)
    
    elif date_from_filename:
        # Filename has a date, but not in target year - still use it
        return (date_from_filename, 'filename')
    
    elif date_from_metadata:
        # Metadata has a date, but not in target year - still use it
        return (date_from_metadata, metadata_source)
    
    # Fallback to file modification date
    mod_date = get_file_modification_date(filepath)
    return (mod_date, 'file_mtime')



def is_image(filepath: str) -> bool:
    """Check if file is an image"""
    from config import SUPPORTED_IMAGE_FORMATS
    ext = os.path.splitext(filepath)[1].lower()
    return ext in SUPPORTED_IMAGE_FORMATS


def is_video(filepath: str) -> bool:
    """Check if file is a video"""
    from config import SUPPORTED_VIDEO_FORMATS
    ext = os.path.splitext(filepath)[1].lower()
    return ext in SUPPORTED_VIDEO_FORMATS


def is_gif(filepath: str) -> bool:
    """Check if file is a GIF"""
    return os.path.splitext(filepath)[1].lower() == '.gif'


def format_duration(seconds: float) -> str:
    """Format duration in MM:SS format"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def ensure_dir_exists(dirpath: str):
    """Create directory if it doesn't exist"""
    os.makedirs(dirpath, exist_ok=True)
