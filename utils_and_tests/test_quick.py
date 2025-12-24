"""
Quick test script to verify video generation works on a small sample
"""
import os
import json
from generate_video import VideoGenerator
from config import MEDIA_ASSIGNMENT_JSON
import logging

logging.basicConfig(level=logging.INFO)

# Load assignments
with open(MEDIA_ASSIGNMENT_JSON, 'r') as f:
    all_assignments = json.load(f)

# Take only first 5 days with media
test_assignments = {}
count = 0
for date_key in sorted(all_assignments.keys()):
    test_assignments[date_key] = all_assignments[date_key]
    count += 1
    if count >= 5:
        break

# Save test assignment
test_file = 'test_assignment.json'
with open(test_file, 'w') as f:
    json.dump(test_assignments, f, indent=2)

print(f"Created test assignment with {count} days")
print("Modify generate_video.py to use 'test_assignment.json' instead of media_assignment.json")
print("Then run: python generate_video.py")
