import os
from typing import List, Tuple
from PyQt6.QtWidgets import QApplication
from .file_operations_manager import FileOperationsManager
from .metadata_manager import MetadataManager
from .memory_manager import MemoryManager


class BatchProcessingManager:
    def __init__(
        self,
        memory_manager: MemoryManager,
        file_ops: FileOperationsManager,
        metadata_manager: MetadataManager,
    ):
        self.memory_manager = memory_manager
        self.file_ops = file_ops
        self.metadata_manager = metadata_manager
        self.cancel_requested = False

    def count_total_sequences(
        self, dictionary_path: str, word_folders: List[str]
    ) -> int:
        total = 0
        for word in word_folders:
            word_path = os.path.join(dictionary_path, word)
            sequences = self.file_ops.get_sequences_in_word(word_path)
            total += len(sequences)
        return total

    def get_all_sequences(
        self, word_folders: List[str], dictionary_path: str
    ) -> List[Tuple[str, str]]:
        all_sequences = []
        for word in word_folders:
            word_path = os.path.join(dictionary_path, word)
            sequences = self.file_ops.get_sequences_in_word(word_path)
            for sequence_file in sequences:
                all_sequences.append((word, sequence_file))
        return all_sequences

    def process_sequence_batch(
        self,
        all_sequences: List[Tuple[str, str]],
        dictionary_path: str,
        export_path: str,
        start_index: int,
        end_index: int,
        sequence_processor,
        memory_check_interval: int,
    ) -> Tuple[int, int, int]:
        batch_sequences = all_sequences[start_index:end_index]
        regenerated_count = 0
        skipped_count = 0
        failed_count = 0
        processed_count = 0

        for word, sequence_file in batch_sequences:
            if self.cancel_requested:
                break

            word_path = os.path.join(dictionary_path, word)
            sequence_path = os.path.join(word_path, sequence_file)

            word_export_path = os.path.join(export_path, word)
            self.file_ops.ensure_directory_exists(word_export_path)
            output_path = os.path.join(word_export_path, sequence_file)

            if processed_count % memory_check_interval == 0:
                self.memory_manager.check_and_manage_memory()

            QApplication.processEvents()

            needs_regeneration, reason = self.file_ops.check_regeneration_needed(
                sequence_path, output_path
            )

            if needs_regeneration:
                success = sequence_processor(sequence_path, output_path)
                if success:
                    regenerated_count += 1
                else:
                    failed_count += 1
            else:
                skipped_count += 1

            processed_count += 1

        return regenerated_count, skipped_count, failed_count

    def cancel_processing(self):
        self.cancel_requested = True

    def reset_cancel_flag(self):
        self.cancel_requested = False
