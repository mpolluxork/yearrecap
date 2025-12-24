"""
Generate the FULL YEAR 2025 recap video
Run this when you're ready for the final video!
"""
import logging
from generate_video import VideoGenerator
from utils import setup_logging

setup_logging("INFO")

logging.info("=" * 70)
logging.info("GENERATING FULL YEAR 2025 VIDEO RECAP")
logging.info("=" * 70)
logging.info("")
logging.info("This will process ALL 503 media files for 2025")
logging.info("Estimated time: 30-45 minutes")
logging.info("Output: 2025_recap.mp4")
logging.info("")
logging.info("=" * 70)

# Generate full video
generator = VideoGenerator()
generator.generate()

logging.info("\n" + "=" * 70)
logging.info("¡LISTO! Tu video del 2025 está completo")
logging.info("=" * 70)
