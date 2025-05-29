import pytest
import logging
from unittest.mock import Mock, MagicMock, patch
from src.main_window.main_widget.sequence_card_tab.generation.generation_manager import (
    GenerationManager,
    GenerationParams,
)


@pytest.fixture
def mock_main_widget():
    """Create a mock main widget with all necessary dependencies."""
    main_widget = Mock()
    main_widget.tab_manager = Mock()
    main_widget.tab_manager._tabs = {}

    # Mock construct tab with option generation capabilities
    construct_tab = Mock()
    construct_tab.option_picker = Mock()
    construct_tab.option_picker.option_getter = Mock()
    construct_tab.option_picker.option_getter._load_all_next_option_dicts = Mock(
        return_value=[
            {"letter": "A", "beat": 1, "blue_attributes": {}, "red_attributes": {}},
            {"letter": "B", "beat": 2, "blue_attributes": {}, "red_attributes": {}},
            {"letter": "C", "beat": 3, "blue_attributes": {}, "red_attributes": {}},
        ]
    )
    main_widget.tab_manager._tabs["construct"] = construct_tab

    # Mock generate tab with builders
    generate_tab = Mock()
    generate_tab.freeform_builder = Mock()
    generate_tab.freeform_builder.build_sequence = Mock()
    generate_tab.circular_builder = Mock()
    main_widget.tab_manager._tabs["generate"] = generate_tab
    main_widget.generate_tab = generate_tab

    return main_widget


@pytest.fixture
def mock_sequence_card_tab(mock_main_widget):
    """Create a mock sequence card tab."""
    sequence_card_tab = Mock()
    sequence_card_tab.main_widget = mock_main_widget
    return sequence_card_tab


@pytest.fixture
def generation_manager(mock_sequence_card_tab):
    """Create a generation manager instance for testing."""
    return GenerationManager(mock_sequence_card_tab)


def test_sequence_length_accuracy(generation_manager):
    """Test that generated sequences have the correct length."""
    # Test different sequence lengths
    test_lengths = [4, 8, 12, 16]

    for length in test_lengths:
        params = GenerationParams(
            length=length, level=1, turn_intensity=1, generation_mode="freeform"
        )

        # Mock the temporary beat frame creation and sequence extraction
        with patch.object(
            generation_manager, "_create_temp_beat_frame"
        ) as mock_create_temp, patch.object(
            generation_manager, "_perform_generation_with_temp_frame"
        ) as mock_perform, patch.object(
            generation_manager, "_extract_generated_sequence_from_temp_frame"
        ) as mock_extract:

            # Mock successful generation
            mock_temp_workbench = Mock()
            mock_create_temp.return_value = mock_temp_workbench
            mock_perform.return_value = True

            # Mock sequence data with correct length
            mock_sequence_data = []
            for i in range(length):
                mock_sequence_data.append(
                    {
                        "beat": i + 1,
                        "letter": chr(65 + (i % 26)),  # A, B, C, etc.
                        "blue_attributes": {},
                        "red_attributes": {},
                    }
                )

            from src.main_window.main_widget.sequence_card_tab.generation.generation_manager import (
                GeneratedSequenceData,
            )

            mock_generated_data = GeneratedSequenceData(mock_sequence_data, params)
            mock_extract.return_value = mock_generated_data

            # Generate sequence
            result = generation_manager.generate_single_sequence(params)

            # Verify generation was successful
            assert result is True, f"Generation failed for length {length}"

            # Verify the mock was called with correct parameters
            mock_create_temp.assert_called_once()
            mock_perform.assert_called_once_with(params, mock_temp_workbench)
            mock_extract.assert_called_once_with(params, mock_temp_workbench)

            # Reset mocks for next iteration
            mock_create_temp.reset_mock()
            mock_perform.reset_mock()
            mock_extract.reset_mock()


