"""
Test script for enhanced date detection
"""
from utils import extract_date_from_filename
from datetime import datetime

# Test cases for filename date extraction
test_filenames = [
    "IMG_20251212.jpg",
    "IMG-20250105-WA0010.jpg",
    "Screenshot_20250323_181709_AppSheet.jpg",
    "VID_20250401.mp4",
    "20250102_161334.jpg",
    "2025-03-14_photo.jpg",
    "vacation.jpg",  # No date
    "photo_19951231.jpg",  # Old date
]

print("FILENAME DATE EXTRACTION TESTS")
print("=" * 60)

for filename in test_filenames:
    date = extract_date_from_filename(filename)
    if date:
        print(f"OK  {filename:45} => {date.strftime('%Y-%m-%d')}")
    else:
        print(f"NO  {filename:45} => No date found")

print("\nTests completed!")
