"""
Phase 3: Video Generation Script
Processes media and generates final video with Ken Burns effects
"""
import os
import json
import subprocess
import shutil
import random
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import ffmpeg

from config import (
    INPUT_FOLDER, OUTPUT_FOLDER, PROCESSED_FOLDER, TEMP_FOLDER,
    MEDIA_ASSIGNMENT_JSON, FINAL_VIDEO, TARGET_YEAR,
    VIDEO_SETTINGS, PHOTO_DURATION, VIDEO_DURATION, GIF_MAX_DURATION,
    MONTH_SEPARATOR_DURATION, FADE_DURATION, KEN_BURNS, MONTH_SEPARATOR,
    MONTH_NAMES, LOG_LEVEL
)
from utils import (
    setup_logging, ensure_dir_exists, is_image, is_video, is_gif,
    format_duration
)


class VideoGenerator:
    """Main video generation class"""
    
    def __init__(self):
        self.width, self.height = VIDEO_SETTINGS['resolution']
        self.fps = VIDEO_SETTINGS['fps']
        self.processed_clips = []
        
        # Create necessary folders
        ensure_dir_exists(PROCESSED_FOLDER)
        ensure_dir_exists(TEMP_FOLDER)
    
    def load_assignments(self) -> Dict[str, List[Dict]]:
        """Load media assignments from JSON"""
        if not os.path.exists(MEDIA_ASSIGNMENT_JSON):
            raise FileNotFoundError(
                f"Assignment file not found: {MEDIA_ASSIGNMENT_JSON}\n"
                "Please run assign_media.py first!"
            )
        
        with open(MEDIA_ASSIGNMENT_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def convert_heic_to_jpg(self, heic_path: str) -> str:
        """Convert HEIC to JPG for processing"""
        try:
            from pillow_heif import register_heif_opener
            from PIL import ImageOps
            register_heif_opener()
            
            img = Image.open(heic_path)
            
            # Fix orientation based on EXIF data (prevents rotation issues)
            img = ImageOps.exif_transpose(img)
            
            jpg_path = heic_path.replace('.HEIC', '.jpg').replace('.heic', '.jpg')
            jpg_path = os.path.join(TEMP_FOLDER, os.path.basename(jpg_path))
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.save(jpg_path, 'JPEG', quality=95)
            return jpg_path
        except Exception as e:
            logging.error(f"Error converting HEIC: {e}")
            raise
    
    def create_ken_burns_image(self, input_path: str, output_path: str, 
                               duration: float, zoom_in: bool = True) -> str:
        """
        Apply Ken Burns effect to an image using FFmpeg
        First creates letterboxed image, then applies zoom
        
        Args:
            input_path: Input image path
            output_path: Output video path
            duration: Duration in seconds
            zoom_in: True for zoom in, False for zoom out
            
        Returns:
            Path to output video
        """
        try:
            # Convert HEIC to JPG if needed
            if input_path.lower().endswith('.heic'):
                input_path = self.convert_heic_to_jpg(input_path)
            
            # Load and fix orientation
            from PIL import ImageOps
            img = Image.open(input_path)
            img = ImageOps.exif_transpose(img)
            
            # Convert to RGB if needed
            if img.mode in('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (0, 0, 0))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to fit 16:9 with letterboxing (BLACK BARS, NO STRETCHING)
            img_ratio = img.width / img.height
            target_ratio = self.width / self.height
            
            if img_ratio > target_ratio:
                # Image is wider - fit by width
                new_width = self.width
                new_height = int(self.width / img_ratio)
            else:
                # Image is taller/vertical - fit by height
                new_height = self.height
                new_width = int(self.height * img_ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create black canvas and paste image centered
            canvas = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            x_offset = (self.width - new_width) // 2
            y_offset = (self.height - new_height) // 2
            canvas.paste(img, (x_offset, y_offset))
            
            # Save the letterboxed image
            temp_letterbox_path = output_path.replace('.mp4', '_letterbox.jpg')
            canvas.save(temp_letterbox_path, 'JPEG', quality=95)
            
            # Now apply Ken Burns to the letterboxed image
            zoom_start, zoom_end = KEN_BURNS['zoom_range']
            if not zoom_in:
                zoom_start, zoom_end = zoom_end, zoom_start
            
            frames = int(duration * self.fps)
            zoom_diff = zoom_end - zoom_start
            
            # Use zoompan filter on the already-letterboxed image
            # Note: d=1 means each input frame produces 1 output frame
            # The zoom expression calculates based on output frame number (on)
            zoompan_filter = (
                f"zoompan=z='if(lte(on,1),{zoom_start},{zoom_start}+{zoom_diff}*(on-1)/{frames})':"
                f"d=1:"  # 1 output frame per zoompan iteration
                f"x='(iw-iw/zoom)/2':"
                f"y='(ih-ih/zoom)/2':"
                f"s={self.width}x{self.height}:"
                f"fps={self.fps}"
            )
            
            # Build FFmpeg command with EXACT parameters (pre-normalized)
            cmd = [
                'ffmpeg',
                '-loop', '1',
                '-i', temp_letterbox_path,
                '-vf', zoompan_filter,
                '-t', str(duration),
                '-c:v', VIDEO_SETTINGS['video_codec'],
                '-pix_fmt', VIDEO_SETTINGS['pixel_format'],  # Force yuv420p
                '-r', str(self.fps),  # Force exact 30 fps
                '-crf', str(VIDEO_SETTINGS['crf']),
                '-y',
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Clean up temp letterbox image
            if os.path.exists(temp_letterbox_path):
                os.remove(temp_letterbox_path)
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error creating Ken Burns effect: {e}")
            logging.warning("Falling back to static video without Ken Burns effect")
            # Fallback: create static video
            return self.create_static_image_video(input_path, output_path, duration)
    
    def create_static_image_video(self, input_path: str, output_path: str, 
                                  duration: float) -> str:
        """
        Convert image to video without Ken Burns effect (fallback)
        
        Args:
            input_path: Input image path
            output_path: Output video path
            duration: Duration in seconds
            
        Returns:
            Path to output video
        """
        try:
            from PIL import ImageOps
            
            # Prepare image with padding to fit 16:9
            img = Image.open(input_path)
            
            # Fix orientation based on EXIF data (prevents rotation issues)
            img = ImageOps.exif_transpose(img)
            
            # Convert RGBA to RGB if needed
            if img.mode in('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (0, 0, 0))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to fit 16:9 with letterboxing
            img_ratio = img.width / img.height
            target_ratio = self.width / self.height
            
            if img_ratio > target_ratio:
                # Fit by width
                new_width = self.width
                new_height = int(self.width / img_ratio)
            else:
                # Fit by height
                new_height = self.height
                new_width = int(self.height * img_ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create black canvas and paste image centered
            canvas = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            x_offset = (self.width - new_width) // 2
            y_offset = (self.height - new_height) // 2
            canvas.paste(img, (x_offset, y_offset))
            
            # Save temporary processed image
            temp_img_path = output_path.replace('.mp4', '_temp.jpg')
            canvas.save(temp_img_path, 'JPEG', quality=95)
            
            # Convert to video with EXACT parameters (pre-normalized)
            cmd = [
                'ffmpeg',
                '-loop', '1',
                '-i', temp_img_path,
                '-c:v', VIDEO_SETTINGS['video_codec'],
                '-t', str(duration),
                '-pix_fmt', VIDEO_SETTINGS['pixel_format'],  # Force yuv420p
                '-r', str(self.fps),  # Force exact 30 fps
                '-vf', f'fps={self.fps}',
                '-y',
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Clean up temp image
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error creating static video from image: {e}")
            raise
    
    def extract_video_clip(self, input_path: str, output_path: str, 
                          duration: float) -> str:
        """
        Extract a random clip from video (max duration)
        
        Args:
            input_path: Input video path
            output_path: Output video path
            duration: Maximum duration in seconds
            
        Returns:
            Path to output video
        """
        try:
            # Get video duration
            probe = ffmpeg.probe(input_path)
            video_duration = float(probe['format']['duration'])
            
            # If video is shorter than target, use whole video
            if video_duration <= duration:
                start_time = 0
                clip_duration = video_duration
            else:
                # Random start point
                max_start = video_duration - duration
                start_time = random.uniform(0, max_start)
                clip_duration = duration
            
            # Check if video has audio
            has_audio = any(stream['codec_type'] == 'audio' for stream in probe.get('streams', []))
            
            # Build output parameters - FORCE constant framerate to fix VFR issues
            output_params = {
                'vf': f'fps={self.fps},scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2',
                'c:v': 'libx264',
                'crf': VIDEO_SETTINGS['crf'],
                'preset': VIDEO_SETTINGS['preset'],
                'pix_fmt': VIDEO_SETTINGS['pixel_format'],
                'r': self.fps  # Force constant framerate (fixes iPhone VFR videos)
            }
            
            # Add audio parameters if audio exists
            if has_audio:
                output_params['c:a'] = 'aac'
                output_params['b:a'] = '128k'
            
            # Extract clip and normalize to 16:9
            (
                ffmpeg
                .input(input_path, ss=start_time, t=clip_duration)
                .output(output_path, **output_params)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            return output_path
            
        except ffmpeg.Error as e:
            logging.error(f"FFmpeg error extracting video clip: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logging.error(f"Error extracting video clip: {e}")
            raise
    
    def process_gif(self, input_path: str, output_path: str) -> str:
        """
        Process GIF - convert to video, respect animation, limit duration
        
        Args:
            input_path: Input GIF path
            output_path: Output video path
            
        Returns:
            Path to output video
        """
        try:
            # Convert GIF to video with max duration
            (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    t=GIF_MAX_DURATION,
                    vf=f'scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2',
                    **{'c:v': 'libx264'},
                    pix_fmt=VIDEO_SETTINGS['pixel_format'],
                    crf=VIDEO_SETTINGS['crf']
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            return output_path
            
        except ffmpeg.Error as e:
            logging.error(f"FFmpeg error processing GIF: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logging.error(f"Error processing GIF: {e}")
            raise
    
    def create_month_separator(self, month: int, output_path: str) -> str:
        """
        Create month separator video (fade in/out with month name)
        
        Args:
            month: Month number (1-12)
            output_path: Output video path
            
        Returns:
            Path to output video
        """
        try:
            # Create image with month name
            img = Image.new('RGB', (self.width, self.height), 
                          MONTH_SEPARATOR['background_color'])
            draw = ImageDraw.Draw(img)
            
            # Load font (try multiple locations for cross-platform compatibility)
            font = None
            font_size = MONTH_SEPARATOR['font_size']
            
            # List of fonts to try (in order of preference)
            font_options = [
                # Windows
                "arial.ttf",
                "Arial.ttf",
                # Linux common locations
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",  # Arch Linux
                "/usr/share/fonts/TTF/DejaVuSans.ttf",
                # Ubuntu/Debian
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-Regular.ttf",
            ]
            
            for font_path in font_options:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    logging.debug(f"Using font: {font_path}")
                    break
                except:
                    continue
            
            # Ultimate fallback - use default with warning
            if font is None:
                logging.warning("No TTF font found, using default (text may appear small)")
                font = ImageFont.load_default()
            
            # Draw month name
            month_text = MONTH_NAMES[month - 1]
            if MONTH_SEPARATOR['show_year']:
                month_text += f" {TARGET_YEAR}"
            
            # Center text
            bbox = draw.textbbox((0, 0), month_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (self.width - text_width) // 2
            y = (self.height - text_height) // 2
            
            draw.text((x, y), month_text, fill=MONTH_SEPARATOR['text_color'], font=font)
            
            # Save image
            temp_img_path = output_path.replace('.mp4', '.jpg')
            img.save(temp_img_path, 'JPEG', quality=95)
            
            # Convert to video with fade in/out
            fade_frames = int(FADE_DURATION * self.fps)
            total_frames = int(MONTH_SEPARATOR_DURATION * self.fps)
            
            cmd = [
                'ffmpeg',
                '-loop', '1',
                '-i', temp_img_path,
                '-vf', f'fade=t=in:st=0:d={FADE_DURATION},fade=t=out:st={MONTH_SEPARATOR_DURATION - FADE_DURATION}:d={FADE_DURATION},fps={self.fps}',
                '-t', str(MONTH_SEPARATOR_DURATION),
                '-c:v', VIDEO_SETTINGS['video_codec'],
                '-pix_fmt', VIDEO_SETTINGS['pixel_format'],
                '-y',
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Clean up temp image
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error creating month separator: {e}")
            raise
    
    def process_media_file(self, media_info: Dict, index: int) -> str:
        """
        Process a single media file
        
        Args:
            media_info: Media information dictionary
            index: Sequence index
            
        Returns:
            Path to processed video clip
        """
        filepath = media_info['filepath']
        media_type = media_info['type']
        filename = os.path.basename(filepath)
        
        # Output path
        output_filename = f"{index:04d}_{os.path.splitext(filename)[0]}.mp4"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        logging.info(f"Processing [{index}]: {filename} ({media_type})")
        
        try:
            if media_type == 'gif':
                # Process GIF
                self.process_gif(filepath, output_path)
                
            elif media_type == 'video':
                # Extract video clip
                self.extract_video_clip(filepath, output_path, VIDEO_DURATION)
                
            elif media_type == 'image':
                # Convert HEIC first if needed
                process_path = filepath
                try:
                    if filepath.lower().endswith('.heic'):
                        logging.debug(f"Converting HEIC to JPG: {filename}")
                        process_path = self.convert_heic_to_jpg(filepath)
                except Exception as e:
                    logging.error(f"Failed to convert HEIC {filename}: {e}")
                    # Try to use static video method as fallback
                    return self.create_static_image_video(filepath, output_path, PHOTO_DURATION) if not filepath.lower().endswith('.heic') else None
                
                # Apply Ken Burns effect to static images
                try:
                    if KEN_BURNS['enabled']:
                        zoom_in = random.choice([True, False])
                        self.create_ken_burns_image(process_path, output_path, 
                                                   PHOTO_DURATION, zoom_in)
                    else:
                        self.create_static_image_video(process_path, output_path, 
                                                       PHOTO_DURATION)
                except Exception as e:
                    logging.error(f"Failed to process image with effects: {e}")
                    # Final fallback - try static video without Ken Burns
                    logging.warning(f"Attempting static video as final fallback for {filename}")
                    self.create_static_image_video(process_path, output_path, PHOTO_DURATION)
            
            return output_path
            
        except Exception as e:
            logging.error(f"Failed to process {filename}: {e}")
            return None
    
    def normalize_clip(self, input_path: str) -> str:
        """
        Normalize a clip to ensure consistent parameters for concatenation
        Fixes frame rate, pixel format, and ensures exact resolution
        
        Args:
            input_path: Path to clip to normalize
            
        Returns:
            Path to normalized clip (same as input after normalization)
        """
        try:
            normalized_path = input_path.replace('.mp4', '_norm.mp4')
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', f'fps={self.fps},scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2',
                '-c:v', VIDEO_SETTINGS['video_codec'],
                '-crf', str(VIDEO_SETTINGS['crf']),
                '-pix_fmt', VIDEO_SETTINGS['pixel_format'],  # Force yuv420p
                '-r', str(self.fps),  # Force 30 fps
                '-c:a', 'aac',
                '-b:a', '128k',
                '-strict', 'experimental',
                '-y',
                normalized_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Replace original with normalized
            if os.path.exists(normalized_path):
                os.remove(input_path)
                os.rename(normalized_path, input_path)
            
            return input_path
            
        except Exception as e:
            logging.error(f"Failed to normalize clip {input_path}: {e}")
            return input_path  # Return original if normalization fails
    
    def add_date_caption(self, input_path: str, date_str: str) -> str:
        """
        Add date caption overlay to a video clip
        
        Args:
            input_path: Path to video clip
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Path to video with caption
        """
        from config import DATE_CAPTION
        
        if not DATE_CAPTION['enabled']:
            return input_path
        
        try:
            # Parse date and format nicely
            from datetime import datetime
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            # Format: "1 Ene 2025"
            months_short = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                           "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            date_text = f"{date_obj.day} {months_short[date_obj.month-1]} {date_obj.year}"
            
            # Determine position
            position = DATE_CAPTION['position']
            margin = DATE_CAPTION['margin']
            
            if position == 'top_left':
                x, y = margin, margin
            elif position == 'top_right':
                x, y = f'w-text_w-{margin}', margin
            elif position == 'bottom_left':
                x, y = margin, f'h-text_h-{margin}'
            else:  # bottom_right
                x, y = f'w-text_w-{margin}', f'h-text_h-{margin}'
            
            # Create caption with FFmpeg drawtext
            caption_path = input_path.replace('.mp4', '_caption.mp4')
            
            drawtext_filter = (
                f"drawtext=text='{date_text}':"
                f"fontsize={DATE_CAPTION['font_size']}:"
                f"fontcolor={DATE_CAPTION['font_color']}:"
                f"x={x}:y={y}:"
                f"shadowcolor=black@0.8:shadowx=2:shadowy=2"
            )
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', drawtext_filter,
                '-c:v', VIDEO_SETTINGS['video_codec'],
                '-crf', str(VIDEO_SETTINGS['crf']),
                '-c:a', 'copy',
                '-y',
                caption_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Replace original with captioned version
            if os.path.exists(caption_path):
                os.remove(input_path)
                os.rename(caption_path, input_path)
            
            return input_path
            
        except Exception as e:
            logging.warning(f"Failed to add date caption: {e}")
            return input_path  # Return original if caption fails
    
    def compile_final_video(self, clip_list: List[str], output_path: str):
        """
        Compile all clips into final video with progress display
        
        Args:
            clip_list: List of video clip paths in order
            output_path: Final output video path
        """
        logging.info("Compiling final video...")
        
        # Create concat file for FFmpeg
        concat_file = os.path.join(TEMP_FOLDER, 'concat_list.txt')
        with open(concat_file, 'w', encoding='utf-8') as f:
            for clip in clip_list:
                # FFmpeg concat format
                f.write(f"file '{os.path.abspath(clip)}'\n")
        
        # Calculate total duration for progress estimation
        total_duration = 0
        try:
            for clip in clip_list:
                probe = ffmpeg.probe(clip)
                total_duration += float(probe['format']['duration'])
            logging.info(f"Total duration to process: {format_duration(total_duration)}")
        except:
            logging.warning("Could not calculate total duration for progress")
            total_duration = 0
        
        # Concatenate all clips with re-encoding for compatibility
        # This prevents frozen frame issues from codec mismatches
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c:v', VIDEO_SETTINGS['video_codec'],
            '-crf', str(VIDEO_SETTINGS['crf']),
            '-preset', VIDEO_SETTINGS['preset'],
            '-pix_fmt', VIDEO_SETTINGS['pixel_format'],
            '-c:a', 'aac',
            '-b:a', '128k',
            '-progress', 'pipe:1',  # Send progress to stdout
            '-y',
            output_path
        ]
        
        try:
            import sys
            import re
            import threading
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Create a thread to consume stderr to prevent deadlock
            # FFmpeg writes a lot to stderr, and if the buffer fills up, it will pause
            stderr_lines = []
            def read_stderr():
                """Read stderr in background to prevent buffer overflow deadlock"""
                for line in process.stderr:
                    stderr_lines.append(line)
            
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stderr_thread.start()
            
            last_time = 0
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                
                # Parse progress from FFmpeg output
                if line.startswith('out_time_ms='):
                    value = line.split('=')[1].strip()
                    # Skip if value is N/A (happens with some video formats)
                    if value == 'N/A' or not value.isdigit():
                        continue
                    time_ms = int(value)
                    time_s = time_ms / 1000000.0  # Convert microseconds to seconds
                    
                    # Update progress every 5 seconds
                    if time_s - last_time >= 5 or (total_duration > 0 and time_s >= total_duration * 0.99):
                        last_time = time_s
                        if total_duration > 0:
                            progress = min(100, (time_s / total_duration) * 100)
                            bar_length = 40
                            filled = int(bar_length * progress / 100)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            print(f"\r⏳ Progreso: [{bar}] {progress:.1f}% ({format_duration(time_s)} / {format_duration(total_duration)})", end='', flush=True)
                        else:
                            print(f"\r⏳ Procesando: {format_duration(time_s)}", end='', flush=True)
            
            # Wait for completion
            process.wait()
            
            # Wait for stderr thread to finish reading
            stderr_thread.join(timeout=5)
            
            # Print newline after progress bar
            if total_duration > 0:
                print()  # New line after progress bar
            
            if process.returncode != 0:
                stderr_output = ''.join(stderr_lines)
                logging.error(f"Error concatenating videos: {stderr_output}")
                raise subprocess.CalledProcessError(process.returncode, cmd, stderr=stderr_output)
            
            logging.info(f"✅ Final video created: {output_path}")
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error concatenating videos: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            raise
    
    def generate(self):
        """Main video generation workflow"""
        logging.info("=" * 60)
        logging.info("VIDEO GENERATION SCRIPT - PHASE 3")
        logging.info("=" * 60)
        
        # Load assignments
        logging.info("Loading media assignments...")
        assignments = self.load_assignments()
        
        # Sort dates
        sorted_dates = sorted(assignments.keys())
        logging.info(f"Processing {len(sorted_dates)} days with media")
        
        # Process all media in chronological order
        all_clips = []
        all_clip_dates = []  # Track dates for captions
        current_month = 0
        clip_index = 0
        
        for date_str in sorted_dates:
            # Parse date
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Add month separator if entering new month
            if date_obj.month != current_month:
                current_month = date_obj.month
                logging.info(f"\n--- {MONTH_NAMES[current_month - 1]} ---")
                
                separator_path = os.path.join(
                    PROCESSED_FOLDER, 
                    f"separator_{current_month:02d}.mp4"
                )
                self.create_month_separator(current_month, separator_path)
                all_clips.append(separator_path)
                all_clip_dates.append(None)  # No date for separators
            
            # Process all media for this day
            media_list = assignments[date_str]
            for media_info in media_list:
                processed_clip = self.process_media_file(media_info, clip_index)
                if processed_clip:
                    all_clips.append(processed_clip)
                    all_clip_dates.append(date_str)  # Track date for this clip
                    clip_index += 1
        
        # Normalize only video/GIF clips (images are already pre-normalized)
        logging.info(f"\nNormalizing video clips for compatibility...")
        for i, clip in enumerate(all_clips):
            clip_name = os.path.basename(clip)
            
            # Skip month separators and image-based clips (already normalized)
            if 'separator_' in clip_name or all_clip_dates[i]:
                # Check if it's a video/GIF that needs normalization
                # Images (from Ken Burns or static) are already pre-normalized
                original_file = None
                if all_clip_dates[i]:
                    # Find the original media file
                    date_str = all_clip_dates[i]
                    for media_info in assignments[date_str]:
                        if clip_name.startswith(f"{clip_name.split('_')[0]}_"):
                            original_file = media_info['filepath']
                            break
                
                # Only normalize if original was a video or GIF
                if original_file and (original_file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.gif'))):
                    logging.info(f"Normalizing {i+1}/{len(all_clips)}: {clip_name}")
                    self.normalize_clip(clip)
            
            # Add date caption if enabled (after normalization)
            if all_clip_dates[i]:  # Skip separators
                self.add_date_caption(clip, all_clip_dates[i])
        
        # Compile final video
        logging.info(f"\nTotal clips to compile: {len(all_clips)}")
        self.compile_final_video(all_clips, FINAL_VIDEO)
        
        # Calculate final duration
        total_duration = sum([
            PHOTO_DURATION if 'image' in clip else 
            VIDEO_DURATION if 'video' in clip or clip.endswith('.mp4') else 
            GIF_MAX_DURATION
            for clip in all_clips
        ])
        
        logging.info("\n" + "=" * 60)
        logging.info("VIDEO GENERATION COMPLETE")
        logging.info("=" * 60)
        logging.info(f"Final video: {FINAL_VIDEO}")
        logging.info(f"Total duration: ~{format_duration(total_duration)}")
        logging.info(f"Number of clips: {len(all_clips)}")


def main():
    """Main execution"""
    setup_logging(LOG_LEVEL)
    
    generator = VideoGenerator()
    generator.generate()


if __name__ == "__main__":
    main()
