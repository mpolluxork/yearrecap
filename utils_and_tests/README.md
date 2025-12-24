# Utils and Tests

This folder contains test scripts and deprecated utilities that are not essential for the main video generation workflow.

## Test Scripts

- `test_date_detection.py` - Tests for enhanced filename date extraction
- `test_january.py` - Test script for January month processing
- `test_july.py` - Test script for July month processing  
- `test_quick.py` - Quick test for video generation

## Deprecated Scripts

- `generate_full_year.py` - Old version (replaced by `generate_recap_optimized.py`)
- `generate_recap.py` - Old version (replaced by `generate_recap_optimized.py`)

## Running Tests

From the project root directory:

```bash
# Test date detection
python utils_and_tests/test_date_detection.py

# Test specific month
python utils_and_tests/test_january.py
```

These scripts are kept for reference and debugging purposes but are not required for normal operation of the video recap generation system.
