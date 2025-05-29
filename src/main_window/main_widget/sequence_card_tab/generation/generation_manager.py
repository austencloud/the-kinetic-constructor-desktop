# src/main_window/main_widget/sequence_card_tab/generation/generation_manager.py
import random
import logging
from typing import TYPE_CHECKING, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
import time
import copy

from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import (
    TempBeatFrame,
)
from .temp_sequence_workbench import TempSequenceWorkbench
from .generation_params import GenerationParams
from .generated_sequence_data import GeneratedSequenceData
from .isolated_generation_system import IsolatedGenerationSystem

if TYPE_CHECKING:
    from main_window.main_widget.sequence_card_tab.tab import SequenceCardTab


class GenerationManager(QObject):
    sequence_generated = pyqtSignal(object)
    generation_failed = pyqtSignal(str)
    batch_generation_progress = pyqtSignal(int, int)

    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        super().__init__()
        self.sequence_card_tab = sequence_card_tab
        self.main_widget = sequence_card_tab.main_widget
        self.generate_tab = None
        self.generated_sequences = []
        self.generation_in_progress = False
        self._current_batch_size = 1

        # Initialize isolated generation system for proper state isolation
        self.isolated_system = IsolatedGenerationSystem(self.main_widget)

        self._initialize_generate_tab()

    def _initialize_generate_tab(self):
        try:
            self._refresh_generate_tab_reference()
        except Exception as e:
            print(f"Error initializing generate tab reference: {e}")

    def _refresh_generate_tab_reference(self):
        try:
            if (
                hasattr(self.main_widget, "generate_tab")
                and self.main_widget.generate_tab is not None
            ):
                self.generate_tab = self.main_widget.generate_tab
                return self._ensure_all_dependencies()

            if hasattr(self.main_widget, "tab_manager"):
                tab_manager = self.main_widget.tab_manager
                if hasattr(tab_manager, "tabs") and "generate" in tab_manager.tabs:
                    self.generate_tab = tab_manager.tabs["generate"]
                    return self._ensure_all_dependencies()

                if hasattr(tab_manager, "_create_tab"):
                    print("Attempting to create generate tab...")
                    generate_tab = tab_manager._create_tab("generate")
                    if generate_tab:
                        self.generate_tab = generate_tab
                        print("Generate tab created successfully!")

                        if not self._ensure_construct_tab_available():
                            print(
                                "Warning: Could not ensure construct tab availability"
                            )

                        return self._ensure_all_dependencies()

            if self.generate_tab is None:
                print("Warning: Generate tab not available for sequence generation")
            return False
        except Exception as e:
            print(f"Error refreshing generate tab reference: {e}")
            return False

    def _ensure_construct_tab_available(self):
        try:
            if hasattr(self.main_widget, "tab_manager"):
                tab_manager = self.main_widget.tab_manager

                if hasattr(tab_manager, "tabs") and "construct" in tab_manager.tabs:
                    print("Construct tab already available")
                    return True

                if hasattr(tab_manager, "_create_tab"):
                    print(
                        "Attempting to create construct tab for generation dependencies..."
                    )
                    construct_tab = tab_manager._create_tab("construct")
                    if construct_tab:
                        print("Construct tab created successfully!")
                        return True
                    else:
                        print("Failed to create construct tab")
                        return False

            return False
        except Exception as e:
            print(f"Error ensuring construct tab availability: {e}")
            return False

    def _ensure_all_dependencies(self):
        try:
            if not self.generate_tab:
                return False

            if not hasattr(self.generate_tab, "freeform_builder") or not hasattr(
                self.generate_tab, "circular_builder"
            ):
                print("Warning: Generate tab missing sequence builders")
                return False

            construct_tab_available = False
            construct_tab = None

            if hasattr(self.main_widget, "tab_manager"):
                tab_manager = self.main_widget.tab_manager
                logging.info(f"Tab manager found: {tab_manager}")
                logging.info(
                    f"Available tabs: {list(tab_manager._tabs.keys()) if hasattr(tab_manager, '_tabs') else 'No _tabs attribute'}"
                )

                if hasattr(tab_manager, "_tabs") and "construct" in tab_manager._tabs:
                    construct_tab = tab_manager._tabs["construct"]
                    logging.info(f"Found construct tab: {type(construct_tab).__name__}")

                    if hasattr(construct_tab, "option_picker"):
                        option_picker = construct_tab.option_picker
                        logging.info(
                            f"Found option_picker: {type(option_picker).__name__}"
                        )

                        if hasattr(option_picker, "option_getter"):
                            option_getter = option_picker.option_getter
                            logging.info(
                                f"Found option_getter: {type(option_getter).__name__}"
                            )

                            if hasattr(option_getter, "_load_all_next_option_dicts"):
                                logging.info(
                                    "✅ All construct tab dependencies verified - option generation available"
                                )
                                construct_tab_available = True
                            else:
                                logging.error(
                                    "option_getter missing _load_all_next_option_dicts method"
                                )
                        else:
                            logging.error(
                                "option_picker missing option_getter attribute"
                            )
                    else:
                        logging.error("construct_tab missing option_picker attribute")
                else:
                    logging.error("construct tab not found in tab_manager._tabs")
            else:
                logging.error("main_widget missing tab_manager")

            if not construct_tab_available:
                logging.error(
                    "CRITICAL: Construct tab dependencies not available - sequence generation will produce identical sequences"
                )
                logging.error(
                    "The freeform builder requires construct_tab.option_picker.option_getter._load_all_next_option_dicts() to access sequence options"
                )
                logging.error(
                    "Without this, random.choice(option_dicts) will always choose from the same limited set"
                )
                return False

            print("All generation dependencies verified successfully!")
            return True

        except Exception as e:
            print(f"Error verifying generation dependencies: {e}")
            return False

    def is_available(self) -> bool:
        if self.generate_tab is None:
            self._refresh_generate_tab_reference()
        return self.generate_tab is not None

    def generate_single_sequence(self, params: GenerationParams) -> bool:
        # CRITICAL FIX: Prevent generation during initialization
        if (
            hasattr(self.sequence_card_tab, "is_initializing")
            and self.sequence_card_tab.is_initializing
        ):
            logging.info(
                "BLOCKED: Generation request during sequence card tab initialization"
            )
            return False

        if not self.is_available():
            self.generation_failed.emit("Generate tab is not available")
            return False

        if self.generation_in_progress:
            self.generation_failed.emit("Generation already in progress")
            return False

        try:
            self.generation_in_progress = True
            logging.info(
                f"Starting isolated single sequence generation with params: {params.__dict__}"
            )

            # Use isolated generation system for complete state isolation
            generated_data = self.isolated_system.generate_sequence_isolated(params)

            if generated_data:
                # Validate sequence length
                if not self._validate_generated_sequence_length(generated_data, params):
                    self.generation_failed.emit(
                        "Generated sequence length validation failed"
                    )
                    return False

                logging.info(
                    f"Successfully generated isolated sequence: {generated_data.word} (length: {len([item for item in generated_data.sequence_data if item.get('beat') is not None])})"
                )
                self.sequence_generated.emit(generated_data)
                return True
            else:
                self.generation_failed.emit("Isolated sequence generation failed")
                return False

        except Exception as e:
            logging.error(f"Generation error: {e}")
            self.generation_failed.emit(f"Generation error: {str(e)}")
            return False
        finally:
            self.generation_in_progress = False

    def generate_batch(self, params: GenerationParams, count: int) -> bool:
        # CRITICAL FIX: Prevent generation during initialization
        if (
            hasattr(self.sequence_card_tab, "is_initializing")
            and self.sequence_card_tab.is_initializing
        ):
            logging.info(
                "BLOCKED: Batch generation request during sequence card tab initialization"
            )
            return False

        if not self.is_available():
            self.generation_failed.emit("Generate tab is not available")
            return False

        if self.generation_in_progress:
            self.generation_failed.emit("Generation already in progress")
            return False

        try:
            self.generation_in_progress = True
            self._current_batch_size = count

            logging.info(
                f"Starting batch generation: {count} sequences with base params: {params.__dict__}"
            )

            successful_generations = 0

            for i in range(count):
                self.batch_generation_progress.emit(i + 1, count)
                logging.info(f"Generating isolated sequence {i + 1}/{count}")

                # Create isolated session for each sequence
                session_id = self.isolated_system.create_isolated_session(
                    f"batch_{i+1}"
                )

                varied_params = self._add_parameter_variation(params)
                logging.info(
                    f"Sequence {i + 1} varied params: {varied_params.__dict__}"
                )

                # Generate sequence in complete isolation
                generated_data = self.isolated_system.generate_sequence_isolated(
                    varied_params, session_id
                )

                if generated_data:
                    # Validate sequence length
                    if self._validate_generated_sequence_length(
                        generated_data, varied_params
                    ):
                        logging.info(
                            f"Successfully generated isolated sequence {i + 1}: {generated_data.word} (length: {len([item for item in generated_data.sequence_data if item.get('beat') is not None])})"
                        )

                        # Store session info in the generated data for later cleanup
                        generated_data.session_id = session_id
                        generated_data.session_json_file = (
                            self.isolated_system.active_sessions[session_id][
                                "json_file"
                            ]
                        )

                        self.sequence_generated.emit(generated_data)
                        successful_generations += 1
                    else:
                        logging.error(f"Length validation failed for sequence {i + 1}")
                        # Clean up failed session
                        self.isolated_system.cleanup_session(session_id)
                else:
                    logging.error(f"Failed to generate isolated sequence {i + 1}")
                    # Clean up failed session
                    self.isolated_system.cleanup_session(session_id)

                QApplication.processEvents()

            if successful_generations > 0:
                logging.info(
                    f"Batch generation completed: {successful_generations}/{count} sequences successful"
                )
                return True
            else:
                self.generation_failed.emit("No sequences were generated successfully")
                return False

        except Exception as e:
            logging.error(f"Batch generation error: {e}")
            self.generation_failed.emit(f"Batch generation error: {str(e)}")
            return False
        finally:
            self._current_batch_size = 1
            self.generation_in_progress = False

    def _create_temp_beat_frame(self) -> Optional[TempSequenceWorkbench]:
        try:

            class MockBrowseTab:
                def __init__(self, main_widget):
                    self.main_widget = main_widget

            mock_browse_tab = MockBrowseTab(self.main_widget)
            temp_beat_frame = TempBeatFrame(mock_browse_tab)
            temp_workbench = TempSequenceWorkbench(temp_beat_frame)

            logging.info(
                "Created fresh temporary beat frame wrapped for sequence builder compatibility"
            )
            return temp_workbench
        except Exception as e:
            logging.error(f"Error creating temporary beat frame: {e}")
            return None

    def _perform_generation_with_temp_frame(
        self, params: GenerationParams, temp_workbench: TempSequenceWorkbench
    ) -> bool:
        try:
            if not self._ensure_all_dependencies():
                logging.error("Generation failed: Required dependencies not available")
                return False

            json_manager_instance = None
            if (
                hasattr(self.main_widget, "app_context")
                and self.main_widget.app_context
            ):
                json_manager_instance = self.main_widget.app_context.json_manager
            elif hasattr(self.main_widget, "json_manager"):
                json_manager_instance = self.main_widget.json_manager

            if json_manager_instance and hasattr(json_manager_instance, "loader_saver"):
                json_manager_instance.loader_saver.clear_current_sequence_file()
                logging.info(
                    "Cleared global current_sequence.json for fresh generation in GenerationManager."
                )
            else:
                logging.error(
                    "GenerationManager: Could not access JsonManager to clear current_sequence.json. Generation might be flawed."
                )

            original_sequence_workbench = None
            if hasattr(self.generate_tab, "sequence_workbench"):
                original_sequence_workbench = self.generate_tab.sequence_workbench

            if hasattr(self.generate_tab, "freeform_builder"):
                if hasattr(self.generate_tab.freeform_builder, "sequence_workbench"):
                    self.generate_tab.freeform_builder.sequence_workbench = (
                        temp_workbench
                    )
                    logging.info("Set freeform_builder to use temporary workbench")

                if hasattr(self.generate_tab.freeform_builder, "main_widget"):
                    if (
                        self.generate_tab.freeform_builder.main_widget
                        != self.main_widget
                    ):
                        logging.warning(
                            "Freeform builder has different main_widget reference - fixing..."
                        )
                        self.generate_tab.freeform_builder.main_widget = (
                            self.main_widget
                        )
                        logging.info("Fixed freeform builder main_widget reference")

            if hasattr(self.generate_tab, "circular_builder"):
                if hasattr(self.generate_tab.circular_builder, "sequence_workbench"):
                    self.generate_tab.circular_builder.sequence_workbench = (
                        temp_workbench
                    )
                    logging.info("Set circular_builder to use temporary workbench")

                if hasattr(self.generate_tab.circular_builder, "main_widget"):
                    if (
                        self.generate_tab.circular_builder.main_widget
                        != self.main_widget
                    ):
                        logging.warning(
                            "Circular builder has different main_widget reference - fixing..."
                        )
                        self.generate_tab.circular_builder.main_widget = (
                            self.main_widget
                        )
                        logging.info("Fixed circular builder main_widget reference")

            try:
                random_seed = (
                    int(time.time() * 1000000)
                    + random.randint(0, 999999)
                    + hash(str(params.__dict__)) % 1000000
                ) % 2147483647
                random.seed(random_seed)
                logging.info(f"Seeded random generator with: {random_seed}")

                if params.generation_mode == "freeform":
                    logging.info(
                        f"Building freeform sequence: length={params.length}, level={params.level}, start_position={params.start_position}"
                    )
                    is_batch_mode = (
                        hasattr(self, "_current_batch_size")
                        and getattr(self, "_current_batch_size", 1) > 1
                    )

                    self.generate_tab.freeform_builder.build_sequence(
                        params.length,
                        params.turn_intensity,
                        params.level,
                        params.prop_continuity,
                        params.start_position,
                        batch_mode=is_batch_mode,
                    )
                else:
                    try:
                        from main_window.main_widget.generate_tab.circular.CAP_type import (
                            CAPType,
                        )

                        cap_type_enum = CAPType.from_str(params.CAP_type)
                    except (ValueError, AttributeError):
                        cap_type_enum = CAPType.STRICT_ROTATED

                    logging.info(
                        f"Building circular sequence: length={params.length}, level={params.level}, CAP={cap_type_enum}"
                    )
                    self.generate_tab.circular_builder.build_sequence(
                        params.length,
                        params.turn_intensity,
                        params.level,
                        params.rotation_type,
                        cap_type_enum,
                        params.prop_continuity,
                    )

                logging.info("Sequence generation completed successfully")
                return True

            finally:
                if original_sequence_workbench:
                    if hasattr(self.generate_tab, "freeform_builder") and hasattr(
                        self.generate_tab.freeform_builder, "sequence_workbench"
                    ):
                        self.generate_tab.freeform_builder.sequence_workbench = (
                            original_sequence_workbench
                        )
                    if hasattr(self.generate_tab, "circular_builder") and hasattr(
                        self.generate_tab.circular_builder, "sequence_workbench"
                    ):
                        self.generate_tab.circular_builder.sequence_workbench = (
                            original_sequence_workbench
                        )

        except Exception as e:
            logging.error(f"Error during sequence generation: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _extract_generated_sequence_from_temp_frame(
        self, params: GenerationParams, temp_workbench: TempSequenceWorkbench
    ) -> Optional[GeneratedSequenceData]:
        try:
            temp_beat_frame = temp_workbench.beat_frame

            if not hasattr(temp_beat_frame, "json_manager"):
                logging.error("Temporary beat frame missing json_manager")
                return None

            current_sequence = (
                temp_beat_frame.json_manager.loader_saver.load_current_sequence()
            )

            if not current_sequence or len(current_sequence) < 3:
                logging.error(
                    f"Invalid sequence data: length={len(current_sequence) if current_sequence else 0}"
                )
                return None

            generated_data = GeneratedSequenceData(current_sequence, params)
            logging.info(
                f"Extracted sequence data: {len(current_sequence)} beats, word={generated_data.word}"
            )

            return generated_data

        except Exception as e:
            logging.error(f"Error extracting generated sequence: {e}")
            return None

    def _add_parameter_variation(
        self, base_params: GenerationParams
    ) -> GenerationParams:
        consistent_params = copy.deepcopy(base_params)

        # For batch generation, always use random start positions to ensure natural variation
        # Even if user selected a specific start position for single generation
        if self._current_batch_size > 1:
            consistent_params.start_position = None
            logging.info(
                f"Batch generation: forcing random start positions for natural variation"
            )

        logging.info(
            f"Using consistent parameters for all sequences in batch: {consistent_params.__dict__}"
        )
        return consistent_params

    def get_generated_sequences(self) -> List[GeneratedSequenceData]:
        return self.generated_sequences.copy()

    def add_generated_sequence(self, sequence_data: GeneratedSequenceData):
        self.generated_sequences.append(sequence_data)

    def clear_generated_sequences(self):
        self.generated_sequences.clear()

    def is_generating(self) -> bool:
        return self.generation_in_progress

    def _validate_generated_sequence_length(
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
            logging.error(
                f"Length validation failed: requested={params.length}, generated={beat_count}"
            )
            logging.error(
                f"Sequence structure: {[item.get('beat', 'metadata/start') for item in sequence_data]}"
            )
            return False

        logging.info(
            f"Length validation passed: {beat_count} beats generated as requested"
        )
        return True

    def cleanup_isolated_system(self):
        """Clean up the isolated generation system."""
        if hasattr(self, "isolated_system"):
            self.isolated_system.cleanup_all_sessions()

    def cleanup_sequence_session(self, sequence_data):
        """Clean up the session for a specific generated sequence after image generation."""
        if hasattr(sequence_data, "session_id") and hasattr(self, "isolated_system"):
            self.isolated_system.cleanup_session(sequence_data.session_id)
            logging.info(
                f"Cleaned up session {sequence_data.session_id} for sequence {sequence_data.word}"
            )

    def __del__(self):
        """Cleanup when the generation manager is destroyed."""
        self.cleanup_isolated_system()
