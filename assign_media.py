"""
Phase 2: Media Assignment Script
Scans media files and assigns them to days of 2025 based on metadata
"""
import os
import json
import csv
from datetime import datetime, date
from collections import defaultdict
from typing import Dict, List, Tuple
import logging

from config import (
    INPUT_FOLDER, TARGET_YEAR, ALL_SUPPORTED_FORMATS,
    MEDIA_ASSIGNMENT_JSON, REPORT_VISUAL_TXT, REPORT_DETAILED_CSV,
    LOG_LEVEL
)
from utils import get_media_date, is_image, is_video, is_gif, setup_logging


def scan_media_folder(folder_path: str) -> List[str]:
    """
    Scan folder for supported media files
    
    Args:
        folder_path: Path to media folder
        
    Returns:
        List of absolute file paths
    """
    media_files = []
    
    if not os.path.exists(folder_path):
        logging.error(f"Folder not found: {folder_path}")
        return media_files
    
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        
        if not os.path.isfile(filepath):
            continue
        
        ext = os.path.splitext(filename)[1].lower()
        if ext in ALL_SUPPORTED_FORMATS:
            media_files.append(filepath)
    
    logging.info(f"Found {len(media_files)} media files")
    return media_files


def assign_media_to_days(media_files: List[str]) -> Dict[str, List[Dict]]:
    """
    Assign media files to specific days based on extracted dates
    
    Args:
        media_files: List of media file paths
        
    Returns:
        Dictionary mapping date strings (YYYY-MM-DD) to list of media info
    """
    assignments = defaultdict(list)
    stats = {
        'total_files': len(media_files),
        'assigned': 0,
        'skipped_wrong_year': 0,
        'date_sources': defaultdict(int)
    }
    
    for filepath in media_files:
        filename = os.path.basename(filepath)
        
        try:
            media_date, source = get_media_date(filepath)
            
            # Only include files from target year
            if media_date.year != TARGET_YEAR:
                stats['skipped_wrong_year'] += 1
                logging.debug(f"Skipping {filename} - wrong year: {media_date.year}")
                continue
            
            # Format date as string key
            date_key = media_date.strftime("%Y-%m-%d")
            
            # Determine media type
            if is_gif(filepath):
                media_type = 'gif'
            elif is_video(filepath):
                media_type = 'video'
            elif is_image(filepath):
                media_type = 'image'
            else:
                media_type = 'unknown'
            
            # Add to assignments
            assignments[date_key].append({
                'filepath': filepath,
                'filename': filename,
                'type': media_type,
                'date': media_date.isoformat(),
                'source': source
            })
            
            stats['assigned'] += 1
            stats['date_sources'][source] += 1
            
        except Exception as e:
            logging.error(f"Error processing {filename}: {e}")
    
    # Sort media within each day by timestamp
    for date_key in assignments:
        assignments[date_key].sort(key=lambda x: x['date'])
    
    logging.info(f"\nAssignment Statistics:")
    logging.info(f"  Total files scanned: {stats['total_files']}")
    logging.info(f"  Files assigned: {stats['assigned']}")
    logging.info(f"  Files skipped (wrong year): {stats['skipped_wrong_year']}")
    logging.info(f"\nDate extraction sources:")
    for source, count in stats['date_sources'].items():
        logging.info(f"  {source}: {count}")
    
    return dict(assignments)


