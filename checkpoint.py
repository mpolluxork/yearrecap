"""
Checkpoint Manager for Resume Functionality
Allows the video generation process to resume from where it left off after interruption
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set


class CheckpointManager:
    """Manages checkpoints for resuming interrupted video generation"""
    
    def __init__(self, checkpoint_file: str):
        """
        Initialize checkpoint manager
        
        Args:
            checkpoint_file: Path to checkpoint JSON file
        """
        self.checkpoint_file = checkpoint_file
        self.checkpoint_data = self._load()
    
    def _load(self) -> Dict:
        """Load checkpoint data from file"""
        if not os.path.exists(self.checkpoint_file):
            return self._create_empty_checkpoint()
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logging.info(f"📋 Loaded checkpoint from {self.checkpoint_file}")
                return data
        except Exception as e:
            logging.warning(f"Error loading checkpoint: {e}. Starting fresh.")
            return self._create_empty_checkpoint()
    
    def _create_empty_checkpoint(self) -> Dict:
        """Create empty checkpoint structure"""
        return {
            'last_update': None,
            'steps_completed': {
                'media_scan': False,
                'media_assignment': False,
                'months_processed': []
            },
            'completed': False
        }
    
    def save(self):
        """Save current checkpoint to disk"""
        self.checkpoint_data['last_update'] = datetime.now().isoformat()
        
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.checkpoint_data, f, indent=2)
            logging.debug(f"💾 Checkpoint saved")
        except Exception as e:
            logging.error(f"Error saving checkpoint: {e}")
    
    def mark_step_complete(self, step_name: str):
        """
        Mark a step as complete
        
        Args:
            step_name: Name of the step (e.g., 'media_scan', 'media_assignment')
        """
        if step_name in self.checkpoint_data['steps_completed']:
            self.checkpoint_data['steps_completed'][step_name] = True
            self.save()
            logging.info(f"✓ Step completed: {step_name}")
    
    def mark_month_complete(self, month: int):
        """
        Mark a month as processed
        
        Args:
            month: Month number (1-12)
        """
        months = self.checkpoint_data['steps_completed']['months_processed']
        if month not in months:
            months.append(month)
            months.sort()
            self.save()
            logging.info(f"✓ Month {month} completed")
    
    def is_step_complete(self, step_name: str) -> bool:
        """Check if a step is already complete"""
        return self.checkpoint_data['steps_completed'].get(step_name, False)
    
    def is_month_complete(self, month: int) -> bool:
        """Check if a month is already processed"""
        return month in self.checkpoint_data['steps_completed']['months_processed']
    
    def invalidate_month(self, month: int):
        """
        Invalidate a month to force regeneration
        
        Args:
            month: Month number (1-12)
        """
        months = self.checkpoint_data['steps_completed']['months_processed']
        if month in months:
            months.remove(month)
            self.save()
            logging.info(f"🔄 Month {month} invalidated - will be regenerated")
    
    def invalidate_months(self, months_to_invalidate: List[int]):
        """
        Invalidate multiple months to force regeneration
        
        Args:
            months_to_invalidate: List of month numbers (1-12)
        """
        for month in months_to_invalidate:
            self.invalidate_month(month)
    
    def get_completed_months(self) -> List[int]:
        """Get list of completed months"""
        return self.checkpoint_data['steps_completed']['months_processed']
    
    def mark_all_complete(self):
        """Mark the entire process as complete"""
        self.checkpoint_data['completed'] = True
        self.save()
        logging.info("✅ All processing complete!")
    
    def is_complete(self) -> bool:
        """Check if the entire process is complete"""
        return self.checkpoint_data['completed']
    
    def clear(self):
        """Clear checkpoint (start fresh)"""
        self.checkpoint_data = self._create_empty_checkpoint()
        if os.path.exists(self.checkpoint_file):
            try:
                os.remove(self.checkpoint_file)
                logging.info("🔄 Checkpoint cleared - starting fresh")
            except Exception as e:
                logging.error(f"Error clearing checkpoint: {e}")
    
    def get_progress_summary(self) -> str:
        """Get a human-readable summary of progress"""
        if self.checkpoint_data['completed']:
            return "✅ Process completed"
        
        steps = self.checkpoint_data['steps_completed']
        months = steps['months_processed']
        
        summary_parts = []
        if steps['media_scan']:
            summary_parts.append("✓ Media scan")
        if steps['media_assignment']:
            summary_parts.append("✓ Media assignment")
        if months:
            summary_parts.append(f"✓ Months processed: {len(months)}/12")
        
        if not summary_parts:
            return "🔵 Not started"
        
        return " | ".join(summary_parts)
    
    def should_resume(self) -> bool:
        """
        Determine if we should resume from checkpoint or start fresh
        
        Returns:
            True if there's progress to resume, False to start fresh
        """
        if self.checkpoint_data['completed']:
            # Process was completed, ask user or start fresh
            return False
        
        steps = self.checkpoint_data['steps_completed']
        has_progress = (
            steps['media_scan'] or 
            steps['media_assignment'] or 
            len(steps['months_processed']) > 0
        )
        
        return has_progress
