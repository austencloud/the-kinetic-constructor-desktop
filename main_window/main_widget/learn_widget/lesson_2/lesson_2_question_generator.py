import random
from typing import TYPE_CHECKING

from Enums.letters import Letter

if TYPE_CHECKING:
    from .lesson_2_widget import Lesson2Widget


class Lesson2QuestionGenerator:
    """Generates questions for Lesson 2 (letter to pictograph matching)."""

    def __init__(self, lesson_2_widget: "Lesson2Widget") -> None:
        self.lesson_2_widget = lesson_2_widget
        self.main_widget = lesson_2_widget.main_widget
        self.previous_pictographs = set()
        self.previous_letter = None  # Track the previously used letter

    def generate_question(self):
        """Generate a question and update the question and answer widgets."""
        correct_letter, correct_pictograph = self._get_random_correct_pictograph()

        # Display the question
        self.lesson_2_widget.question_widget.display_question(
            "Choose the pictograph for:", correct_letter.value
        )

        # Generate the answers and display them
        pictographs = self._get_shuffled_pictographs(correct_pictograph)
        self.lesson_2_widget.answers_widget.display_answers(
            pictographs, correct_pictograph, self.lesson_2_widget.check_answer
        )

    def _get_random_correct_pictograph(self) -> tuple[Letter, dict]:
        """Retrieve a random correct letter and its corresponding pictograph, avoiding repetition."""
        # Get a list of available letters excluding the previous one
        available_letters = [
            letter for letter in self.main_widget.letters.keys() if letter != self.previous_letter
        ]

        correct_letter = random.choice(available_letters)
        correct_pictograph = random.choice(self.main_widget.letters[correct_letter])

        # Update the previous letter to the current one
        self.previous_letter = correct_letter
        return correct_letter, correct_pictograph

    def _get_shuffled_pictographs(self, correct_pictograph):
        """Generate and shuffle the correct and wrong pictographs."""
        wrong_pictographs = self.generate_wrong_answers(
            correct_pictograph["letter"]
        )
        pictographs = [correct_pictograph] + wrong_pictographs
        pictographs = [correct_pictograph] + wrong_pictographs
        assert correct_pictograph in pictographs, "Correct answer is missing from options"
        random.shuffle(pictographs)

        return pictographs

    def generate_wrong_answers(self, correct_letter: str) -> list[dict]:
        """Generate three random wrong pictographs, ensuring each has a different letter."""
        available_letters = self._get_available_letters(correct_letter)
        wrong_pictographs = []

        while len(wrong_pictographs) < 3:
            letter, pictograph_dict = self._get_random_pictograph(available_letters)

            if not self._is_duplicate_pictograph(letter, pictograph_dict):
                wrong_pictographs.append(pictograph_dict)
                available_letters.remove(letter)

        return wrong_pictographs

    def _get_available_letters(self, correct_letter: str) -> list[str]:
        """Get the available letters excluding the correct letter."""
        return [
            letter for letter in self.main_widget.letters if letter != correct_letter
        ]

    def _get_random_pictograph(self, available_letters: list[str]) -> tuple[str, dict]:
        """Choose a random letter and a corresponding pictograph."""
        letter = random.choice(available_letters)
        pictograph_dict = random.choice(self.main_widget.letters[letter])
        return letter, pictograph_dict

    def _is_duplicate_pictograph(self, letter: str, pictograph_dict: dict) -> bool:
        """Check if a pictograph has already been used."""
        pictograph_key = (
            self.main_widget.pictograph_key_generator.generate_pictograph_key(
                pictograph_dict
            )
        )
        if pictograph_key in self.previous_pictographs:
            return True

        self.previous_pictographs.add(pictograph_key)
        return False
