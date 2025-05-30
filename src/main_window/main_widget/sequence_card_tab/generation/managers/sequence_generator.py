import logging
import random
import time
from typing import TYPE_CHECKING, Optional

from ..generation_params import GenerationParams
from ..temp_sequence_workbench import TempSequenceWorkbench

if TYPE_CHECKING:
    from main_window.main_widget.generate_tab.generate_tab import GenerateTab
    from main_window.main_widget.main_widget import MainWidget


class SequenceGenerator:
    def __init__(self, main_widget: "MainWidget"):
        self.main_widget = main_widget
        self.logger = logging.getLogger(__name__)

    def generate_sequence(
        self,
        params: GenerationParams,
        generate_tab: "GenerateTab",
        temp_workbench: TempSequenceWorkbench,
        is_batch_mode: bool = False,
    ) -> bool:
        try:
            self._clear_json_state()
            self._setup_builders_with_workbench(generate_tab, temp_workbench)

            success = self._execute_generation(params, generate_tab, is_batch_mode)

            return success
        except Exception as e:
            self.logger.error(f"Error during sequence generation: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _clear_json_state(self):
        json_manager_instance = None
        if hasattr(self.main_widget, "app_context") and self.main_widget.app_context:
            json_manager_instance = self.main_widget.app_context.json_manager
        elif hasattr(self.main_widget, "json_manager"):
            json_manager_instance = self.main_widget.json_manager

        if json_manager_instance and hasattr(json_manager_instance, "loader_saver"):
            json_manager_instance.loader_saver.clear_current_sequence_file()
            self.logger.info(
                "Cleared global current_sequence.json for fresh generation"
            )
        else:
            self.logger.error(
                "Could not access JsonManager to clear current_sequence.json"
            )

    def _setup_builders_with_workbench(
        self, generate_tab: "GenerateTab", temp_workbench: TempSequenceWorkbench
    ):
        original_sequence_workbench = None
        if hasattr(generate_tab, "sequence_workbench"):
            original_sequence_workbench = generate_tab.sequence_workbench

        if hasattr(generate_tab, "freeform_builder"):
            if hasattr(generate_tab.freeform_builder, "sequence_workbench"):
                generate_tab.freeform_builder.sequence_workbench = temp_workbench
                self.logger.info("Set freeform_builder to use temporary workbench")

            if hasattr(generate_tab.freeform_builder, "main_widget"):
                if generate_tab.freeform_builder.main_widget != self.main_widget:
                    self.logger.warning(
                        "Freeform builder has different main_widget reference - fixing..."
                    )
                    generate_tab.freeform_builder.main_widget = self.main_widget
                    self.logger.info("Fixed freeform builder main_widget reference")

        if hasattr(generate_tab, "circular_builder"):
            if hasattr(generate_tab.circular_builder, "sequence_workbench"):
                generate_tab.circular_builder.sequence_workbench = temp_workbench
                self.logger.info("Set circular_builder to use temporary workbench")

            if hasattr(generate_tab.circular_builder, "main_widget"):
                if generate_tab.circular_builder.main_widget != self.main_widget:
                    self.logger.warning(
                        "Circular builder has different main_widget reference - fixing..."
                    )
                    generate_tab.circular_builder.main_widget = self.main_widget
                    self.logger.info("Fixed circular builder main_widget reference")

        return original_sequence_workbench

    def _execute_generation(
        self, params: GenerationParams, generate_tab: "GenerateTab", is_batch_mode: bool
    ) -> bool:
        random_seed = (
            int(time.time() * 1000000)
            + random.randint(0, 999999)
            + hash(str(params.__dict__)) % 1000000
        ) % 2147483647
        random.seed(random_seed)
        self.logger.info(f"Seeded random generator with: {random_seed}")

        if params.generation_mode == "freeform":
            return self._generate_freeform_sequence(params, generate_tab, is_batch_mode)
        else:
            return self._generate_circular_sequence(params, generate_tab)

    def _generate_freeform_sequence(
        self, params: GenerationParams, generate_tab: "GenerateTab", is_batch_mode: bool
    ) -> bool:
        self.logger.info(
            f"Building freeform sequence: length={params.length}, level={params.level}, start_position={params.start_position}"
        )

        generate_tab.freeform_builder.build_sequence(
            params.length,
            params.turn_intensity,
            params.level,
            params.prop_continuity,
            params.start_position,
            batch_mode=is_batch_mode,
        )

        self.logger.info("Freeform sequence generation completed successfully")
        return True

    def _generate_circular_sequence(
        self, params: GenerationParams, generate_tab: "GenerateTab"
    ) -> bool:
        try:
            from main_window.main_widget.generate_tab.circular.CAP_type import CAPType

            cap_type_enum = CAPType.from_str(params.CAP_type)
        except (ValueError, AttributeError):
            from main_window.main_widget.generate_tab.circular.CAP_type import CAPType

            cap_type_enum = CAPType.STRICT_ROTATED

        self.logger.info(
            f"Building circular sequence: length={params.length}, level={params.level}, CAP={cap_type_enum}"
        )

        generate_tab.circular_builder.build_sequence(
            params.length,
            params.turn_intensity,
            params.level,
            params.rotation_type,
            cap_type_enum,
            params.prop_continuity,
        )

        self.logger.info("Circular sequence generation completed successfully")
        return True
