from PyQt6.QtCore import Qt
from typing import Dict
import logging

from ...image_generation_worker import ImageGenerationWorker


class WorkerManager:
    def __init__(self):
        self.image_workers: Dict[str, ImageGenerationWorker] = {}

    def create_worker(self, sequence_data, main_widget) -> ImageGenerationWorker:
        """Create and register a new image generation worker"""
        try:
            worker = ImageGenerationWorker(sequence_data, main_widget)
            self.image_workers[sequence_data.id] = worker
            return worker
        except Exception as e:
            logging.error(f"Error creating worker for {sequence_data.id}: {e}")
            raise

    def setup_worker_connections(
        self,
        worker: ImageGenerationWorker,
        image_generated_callback,
        image_failed_callback,
        diagnostic_callback,
        finished_callback,
    ) -> None:
        """Setup worker signal connections with error handling"""
        try:
            worker.image_generated.connect(
                image_generated_callback,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.image_failed.connect(
                image_failed_callback,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.diagnostic_info.connect(
                diagnostic_callback, Qt.ConnectionType.QueuedConnection
            )
            worker.finished.connect(
                lambda: finished_callback(worker),
                Qt.ConnectionType.QueuedConnection,
            )
        except Exception as e:
            logging.error(f"Error setting up worker connections: {e}")
            raise

    def get_worker(self, sequence_id: str) -> ImageGenerationWorker:
        """Get worker for a specific sequence"""
        return self.image_workers.get(sequence_id)

    def remove_worker(self, sequence_id: str) -> None:
        """Remove worker from tracking"""
        if sequence_id in self.image_workers:
            del self.image_workers[sequence_id]

    def cleanup_worker(self, worker: ImageGenerationWorker) -> None:
        """Safely cleanup a single worker"""
        try:
            # Find the sequence_id for this worker
            sequence_id = None
            for sid, w in self.image_workers.items():
                if w == worker:
                    sequence_id = sid
                    break

            if sequence_id:
                del self.image_workers[sequence_id]

            if worker.isRunning():
                worker.terminate()
                worker.wait(1000)
            worker.deleteLater()

        except Exception as e:
            logging.error(f"Error cleaning up worker: {e}")

    def cleanup_all_workers(self) -> None:
        """Cleanup all workers and reset state"""
        try:
            for worker in list(self.image_workers.values()):
                try:
                    if worker.isRunning():
                        worker.terminate()
                        worker.wait(1000)
                    worker.deleteLater()
                except Exception as e:
                    logging.warning(f"Error cleaning up worker: {e}")

            self.image_workers.clear()
            logging.info("Worker manager cleanup completed")

        except Exception as e:
            logging.error(f"Error during worker cleanup: {e}")

    def terminate_all_workers(self) -> None:
        """Forcefully terminate all running workers"""
        try:
            for worker in list(self.image_workers.values()):
                if worker.isRunning():
                    worker.terminate()
                    worker.wait(500)
        except Exception as e:
            logging.error(f"Error terminating workers: {e}")

    def get_worker_count(self) -> int:
        """Get the number of active workers"""
        return len(self.image_workers)

    def get_running_workers_count(self) -> int:
        """Get the number of currently running workers"""
        return sum(1 for worker in self.image_workers.values() if worker.isRunning())
