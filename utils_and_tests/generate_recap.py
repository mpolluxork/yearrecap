"""
YEAR IN 365 SECONDS - Master Script
Run this single command to generate your complete 2025 video recap

This script:
1. Scans your media folder and assigns files to days
2. Generates the complete video with Ken Burns effects
3. Cleans up temporary files automatically

Usage: python generate_recap.py
"""
import os
import shutil
import logging
from utils import setup_logging
from config import (
    PROCESSED_FOLDER, TEMP_FOLDER, LOG_LEVEL,
    MEDIA_ASSIGNMENT_JSON, REPORT_VISUAL_TXT, REPORT_DETAILED_CSV
)

# Import the main functions
from assign_media import main as assign_media_main
from generate_video import VideoGenerator

def cleanup_temp_files():
    """Remove temporary files and folders after video generation"""
    logging.info("\n" + "="*60)
    logging.info("CLEANING UP TEMPORARY FILES")
    logging.info("="*60)
    
    # Remove processed folder
    if os.path.exists(PROCESSED_FOLDER):
        try:
            shutil.rmtree(PROCESSED_FOLDER)
            logging.info(f"✓ Removed: {PROCESSED_FOLDER}")
        except Exception as e:
            logging.warning(f"Could not remove {PROCESSED_FOLDER}: {e}")
    
    # Remove temp folder
    if os.path.exists(TEMP_FOLDER):
        try:
            shutil.rmtree(TEMP_FOLDER)
            logging.info(f"✓ Removed: {TEMP_FOLDER}")
        except Exception as e:
            logging.warning(f"Could not remove {TEMP_FOLDER}: {e}")
    
    # Remove test files
    for pattern in ['*TEST*.mp4', '*_january.json', '*_july.json']:
        import glob
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                logging.info(f"✓ Removed: {file}")
            except Exception as e:
                logging.warning(f"Could not remove {file}: {e}")
    
    logging.info("\nTemporary files cleaned up successfully!")


def main():
    """Main execution - Complete video generation workflow"""
    setup_logging(LOG_LEVEL)
    
    print("\n" + "="*70)
    print("           YEAR IN 365 SECONDS - 2025 RECAP")
    print("="*70)
    print()
    
    try:
        # PHASE 1: Scan and assign media to days
        print("PHASE 1: Scanning media and assigning to days...")
        print("-" * 70)
        assign_media_main()
        
        # PHASE 2: Generate video
        print("\n" + "="*70)
        print("PHASE 2: Generating video with effects...")
        print("-" * 70)
        generator = VideoGenerator()
        generator.generate()
        
        # PHASE 3: Cleanup
        cleanup_temp_files()
        
        # Final summary
        print("\n" + "="*70)
        print("           ✨ VIDEO GENERATION COMPLETE ✨")
        print("="*70)
        print()
        print("📁 Output files:")
        print(f"   🎬 Video: 2025_recap.mp4")
        print(f"   📊 Visual report: {os.path.basename(REPORT_VISUAL_TXT)}")
        print(f"   📄 Detailed CSV: {os.path.basename(REPORT_DETAILED_CSV)}")
        print()
        print("🎉 ¡Tu video del 2025 está listo!")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        print("Temporary files were not cleaned up")
        print("Run cleanup manually if needed")
    except Exception as e:
        logging.error(f"\n❌ Error during video generation: {e}")
        print("\n⚠️  Video generation failed")
        print("Check the error messages above for details")
        raise


if __name__ == "__main__":
    main()
