"""
YEAR IN 365 SECONDS - Optimized Master Script
Run this single command to generate your complete 2025 video recap with smart caching

OPTIMIZATIONS:
1. Pre-normalized images - no redundant processing
2. Incremental detection - only process new/changed files
3. Processed clip caching - reuse existing processed files
4. Monthly generation - 12 smaller videos, then concatenate

Usage: python generate_recap_optimized.py
"""
import os
import shutil
import logging
from utils import setup_logging
from config import (
    PROCESSED_FOLDER, TEMP_FOLDER, LOG_LEVEL, INPUT_FOLDER,
    MEDIA_ASSIGNMENT_JSON, REPORT_VISUAL_TXT, REPORT_DETAILED_CSV,
    OUTPUT_VIDEO_FOLDER, CHECKPOINT_FILE
)
from checkpoint import CheckpointManager

def update_media_assignments(checkpoint_manager: CheckpointManager):
    """Update media assignments incrementally"""
    from incremental_scan import incremental_media_scan
    from assign_media import assign_media_to_days, save_assignment_json
    
    # Check if already completed
    if checkpoint_manager.is_step_complete('media_scan') and checkpoint_manager.is_step_complete('media_assignment'):
        logging.info("✅ Media scan and assignment already completed (from checkpoint)")
        return False
    
    logging.info("Checking for new/changed media files...")
    all_files, files_to_process = incremental_media_scan(INPUT_FOLDER)
    checkpoint_manager.mark_step_complete('media_scan')
    
    if not files_to_process and os.path.exists(MEDIA_ASSIGNMENT_JSON):
        logging.info("✓ No new files detected, using existing assignments")
        checkpoint_manager.mark_step_complete('media_assignment')
        return False
    
    logging.info(f"Found {len(files_to_process)} new/changed files")
    logging.info("Updating media assignments...")
    
    # Re-run assignment for all files (fast operation)
    assignments = assign_media_to_days(all_files)
    save_assignment_json(assignments, MEDIA_ASSIGNMENT_JSON)
    checkpoint_manager.mark_step_complete('media_assignment')
    
    return True


def cleanup_temp_files():
    """Remove only temporary files, keep processed clips and output videos for caching"""
    logging.info("\n" + "="*60)
    logging.info("CLEANING UP TEMPORARY FILES")
    logging.info("="*60)
    
    # Remove temp folder only (keep processed for caching)
    if os.path.exists(TEMP_FOLDER):
        try:
            shutil.rmtree(TEMP_FOLDER)
            logging.info(f"✓ Removed: {TEMP_FOLDER}")
        except Exception as e:
            logging.warning(f"Could not remove {TEMP_FOLDER}: {e}")
    
    # NOTE: We now keep monthly videos in output/ folder
    # They are useful for debugging and re-processing
    
    logging.info("\nTemporary files cleaned up!")
    logging.info(f"Note: Keeping {PROCESSED_FOLDER}/ for faster regeneration")
    logging.info(f"Note: Keeping {OUTPUT_VIDEO_FOLDER}/ with monthly and final videos")


def main():
    """Main execution - Optimized complete workflow with checkpoint/resume support"""
    setup_logging(LOG_LEVEL)
    
    print("\n" + "="*70)
    print("     YEAR IN 365 SECONDS - 2025 RECAP (OPTIMIZED)")
    print("="*70)
    print()
    
    # Initialize checkpoint manager
    checkpoint_manager = CheckpointManager(CHECKPOINT_FILE)
    
    # Check if process was previously completed
    if checkpoint_manager.is_complete():
        print("🔄 Previous run completed successfully.")
        print("Starting fresh (clearing checkpoint)...\n")
        checkpoint_manager.clear()
    elif checkpoint_manager.should_resume():
        print("💾 Resuming from previous checkpoint...")
        print(f"Progress: {checkpoint_manager.get_progress_summary()}\n")
    
    try:
        # Ensure folders exist
        os.makedirs(PROCESSED_FOLDER, exist_ok=True)
        os.makedirs(OUTPUT_VIDEO_FOLDER, exist_ok=True)
        
        # PHASE 1: Incremental media detection
        print("PHASE 1: Detecting new/changed media files...")
        print("-" * 70)
        has_changes = update_media_assignments(checkpoint_manager)
        
        if not has_changes and not os.path.exists(MEDIA_ASSIGNMENT_JSON):
            # First run
            from assign_media import main as assign_media_main
            assign_media_main()
            checkpoint_manager.mark_step_complete('media_assignment')
        
        # PHASE 2: Generate video with caching and checkpoint support
        print("\n" + "="*70)
        print("PHASE 2: Generating video (using cache when possible)...")
        print("-" * 70)
        
        from generate_optimized import generate_optimized
        final_video = generate_optimized(checkpoint_manager)
        
        # Mark as complete
        checkpoint_manager.mark_all_complete()
        
        # PHASE 3: Cleanup
        cleanup_temp_files()
        
        # Final summary
        print("\n" + "="*70)
        print("           ✨ VIDEO GENERATION COMPLETE ✨")
        print("="*70)
        print()
        print("📁 Output files:")
        print(f"   🎬 Video: {os.path.relpath(final_video)}")
        print(f"   📊 Reports: {os.path.basename(REPORT_VISUAL_TXT)}, {os.path.basename(REPORT_DETAILED_CSV)}")
        print()
        print(f"💾 Cached: {PROCESSED_FOLDER}/ (kept for faster regeneration)")
        print(f"📂 Output: {OUTPUT_VIDEO_FOLDER}/ (monthly + final videos)")
        print()
        print("🎉 ¡Tu video del 2025 está listo!")
        print("="*70)
        print()
        print("💡 Tip: Add/remove files in 'Recap 2025/' and run again")
        print("   Only new/changed files will be processed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        print("💾 Checkpoint saved - run again to resume from where you left off")
        checkpoint_manager.save()
    except Exception as e:
        logging.error(f"\n❌ Error during video generation: {e}")
        print("\n⚠️  Video generation failed")
        print("Check the error messages above for details")
        checkpoint_manager.save()  # Save progress even on error
        raise


if __name__ == "__main__":
    main()
