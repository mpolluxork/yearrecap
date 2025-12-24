"""
Test script: Generate video only for January 2025
"""
import os
import json
from generate_video import VideoGenerator
from config import MEDIA_ASSIGNMENT_JSON, OUTPUT_FOLDER
import logging
from utils import setup_logging

setup_logging("INFO")

# Load all assignments
logging.info("Loading media assignments...")
with open(MEDIA_ASSIGNMENT_JSON, 'r', encoding='utf-8') as f:
    all_assignments = json.load(f)

# Filter only January dates
january_assignments = {}
for date_key in sorted(all_assignments.keys()):
    if date_key.startswith('2025-01'):
        january_assignments[date_key] = all_assignments[date_key]

logging.info(f"Found {len(january_assignments)} days in January with media")
total_files = sum(len(media_list) for media_list in january_assignments.values())
logging.info(f"Total files for January: {total_files}")

# Save temporary test assignment
test_file = 'media_assignment_january.json'
with open(test_file, 'w', encoding='utf-8') as f:
    json.dump(january_assignments, f, indent=2)

logging.info(f"Created test assignment: {test_file}")

# Temporarily modify the generator to use test file
class JanuaryVideoGenerator(VideoGenerator):
    def load_assignments(self):
        with open(test_file, 'r', encoding='utf-8') as f:
            return json.load(f)

# Generate video
logging.info("\nStarting video generation for January only...")
generator = JanuaryVideoGenerator()

# Override output filename
from config import FINAL_VIDEO
test_output = FINAL_VIDEO.replace('2025_recap.mp4', '2025_recap_JANUARY_TEST.mp4')
original_final_video = FINAL_VIDEO

# Patch the config temporarily
import config
config.FINAL_VIDEO = test_output

try:
    generator.generate()
finally:
    # Restore
    config.FINAL_VIDEO = original_final_video
    
logging.info(f"\n{'='*60}")
logging.info(f"TEST VIDEO COMPLETE: {test_output}")
logging.info(f"{'='*60}")
