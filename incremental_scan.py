"""
Incremental media detection - only process new/changed files
"""
import os
import json
from typing import Dict, List, Set, Tuple
from datetime import datetime

def load_previous_scan(scan_file: str) -> Dict:
    """Load previous media scan results"""
    if not os.path.exists(scan_file):
        return {}
    
    with open(scan_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_scan_results(scan_file: str, results: Dict):
    """Save current scan results for next comparison"""
    with open(scan_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)


def get_file_signature(filepath: str) -> str:
    """Get file signature (mtime + size) for change detection"""
    stat = os.stat(filepath)
    return f"{stat.st_mtime}_{stat.st_size}"


def detect_changes(current_files: Dict[str, str], previous_scan: Dict) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    Detect which files are new, changed, or deleted
    
    Args:
        current_files: Dict of {filepath: signature}
        previous_scan: Previous scan results
        
    Returns:
        Tuple of (new_files, changed_files, deleted_files)
    """
    current_paths = set(current_files.keys())
    previous_paths = set(previous_scan.keys())
    
    # New files
    new_files = current_paths - previous_paths
    
    # Deleted files
    deleted_files = previous_paths - current_paths
    
    # Changed files (same path, different signature)
    changed_files = set()
    for path in current_paths & previous_paths:
        if current_files[path] != previous_scan.get(path):
            changed_files.add(path)
    
    return new_files, changed_files, deleted_files


def incremental_media_scan(media_folder: str, scan_cache_file: str = "media_scan_cache.json") -> Tuple[List[str], Set[str]]:
    """
    Perform incremental scan of media folder
    
    Args:
        media_folder: Path to media folder
        scan_cache_file: Where to store scan cache
        
    Returns:
        Tuple of (all_files, files_to_process)
    """
    from config import ALL_SUPPORTED_FORMATS
    
    # Scan current files
    current_files = {}
    for filename in os.listdir(media_folder):
        filepath = os.path.join(media_folder, filename)
        
        if not os.path.isfile(filepath):
            continue
        
        ext = os.path.splitext(filename)[1].lower()
        if ext in ALL_SUPPORTED_FORMATS:
            current_files[filepath] = get_file_signature(filepath)
    
    # Load previous scan
    previous_scan = load_previous_scan(scan_cache_file)
    
    # Detect changes
    new_files, changed_files, deleted_files = detect_changes(current_files, previous_scan)
    
    # Files that need processing
    files_to_process = new_files | changed_files
    
    # Save current scan
    save_scan_results(scan_cache_file, current_files)
    
    return list(current_files.keys()), files_to_process


if __name__ == "__main__":
    # Test incremental scan
    from config import INPUT_FOLDER
    all_files, to_process = incremental_media_scan(INPUT_FOLDER)
    print(f"Total files: {len(all_files)}")
    print(f"Files to process: {len(to_process)}")
    if to_process:
        print("New/changed files:")
        for f in list(to_process)[:10]:
            print(f"  - {os.path.basename(f)}")
