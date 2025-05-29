"""
Isolated Generation System - Provides complete isolation between sequence generation and user work.

This system ensures that:
1. Sequence generation uses completely separate JSON files
2. Temporary beat frames are truly isolated from the main sequence workbench
3. No shared state contamination between generation and construct tab
4. Generated sequences match the exact requested length
"""

import os
import json
import tempfile
import logging
import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path

from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import TempBeatFrame
from .temp_sequence_workbench import TempSequenceWorkbench
from .generation_params import GenerationParams
from .generated_sequence_data import GeneratedSequenceData
from utils.path_helpers import get_user_editable_resource_path


class IsolatedGenerationSystem:
    """
    Provides complete isolation for sequence generation operations.
    
    This system ensures that generation operations cannot contaminate
    the user's current work in the construct tab or main sequence workbench.
    """
    
    def __init__(self, main_widget):
        self.main_widget = main_widget
        self.logger = logging.getLogger(__name__)
        
        # Create isolated temporary directory for generation
        self.temp_dir = tempfile.mkdtemp(prefix="sequence_generation_")
        self.logger.info(f"Created isolated generation directory: {self.temp_dir}")
        
        # Track active generation sessions
        self.active_sessions = {}
        
        # Store original state for restoration
        self.original_state = None
    
    def create_isolated_session(self, session_id: str = None) -> str:
        """
        Create a completely isolated generation session.
        
        Returns:
            session_id: Unique identifier for this generation session
        """
        if session_id is None:
            session_id = f"gen_session_{uuid.uuid4().hex[:8]}"
        
        session_dir = os.path.join(self.temp_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Create isolated JSON file for this session
        session_json_file = os.path.join(session_dir, "isolated_sequence.json")
        
        # Initialize with empty sequence
        empty_sequence = self._get_empty_sequence()
        with open(session_json_file, 'w', encoding='utf-8') as f:
            json.dump(empty_sequence, f, indent=2)
        
        # Create isolated beat frame for this session
        isolated_beat_frame = self._create_isolated_beat_frame(session_json_file)
        isolated_workbench = TempSequenceWorkbench(isolated_beat_frame)
        
        # Store session data
        self.active_sessions[session_id] = {
            'session_dir': session_dir,
            'json_file': session_json_file,
            'beat_frame': isolated_beat_frame,
            'workbench': isolated_workbench,
            'created_at': logging.time.time() if hasattr(logging, 'time') else 0
        }
        
        self.logger.info(f"Created isolated generation session: {session_id}")
        return session_id
    
    def get_session_workbench(self, session_id: str) -> Optional[TempSequenceWorkbench]:
        """Get the isolated workbench for a specific session."""
        session = self.active_sessions.get(session_id)
        return session['workbench'] if session else None
    
    def preserve_user_state(self):
        """Preserve the current user state before generation."""
        try:
            # Save the current sequence from the main JSON file
            main_json_file = get_user_editable_resource_path("current_sequence.json")
            if os.path.exists(main_json_file):
                with open(main_json_file, 'r', encoding='utf-8') as f:
                    self.original_state = json.load(f)
                self.logger.info("Preserved user state for restoration")
            else:
                self.original_state = self._get_empty_sequence()
                self.logger.info("No existing user state found, using empty sequence")
        except Exception as e:
            self.logger.error(f"Error preserving user state: {e}")
            self.original_state = self._get_empty_sequence()
    
    def restore_user_state(self):
        """Restore the original user state after generation."""
        if self.original_state is None:
            self.logger.warning("No original state to restore")
            return
        
        try:
            main_json_file = get_user_editable_resource_path("current_sequence.json")
            with open(main_json_file, 'w', encoding='utf-8') as f:
                json.dump(self.original_state, f, indent=2)
            self.logger.info("Restored original user state")
        except Exception as e:
            self.logger.error(f"Error restoring user state: {e}")
    
    def generate_sequence_isolated(self, params: GenerationParams, session_id: str = None) -> Optional[GeneratedSequenceData]:
        """
        Generate a sequence in complete isolation.
        
        Args:
            params: Generation parameters
            session_id: Optional session ID, creates new session if None
            
        Returns:
            GeneratedSequenceData if successful, None otherwise
        """
        if session_id is None:
            session_id = self.create_isolated_session()
        
        session = self.active_sessions.get(session_id)
        if not session:
            self.logger.error(f"Session {session_id} not found")
            return None
        
        try:
            # Preserve user state before generation
            self.preserve_user_state()
            
            # Perform generation in isolation
            workbench = session['workbench']
            success = self._perform_isolated_generation(params, workbench)
            
            if not success:
                self.logger.error("Isolated generation failed")
                return None
            
            # Extract generated sequence data
            generated_data = self._extract_sequence_from_session(params, session_id)
            
            # Validate sequence length
            if not self._validate_sequence_length(generated_data, params):
                self.logger.error("Generated sequence length validation failed")
                return None
            
            self.logger.info(f"Successfully generated isolated sequence: {generated_data.word}")
            return generated_data
            
        except Exception as e:
            self.logger.error(f"Error in isolated generation: {e}")
            return None
        finally:
            # Always restore user state
            self.restore_user_state()
    
    def cleanup_session(self, session_id: str):
        """Clean up a generation session."""
        session = self.active_sessions.get(session_id)
        if session:
            try:
                # Remove session directory
                import shutil
                shutil.rmtree(session['session_dir'], ignore_errors=True)
                
                # Remove from active sessions
                del self.active_sessions[session_id]
                
                self.logger.info(f"Cleaned up generation session: {session_id}")
            except Exception as e:
                self.logger.error(f"Error cleaning up session {session_id}: {e}")
    
    def cleanup_all_sessions(self):
        """Clean up all active generation sessions."""
        session_ids = list(self.active_sessions.keys())
        for session_id in session_ids:
            self.cleanup_session(session_id)
        
        # Remove the entire temp directory
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.logger.info("Cleaned up all generation sessions")
        except Exception as e:
            self.logger.error(f"Error cleaning up temp directory: {e}")
    
    def _create_isolated_beat_frame(self, json_file: str) -> TempBeatFrame:
        """Create a completely isolated beat frame."""
        class IsolatedBrowseTab:
            def __init__(self, main_widget, json_file):
                self.main_widget = main_widget
                self.isolated_json_file = json_file
        
        isolated_browse_tab = IsolatedBrowseTab(self.main_widget, json_file)
        isolated_beat_frame = TempBeatFrame(isolated_browse_tab)
        
        # Override the JSON file path to use our isolated file
        if hasattr(isolated_beat_frame, 'json_manager') and hasattr(isolated_beat_frame.json_manager, 'loader_saver'):
            isolated_beat_frame.json_manager.loader_saver.current_sequence_json = json_file
        
        return isolated_beat_frame
    
    def _perform_isolated_generation(self, params: GenerationParams, workbench: TempSequenceWorkbench) -> bool:
        """Perform the actual sequence generation in isolation."""
        try:
            # Get the generate tab
            generate_tab = self.main_widget.tab_manager.get_tab_widget("generate")
            if not generate_tab:
                self.logger.error("Generate tab not available")
                return False
            
            # Set the workbench as the current sequence workbench temporarily
            original_workbench = getattr(generate_tab, 'sequence_workbench', None)
            generate_tab.sequence_workbench = workbench
            
            try:
                # Perform generation based on mode
                if params.generation_mode == "freeform":
                    generate_tab.freeform_builder.build_sequence(
                        params.length,
                        params.turn_intensity,
                        params.level,
                        params.prop_continuity,
                        params.start_position,
                        batch_mode=True  # Use batch mode for better isolation
                    )
                else:
                    # Handle circular generation
                    from main_window.main_widget.generate_tab.circular.CAP_type import CAPType
                    cap_type_enum = CAPType.from_str(params.CAP_type)
                    
                    generate_tab.circular_builder.build_sequence(
                        params.length,
                        params.turn_intensity,
                        params.level,
                        params.rotation_type,
                        cap_type_enum,
                        params.prop_continuity
                    )
                
                return True
                
            finally:
                # Restore original workbench
                if original_workbench:
                    generate_tab.sequence_workbench = original_workbench
                
        except Exception as e:
            self.logger.error(f"Error in isolated generation: {e}")
            return False
    
    def _extract_sequence_from_session(self, params: GenerationParams, session_id: str) -> Optional[GeneratedSequenceData]:
        """Extract the generated sequence from an isolated session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        try:
            beat_frame = session['beat_frame']
            current_sequence = beat_frame.json_manager.loader_saver.load_current_sequence()
            
            if not current_sequence or len(current_sequence) < 3:
                self.logger.error(f"Invalid sequence data: length={len(current_sequence) if current_sequence else 0}")
                return None
            
            generated_data = GeneratedSequenceData(current_sequence, params)
            self.logger.info(f"Extracted sequence: {len(current_sequence)} elements, word={generated_data.word}")
            
            return generated_data
            
        except Exception as e:
            self.logger.error(f"Error extracting sequence from session: {e}")
            return None
    
    def _validate_sequence_length(self, generated_data: GeneratedSequenceData, params: GenerationParams) -> bool:
        """Validate that the generated sequence has the correct length."""
        if not generated_data:
            return False
        
        sequence_data = generated_data.sequence_data
        
        # Count actual beats (excluding metadata and start position)
        beat_count = len([item for item in sequence_data if item.get("beat") is not None])
        
        if beat_count != params.length:
            self.logger.error(f"Length mismatch: requested={params.length}, generated={beat_count}")
            return False
        
        self.logger.info(f"Length validation passed: {beat_count} beats generated as requested")
        return True
    
    def _get_empty_sequence(self) -> List[Dict[str, Any]]:
        """Get an empty sequence structure."""
        return [
            {
                "word": "",
                "author": "system",
                "level": 1,
                "prop_type": "staff",
                "grid_mode": "diamond",
                "is_circular": False
            }
        ]
    
    def __del__(self):
        """Cleanup when the system is destroyed."""
        self.cleanup_all_sessions()
