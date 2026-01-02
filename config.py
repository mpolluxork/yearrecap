"""
Configuration settings for Year in 365 Seconds video generator
"""
import os

# Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(PROJECT_ROOT, "Recap 2025")
OUTPUT_FOLDER = PROJECT_ROOT
OUTPUT_VIDEO_FOLDER = os.path.join(PROJECT_ROOT, "output")  # Separate folder for final videos
PROCESSED_FOLDER = os.path.join(PROJECT_ROOT, "processed")
TEMP_FOLDER = os.path.join(PROJECT_ROOT, "temp")

# Output files
MEDIA_ASSIGNMENT_JSON = os.path.join(OUTPUT_FOLDER, "media_assignment.json")
REPORT_VISUAL_TXT = os.path.join(OUTPUT_FOLDER, "report_visual.txt")
REPORT_DETAILED_CSV = os.path.join(OUTPUT_FOLDER, "report_detailed.csv")
FINAL_VIDEO = os.path.join(OUTPUT_VIDEO_FOLDER, "2025_recap.mp4")
CHECKPOINT_FILE = os.path.join(OUTPUT_FOLDER, "checkpoint.json")  # For resume functionality


# Supported formats
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.heic', '.gif'}
SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi', '.mkv'}
ALL_SUPPORTED_FORMATS = SUPPORTED_IMAGE_FORMATS | SUPPORTED_VIDEO_FORMATS

# Year configuration
TARGET_YEAR = 2025

# Video encoding settings
VIDEO_SETTINGS = {
    'resolution': (1920, 1080),  # 16:9 aspect ratio
    'fps': 30,
    'video_codec': 'libx264',
    'audio_codec': 'aac',
    'crf': 23,  # Quality (lower = better quality, larger file)
    'preset': 'medium',  # Encoding speed vs compression
    'pixel_format': 'yuv420p'
}

# Content duration settings (in seconds)
PHOTO_DURATION = 0.8
VIDEO_DURATION = 1.25
GIF_MAX_DURATION = 1.25
MONTH_SEPARATOR_DURATION = 1.0
FADE_DURATION = 0.3

# Ken Burns effect settings
KEN_BURNS = {
    'enabled': True,
    'zoom_range': (1.0, 1.10),  # Very subtle zoom: 1.0 to 1.10 (más lento)
    'duration': PHOTO_DURATION,
    'easing': 'ease_in_out'
}


# Month separator styling
MONTH_SEPARATOR = {
    'background_color': (0, 0, 0),  # Black
    'text_color': (255, 255, 255),  # White
    'font_size': 80,
    'font_family': 'Arial',
    'show_month_name': True,
    'show_year': True
}

# Month names (in Spanish)
MONTH_NAMES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Date caption settings (overlay date on each clip)
DATE_CAPTION = {
    'enabled': True,  # Show date overlay
    'font_size': 24,
    'font_color': 'white@0.7',  # White with 70% opacity (30% transparent)
    'position': 'bottom_right',  # Options: 'top_left', 'top_right', 'bottom_left', 'bottom_right'
    'margin': 20  # Pixels from edge
}

# Logging
LOG_LEVEL = "INFO"
