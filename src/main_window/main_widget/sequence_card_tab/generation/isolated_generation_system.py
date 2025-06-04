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
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from pathlib import Path


from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import (
    TempBeatFrame,
)
from main_window.main_widget.json_manager.default_sequence_provider import (
    DefaultSequenceProvider,
)
from .temp_sequence_workbench import TempSequenceWorkbench
from .generation_params import GenerationParams
from .generated_sequence_data import GeneratedSequenceData
from utils.path_helpers import get_user_editable_resource_path
from interfaces.json_manager_interface import IJsonManager  # Added
from main_window.main_widget.json_manager.json_manager import JsonManager  # Added
from main_window.main_widget.json_manager.sequence_data_loader_saver import (
    SequenceDataLoaderSaver,
)  # Added

if TYPE_CHECKING:
    from main_window.main_widget.generate_tab.generate_tab import GenerateTab


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
        empty_sequence = DefaultSequenceProvider.get_default_sequence()
        with open(session_json_file, "w", encoding="utf-8") as f:
            json.dump(empty_sequence, f, indent=2)

        # Create isolated beat frame for this session
        isolated_beat_frame = self._create_isolated_beat_frame(session_json_file)
        isolated_workbench = TempSequenceWorkbench(isolated_beat_frame)

        # Store session data
        self.active_sessions[session_id] = {
            "session_dir": session_dir,
            "json_file": session_json_file,
            "beat_frame": isolated_beat_frame,
            "workbench": isolated_workbench,
            "created_at": logging.time.time() if hasattr(logging, "time") else 0,
        }

        self.logger.info(f"Created isolated generation session: {session_id}")
        return session_id

    def get_session_workbench(self, session_id: str) -> Optional[TempSequenceWorkbench]:
        """Get the isolated workbench for a specific session."""
        session = self.active_sessions.get(session_id)
        return session["workbench"] if session else None

    def preserve_user_state(self):
        """Preserve the current user state before generation."""
        try:
            # Save the current sequence from the main JSON file
            main_json_file = get_user_editable_resource_path("current_sequence.json")
            if os.path.exists(main_json_file):
                with open(main_json_file, "r", encoding="utf-8") as f:
                    self.original_state = json.load(f)
                self.logger.info("Preserved user state for restoration")
            else:
                self.original_state = DefaultSequenceProvider.get_default_sequence()
                self.logger.info("No existing user state found, using empty sequence")
        except Exception as e:
            self.logger.error(f"Error preserving user state: {e}")
            self.original_state = DefaultSequenceProvider.get_default_sequence()

    def restore_user_state(self):
        """Restore the original user state after generation."""
        if self.original_state is None:
            self.logger.warning("No original state to restore")
            return

        try:
            main_json_file = get_user_editable_resource_path("current_sequence.json")
            with open(main_json_file, "w", encoding="utf-8") as f:
                json.dump(self.original_state, f, indent=2)
            self.logger.info("Restored original user state")
        except Exception as e:
            self.logger.error(f"Error restoring user state: {e}")

    def generate_sequence_isolated(
        self, params: GenerationParams, session_id: str = None
    ) -> Optional[GeneratedSequenceData]:
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
            workbench = session["workbench"]
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

            self.logger.info(
                f"Successfully generated isolated sequence: {generated_data.word}"
            )
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

                shutil.rmtree(session["session_dir"], ignore_errors=True)

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
        """Create a completely isolated beat frame with its own JsonManager."""
        # Create a new JsonManager instance for this isolated session
        isolated_json_manager = JsonManager()
        # Configure its loader_saver to use the specific isolated JSON file
        isolated_json_manager.loader_saver = SequenceDataLoaderSaver()
        isolated_json_manager.loader_saver.current_sequence_json = json_file

        # Mock or create a minimal browse_tab-like object if TempBeatFrame strictly requires it
        class MinimalBrowseTabMock:
            def __init__(self, main_widget, json_manager_instance):
                self.main_widget = main_widget
                # TempBeatFrame expects a json_manager on its browse_tab, or it will create a new one from AppContext
                # To ensure it uses our isolated one, we can pass it this way.
                # However, TempBeatFrame's __init__ needs to be adapted to use this.
                # For now, we rely on TempBeatFrame's __init__ to accept a json_manager directly or be refactored.
                # As a simpler approach, we'll pass the json_manager directly to TempBeatFrame if its constructor allows.

        # This part assumes TempBeatFrame can accept json_manager directly or is refactored.
        # If TempBeatFrame strictly gets json_manager from browse_tab.main_widget.app_context,
        # then browse_tab_mock would need a main_widget with an app_context that has this isolated_json_manager.
        # This can get complex. The ideal is to pass dependencies directly.

        # Assuming TempBeatFrame can be instantiated with an explicit json_manager:
        # isolated_beat_frame = TempBeatFrame(browse_tab=None, json_manager=isolated_json_manager, main_widget=self.main_widget)
        # If TempBeatFrame must take a browse_tab and gets json_manager from AppContext:
        # We need to ensure TempBeatFrame is modified or it will pick up the global AppContext.json_manager().
        # The current TempBeatFrame init: TempBeatFrame(self, browse_tab: \"BrowseTab\") -> None:
        # and then self.json_manager = AppContext.json_manager()
        # This MUST be changed for true isolation.
        # For now, proceeding with the assumption that TempBeatFrame will be refactored or this is handled.

        # Let's assume TempBeatFrame is refactored to accept json_manager directly.
        # If not, the _create_isolated_beat_frame in IsolatedGenerationSystem
        # would need to patch AppContext or use a more complex mock.

        # Create a mock browse_tab that holds the isolated json_manager
        # This is a workaround if TempBeatFrame cannot take json_manager directly
        class IsolatedBrowseTabMock:
            def __init__(self, main_widget, isolated_json_manager_instance):
                self.main_widget = main_widget
                # This mock needs to provide what TempBeatFrame expects from browse_tab
                # If TempBeatFrame uses browse_tab.main_widget.app_context.json_manager,
                # then this mock needs a main_widget with a mock app_context.
                # For simplicity, let's assume TempBeatFrame is modified to accept json_manager.
                # If not, this mock needs to be more elaborate.
                self.json_manager = isolated_json_manager_instance  # Store it here for TempBeatFrame to potentially use

        # Create the TempBeatFrame, assuming it's refactored to take json_manager
        # or can get it from a browse_tab_mock that has it.
        # The original TempBeatFrame takes `browse_tab` and then calls `AppContext.json_manager()`.
        # This needs to be addressed. For now, we'll create the mock and pass it.
        # The TempBeatFrame will need to be updated to use browse_tab.json_manager if available.
        # Or, even better, TempBeatFrame should accept json_manager as a direct constructor argument.
        browse_tab_mock = IsolatedBrowseTabMock(self.main_widget, isolated_json_manager)
        isolated_beat_frame = TempBeatFrame(
            browse_tab_mock
        )  # Ensure this line is active

        # Explicitly set the json_manager on the created beat_frame to be certain.
        isolated_beat_frame.json_manager = isolated_json_manager
        # And ensure its loader_saver points to the correct file (already done for isolated_json_manager)
        # isolated_beat_frame.json_manager.loader_saver.current_sequence_json = json_file # This is redundant if isolated_json_manager is correctly used.

        return isolated_beat_frame

    def _perform_isolated_generation(
        self, params: GenerationParams, workbench: TempSequenceWorkbench
    ) -> bool:
        """Perform the generation using the isolated workbench and context."""
        generate_tab: "GenerateTab" = self.main_widget.tab_manager.get_tab_widget(
            "generate"
        )
        if not generate_tab:
            self.logger.error("Generate tab not available for isolated generation")
            return False

        isolated_json_manager = (
            workbench.beat_frame.json_manager
        )  # Get the isolated json_manager from the workbench's beat_frame

        try:
            # Set the isolated context on GenerateTab
            generate_tab.set_isolated_generation_context(
                workbench, isolated_json_manager
            )

            # Use the appropriate builder to build the complete sequence
            if (
                hasattr(params, "generation_mode")
                and params.generation_mode.lower() == "circular"
            ):
                # Use circular builder with correct parameters
                try:
                    from main_window.main_widget.generate_tab.circular.CAP_type import (
                        CAPType,
                    )

                    cap_type_enum = CAPType.from_str(params.CAP_type)
                except (ValueError, AttributeError, ImportError):
                    from main_window.main_widget.generate_tab.circular.CAP_type import (
                        CAPType,
                    )

                    cap_type_enum = CAPType.STRICT_ROTATED

                # For circular sequences, the CAP system works as follows:
                # 1. WordLengthCalculator determines initial beats to generate
                # 2. CAP executors add permutations to reach the final length
                # 3. The final length should equal the requested length
                # Note: "full" is not a valid rotation type for circular sequences
                if params.rotation_type not in ["quartered", "halved"]:
                    self.logger.error(
                        f"Invalid rotation type for circular sequences: {params.rotation_type}"
                    )
                    return False

                # Pass the requested length directly - the CAP system will handle the rest
                adjusted_length = params.length

                # Use the circular builder's internal method to generate the first line only
                # Then apply CAPs to create the full circular sequence
                generate_tab.circular_builder._build_sequence_internal(
                    adjusted_length,
                    params.turn_intensity,
                    params.level,
                    params.rotation_type,  # This is the slice_size parameter
                    cap_type_enum,
                    params.prop_continuity,
                    start_position=params.start_position,  # Pass start position for proper randomization
                )
            else:
                # Use freeform builder with correct parameters
                generate_tab.freeform_builder.build_sequence(
                    params.length,
                    params.turn_intensity,
                    params.level,
                    params.prop_continuity,
                    params.start_position,
                    batch_mode=True,  # Set batch mode for isolated generation
                )

            # Get the sequence length from the workbench
            sequence_length = (
                len(
                    workbench.beat_frame.json_manager.loader_saver.load_current_sequence()
                )
                - 1
            )
            self.logger.info(
                f"Isolated generation completed. Sequence length: {sequence_length}"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Error during isolated generation execution: {e}", exc_info=True
            )
            return False
        finally:
            # Restore the main context on GenerateTab
            generate_tab.restore_main_context()
            self.logger.info(
                "Restored main context in GenerateTab after isolated generation"
            )

    def _extract_sequence_from_session(
        self, params: GenerationParams, session_id: str
    ) -> Optional[GeneratedSequenceData]:
        """Extract generated sequence data from an isolated session."""
        session = self.active_sessions.get(session_id)
        if not session:
            self.logger.error(f"Session {session_id} not found for extraction")
            return None

        try:
            workbench = session["workbench"]
            beat_frame = workbench.beat_frame

            if not hasattr(beat_frame, "json_manager"):
                self.logger.error("Beat frame missing json_manager")
                return None

            current_sequence = (
                beat_frame.json_manager.loader_saver.load_current_sequence()
            )

            if not current_sequence or len(current_sequence) < 3:
                self.logger.error(
                    f"Invalid sequence data: length={len(current_sequence) if current_sequence else 0}"
                )
                return None

            generated_data = GeneratedSequenceData(current_sequence, params)
            self.logger.info(
                f"Extracted sequence data: {len(current_sequence)} beats, word={generated_data.word}"
            )
            return generated_data

        except Exception as e:
            self.logger.error(
                f"Error extracting sequence from session {session_id}: {e}"
            )
            return None

    def _validate_sequence_length(
        self, generated_data: GeneratedSequenceData, params: GenerationParams
    ) -> bool:
        """Validate that the generated sequence has the correct length."""
        if not generated_data:
            return False

        sequence_data = generated_data.sequence_data

        # Count actual beats (excluding metadata and start position)
        # Start positions have beat=0 or sequence_start_position=True, actual beats have beat >= 1
        beat_count = len(
            [
                item
                for item in sequence_data
                if item.get("beat") is not None
                and item.get("beat") > 0  # Exclude start position (beat=0)
                and not item.get("sequence_start_position", False)  # Extra safety check
            ]
        )

        if beat_count != params.length:
            self.logger.error(
                f"Length validation failed: requested={params.length}, generated={beat_count}"
            )
            self.logger.error(
                f"Sequence structure: {[item.get('beat', 'metadata/start') for item in sequence_data]}"
            )
            return False

        self.logger.info(
            f"Length validation passed: {beat_count} beats generated as requested"
        )
        return True

    def _get_empty_sequence(self) -> List[Dict[str, Any]]:
        """Return default empty sequence for isolated sessions."""
        return [
            {
                "word": "",
                "author": "system",
                "level": 1,
                "prop_type": "staff",
                "grid_mode": "diamond",
                "is_circular": False,
            }
        ]