def generate_visual_report(assignments: Dict[str, List[Dict]]) -> str:
    """
    Generate ASCII calendar showing which days have media
    
    Args:
        assignments: Date to media mapping
        
    Returns:
        Visual report as string
    """
    import calendar
    
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append(f"YEAR {TARGET_YEAR} MEDIA COVERAGE REPORT")
    report_lines.append("=" * 60)
    report_lines.append("")
    
    filled_days = len(assignments)
    total_media = sum(len(media_list) for media_list in assignments.values())
    
    report_lines.append(f"Days with media: {filled_days} / 365")
    report_lines.append(f"Total media files: {total_media}")
    report_lines.append(f"Average media per day: {total_media / max(filled_days, 1):.1f}")
    report_lines.append("")
    
    # Month by month breakdown
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        report_lines.append(f"\n{month_name} {TARGET_YEAR}")
        report_lines.append("-" * 30)
        
        # Calendar header
        cal = calendar.monthcalendar(TARGET_YEAR, month)
        report_lines.append("Mo Tu We Th Fr Sa Su")
        
        for week in cal:
            week_str = []
            for day in week:
                if day == 0:
                    week_str.append("  ")
                else:
                    date_key = f"{TARGET_YEAR}-{month:02d}-{day:02d}"
                    if date_key in assignments:
                        count = len(assignments[date_key])
                        if count > 9:
                            week_str.append("9+")
                        else:
                            week_str.append(f"{count:>2}")
                    else:
                        week_str.append(" .")
            report_lines.append(" ".join(week_str))
        
        # Month summary
        month_days = [d for d in assignments.keys() if d.startswith(f"{TARGET_YEAR}-{month:02d}")]
        month_media = sum(len(assignments[d]) for d in month_days)
        report_lines.append(f"  {len(month_days)} days, {month_media} media files")
    
    report_lines.append("\n" + "=" * 60)
    report_lines.append("Legend: . = no media, number = count of media files")
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)


def generate_csv_report(assignments: Dict[str, List[Dict]]) -> List[List[str]]:
    """
    Generate detailed CSV report
    
    Args:
        assignments: Date to media mapping
        
    Returns:
        List of rows for CSV
    """
    rows = [['Date', 'Day_of_Week', 'Media_Count', 'Filename', 'Type', 'Date_Source']]
    
    # Generate all days of the year
    start_date = date(TARGET_YEAR, 1, 1)
    for day_offset in range(365):
        current_date = date(TARGET_YEAR, 1, 1)
        from datetime import timedelta
        current_date = start_date + timedelta(days=day_offset)
        date_key = current_date.strftime("%Y-%m-%d")
        day_name = current_date.strftime("%A")
        
        if date_key in assignments:
            media_list = assignments[date_key]
            for media_info in media_list:
                rows.append([
                    date_key,
                    day_name,
                    str(len(media_list)),
                    media_info['filename'],
                    media_info['type'],
                    media_info['source']
                ])
        else:
            # Empty day
            rows.append([date_key, day_name, '0', '', '', ''])
    
    return rows


def save_assignment_json(assignments: Dict, filepath: str):
    """Save assignments to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(assignments, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved assignment data to: {filepath}")


def save_visual_report(report: str, filepath: str):
    """Save visual report to text file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    logging.info(f"Saved visual report to: {filepath}")


def save_csv_report(rows: List[List[str]], filepath: str):
    """Save CSV report"""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    logging.info(f"Saved detailed report to: {filepath}")


def main():
    """Main execution"""
    setup_logging(LOG_LEVEL)
    
    logging.info("=" * 60)
    logging.info("MEDIA ASSIGNMENT SCRIPT - PHASE 2")
    logging.info("=" * 60)
    logging.info(f"Scanning folder: {INPUT_FOLDER}")
    logging.info(f"Target year: {TARGET_YEAR}")
    logging.info("")
    
    # Step 1: Scan for media files
    media_files = scan_media_folder(INPUT_FOLDER)
    
    if not media_files:
        logging.error("No media files found!")
        return
    
    # Step 2: Assign media to days
    logging.info("\nAssigning media to days...")
    assignments = assign_media_to_days(media_files)
    
    # Step 3: Generate reports
    logging.info("\nGenerating reports...")
    
    # JSON assignment file
    save_assignment_json(assignments, MEDIA_ASSIGNMENT_JSON)
    
    # Visual calendar report
    visual_report = generate_visual_report(assignments)
    save_visual_report(visual_report, REPORT_VISUAL_TXT)
    print("\n" + visual_report)
    
    # CSV detailed report
    csv_rows = generate_csv_report(assignments)
    save_csv_report(csv_rows, REPORT_DETAILED_CSV)
    
    logging.info("\n" + "=" * 60)
    logging.info("MEDIA ASSIGNMENT COMPLETE")
    logging.info("=" * 60)
    logging.info(f"\nOutput files:")
    logging.info(f"  1. {MEDIA_ASSIGNMENT_JSON}")
    logging.info(f"  2. {REPORT_VISUAL_TXT}")
    logging.info(f"  3. {REPORT_DETAILED_CSV}")
    logging.info("\nNext step: Run generate_video.py to create the final video")


if __name__ == "__main__":
    main()