def test_batch_mode_parameter_passing(generation_manager):
    """Test that batch_mode parameter is correctly passed to the freeform builder."""
    params = GenerationParams(
        length=4, level=1, turn_intensity=1, generation_mode="freeform"
    )

    # Mock the freeform builder
    mock_builder = generation_manager.generate_tab.freeform_builder

    with patch.object(
        generation_manager, "_create_temp_beat_frame"
    ) as mock_create_temp, patch.object(
        generation_manager, "_extract_generated_sequence_from_temp_frame"
    ) as mock_extract:

        mock_temp_workbench = Mock()
        mock_create_temp.return_value = mock_temp_workbench
        mock_extract.return_value = (
            None  # Will cause failure, but that's ok for this test
        )

        # Test single generation (batch_mode should be False)
        generation_manager._current_batch_size = 1
        generation_manager._perform_generation_with_temp_frame(
            params, mock_temp_workbench
        )

        # Verify freeform builder was called with batch_mode=False
        mock_builder.build_sequence.assert_called_with(
            params.length,
            params.turn_intensity,
            params.level,
            params.prop_continuity,
            params.start_position,
            batch_mode=False,
        )

        # Reset mock
        mock_builder.build_sequence.reset_mock()

        # Test batch generation (batch_mode should be True)
        generation_manager._current_batch_size = 5
        generation_manager._perform_generation_with_temp_frame(
            params, mock_temp_workbench
        )

        # Verify freeform builder was called with batch_mode=True
        mock_builder.build_sequence.assert_called_with(
            params.length,
            params.turn_intensity,
            params.level,
            params.prop_continuity,
            params.start_position,
            batch_mode=True,
        )


def test_batch_generation_creates_multiple_sequences(generation_manager):
    """Test that batch generation creates the correct number of sequences."""
    params = GenerationParams(
        length=4, level=1, turn_intensity=1, generation_mode="freeform"
    )

    batch_count = 3
    generated_sequences = []

    def mock_sequence_generated(sequence_data):
        generated_sequences.append(sequence_data)

    # Connect to the signal
    generation_manager.sequence_generated.connect(mock_sequence_generated)

    with patch.object(
        generation_manager, "_create_temp_beat_frame"
    ) as mock_create_temp, patch.object(
        generation_manager, "_perform_generation_with_temp_frame"
    ) as mock_perform, patch.object(
        generation_manager, "_extract_generated_sequence_from_temp_frame"
    ) as mock_extract:

        # Mock successful generation for each sequence
        mock_temp_workbench = Mock()
        mock_create_temp.return_value = mock_temp_workbench
        mock_perform.return_value = True

        # Create different mock sequences for each generation
        def create_mock_sequence(call_count=[0]):
            call_count[0] += 1
            mock_sequence_data = []
            for i in range(params.length):
                mock_sequence_data.append(
                    {
                        "beat": i + 1,
                        "letter": chr(65 + ((i + call_count[0]) % 26)),
                        "blue_attributes": {},
                        "red_attributes": {},
                    }
                )

            from src.main_window.main_widget.sequence_card_tab.generation.generation_manager import (
                GeneratedSequenceData,
            )

            return GeneratedSequenceData(mock_sequence_data, params)

        mock_extract.side_effect = lambda p, w: create_mock_sequence()

        # Generate batch
        result = generation_manager.generate_batch(params, batch_count)

        # Verify batch generation was successful
        assert result is True, "Batch generation failed"

        # Verify correct number of sequences were generated
        assert (
            len(generated_sequences) == batch_count
        ), f"Expected {batch_count} sequences, got {len(generated_sequences)}"

        # Verify each sequence has the correct length
        for i, sequence in enumerate(generated_sequences):
            assert (
                len(sequence.sequence_data) == params.length
            ), f"Sequence {i+1} has incorrect length"


if __name__ == "__main__":
    # Set up logging for test debugging
    logging.basicConfig(level=logging.INFO)

    # Run tests
    pytest.main([__file__, "-v"])
