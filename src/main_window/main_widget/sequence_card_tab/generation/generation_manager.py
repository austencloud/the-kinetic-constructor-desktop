# src/main_window/main_widget/sequence_card_tab/generation/generation_manager.py
import logging
from typing import TYPE_CHECKING, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from .generation_params import GenerationParams
from .generated_sequence_data import GeneratedSequenceData
from .isolated_generation_system import IsolatedGenerationSystem
from .managers.generation_dependency_manager import GenerationDependencyManager
from .managers.sequence_generator import SequenceGenerator
from .managers.generation_workbench_manager import GenerationWorkbenchManager
from .managers.generation_validator import GenerationValidator
from .managers.generation_parameter_manager import GenerationParameterManager

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
        self.generated_sequences = []
        self.generation_in_progress = False
        self._current_batch_size = 1
        self.logger = logging.getLogger(__name__)

        # Initialize component managers
        self.dependency_manager = GenerationDependencyManager(self.main_widget)
        self.sequence_generator = SequenceGenerator(self.main_widget)
        self.workbench_manager = GenerationWorkbenchManager(self.main_widget)
        self.validator = GenerationValidator()
        self.parameter_manager = GenerationParameterManager()
        self.isolated_system = IsolatedGenerationSystem(self.main_widget)

        # Initialize dependencies
        self.dependency_manager.initialize_generate_tab()

    def is_available(self) -> bool:
        return self.dependency_manager.is_available()

    def generate_single_sequence(self, params: GenerationParams) -> bool:
        if self._should_block_generation():
            return False

        if not self._validate_generation_preconditions():
            return False

        try:
            self.generation_in_progress = True
            self.logger.info(
                f"Starting isolated single sequence generation with params: {params.__dict__}"
            )

            generated_data = self.isolated_system.generate_sequence_isolated(params)

            if generated_data:
                if not self.validator.validate_sequence_length(generated_data, params):
                    self.generation_failed.emit(
                        "Generated sequence length validation failed"
                    )
                    return False

                self.logger.info(
                    f"Successfully generated isolated sequence: {generated_data.word} "
                    f"(length: {len([item for item in generated_data.sequence_data if item.get('beat') is not None])})"
                )
                self.sequence_generated.emit(generated_data)
                return True
            else:
                self.generation_failed.emit("Isolated sequence generation failed")
                return False

        except Exception as e:
            self.logger.error(f"Generation error: {e}")
            self.generation_failed.emit(f"Generation error: {str(e)}")
            return False
        finally:
            self.generation_in_progress = False

    def generate_batch(self, params: GenerationParams, count: int) -> bool:
        if self._should_block_generation():
            return False

        if not self._validate_generation_preconditions():
            return False

        try:
            self.generation_in_progress = True
            self._current_batch_size = count

            self.logger.info(
                f"Starting batch generation: {count} sequences with base params: {params.__dict__}"
            )

            successful_generations = 0

            for i in range(count):
                self.batch_generation_progress.emit(i + 1, count)
                self.logger.info(f"Generating isolated sequence {i + 1}/{count}")

                session_id = self.isolated_system.create_isolated_session(
                    f"batch_{i+1}"
                )
                varied_params = self.parameter_manager.add_parameter_variation(
                    params, self._current_batch_size
                )

                self.logger.info(
                    f"Sequence {i + 1} varied params: {varied_params.__dict__}"
                )

                generated_data = self.isolated_system.generate_sequence_isolated(
                    varied_params, session_id
                )

                if generated_data:
                    if self.validator.validate_sequence_length(
                        generated_data, varied_params
                    ):
                        self.logger.info(
                            f"Successfully generated isolated sequence {i + 1}: {generated_data.word} "
                            f"(length: {len([item for item in generated_data.sequence_data if item.get('beat') is not None])})"
                        )

                        generated_data.session_id = session_id
                        generated_data.session_json_file = (
                            self.isolated_system.active_sessions[session_id][
                                "json_file"
                            ]
                        )

                        self.sequence_generated.emit(generated_data)
                        successful_generations += 1
                    else:
                        self.logger.error(
                            f"Length validation failed for sequence {i + 1}"
                        )
                        self.isolated_system.cleanup_session(session_id)
                else:
                    self.logger.error(f"Failed to generate isolated sequence {i + 1}")
                    self.isolated_system.cleanup_session(session_id)

                QApplication.processEvents()

            if successful_generations > 0:
                self.logger.info(
                    f"Batch generation completed: {successful_generations}/{count} sequences successful"
                )
                return True
            else:
                self.generation_failed.emit("No sequences were generated successfully")
                return False

        except Exception as e:
            self.logger.error(f"Batch generation error: {e}")
            self.generation_failed.emit(f"Batch generation error: {str(e)}")
            return False
        finally:
            self._current_batch_size = 1
            self.generation_in_progress = False

    def _should_block_generation(self) -> bool:
        if (
            hasattr(self.sequence_card_tab, "is_initializing")
            and self.sequence_card_tab.is_initializing
        ):
            self.logger.info(
                "BLOCKED: Generation request during sequence card tab initialization"
            )
            return True
        return False

    def _validate_generation_preconditions(self) -> bool:
        if not self.is_available():
            self.generation_failed.emit("Generate tab is not available")
            return False

        if self.generation_in_progress:
            self.generation_failed.emit("Generation already in progress")
            return False

        return True

    # Legacy API support
    def get_generated_sequences(self) -> List[GeneratedSequenceData]:
        return self.generated_sequences.copy()

    def add_generated_sequence(self, sequence_data: GeneratedSequenceData):
        self.generated_sequences.append(sequence_data)

    def clear_generated_sequences(self):
        self.generated_sequences.clear()

    def is_generating(self) -> bool:
        return self.generation_in_progress

    def cleanup_isolated_system(self):
        if hasattr(self, "isolated_system"):
            self.isolated_system.cleanup_all_sessions()

    def cleanup_sequence_session(self, sequence_data):
        if hasattr(sequence_data, "session_id") and hasattr(self, "isolated_system"):
            self.isolated_system.cleanup_session(sequence_data.session_id)
            self.logger.info(
                f"Cleaned up session {sequence_data.session_id} for sequence {sequence_data.word}"
            )

    def __del__(self):
        self.cleanup_isolated_system()
