from copy import deepcopy
from typing import TYPE_CHECKING, Optional
import pandas as pd
from enums.letter.letter import Letter

from data.constants import (
    BLUE,
    BLUE_ATTRS,
    END_LOC,
    END_POS,
    IN,
    LETTER,
    MOTION_TYPE,
    PROP_ROT_DIR,
    RED,
    RED_ATTRS,
    START_LOC,
    START_ORI,
    START_POS,
    TURNS,
)
from utils.path_helpers import get_data_path

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class PictographDataLoader:
    def __init__(self, main_widget: "MainWidget") -> None:
        self.main_widget = main_widget

    def load_pictograph_dataset(self) -> dict[Letter, list[dict]]:
        diamond_csv_path = get_data_path("DiamondPictographDataframe.csv")
        box_csv_path = get_data_path("BoxPictographDataframe.csv")
        diamond_df = pd.read_csv(diamond_csv_path)
        box_df = pd.read_csv(box_csv_path)
        combined_df = pd.concat([diamond_df, box_df], ignore_index=True)
        combined_df = combined_df.sort_values(by=[LETTER, START_POS, END_POS])
        combined_df = self.add_turns_and_ori_to_pictograph_data(combined_df)
        combined_df = self.restructure_dataframe_for_new_json_format(combined_df)
        letters = {
            self.get_letter_enum_by_value(letter_str): combined_df[
                combined_df[LETTER] == letter_str
            ].to_dict(orient="records")
            for letter_str in combined_df[LETTER].unique()
        }
        self._convert_turns_str_to_int_or_float(letters)
        return letters

    def _convert_turns_str_to_int_or_float(self, letters):
        for letter in letters:
            for motion in letters[letter]:
                motion[BLUE_ATTRS][TURNS] = int(motion[BLUE_ATTRS][TURNS])
                motion[RED_ATTRS][TURNS] = int(motion[RED_ATTRS][TURNS])

    def add_turns_and_ori_to_pictograph_data(self, df: pd.DataFrame) -> pd.DataFrame:
        for index, row in df.iterrows():
            df.at[index, "blue_turns"] = 0
            df.at[index, "red_turns"] = 0
            df.at[index, "blue_start_ori"] = IN
            df.at[index, "red_start_ori"] = IN
        return df

    def restructure_dataframe_for_new_json_format(
        self, df: pd.DataFrame
    ) -> pd.DataFrame:
        def nest_attributes(row, color_prefix):
            return {
                MOTION_TYPE: row[f"{color_prefix}_motion_type"],
                START_ORI: row[f"{color_prefix}_start_ori"],
                PROP_ROT_DIR: row[f"{color_prefix}_prop_rot_dir"],
                START_LOC: row[f"{color_prefix}_start_loc"],
                END_LOC: row[f"{color_prefix}_end_loc"],
                TURNS: row[f"{color_prefix}_turns"],
            }

        df[BLUE_ATTRS] = df.apply(lambda row: nest_attributes(row, BLUE), axis=1)
        df[RED_ATTRS] = df.apply(lambda row: nest_attributes(row, RED), axis=1)
        blue_columns = [
            "blue_motion_type",
            "blue_prop_rot_dir",
            "blue_start_loc",
            "blue_end_loc",
            "blue_turns",
            "blue_start_ori",
        ]
        red_columns = [
            "red_motion_type",
            "red_prop_rot_dir",
            "red_start_loc",
            "red_end_loc",
            "red_turns",
            "red_start_ori",
        ]
        df = df.drop(columns=blue_columns + red_columns)
        return df

    @staticmethod
    def get_letter_enum_by_value(letter_value: str) -> Letter:
        for letter in Letter.__members__.values():
            if letter.value == letter_value:
                return letter
        raise ValueError(f"No matching Letters enum for value: {letter_value}")

    def find_pictograph_data(self, simplified_dict: dict) -> Optional[dict]:
        from enums.letter.letter import Letter

        target_letter = next(
            (l for l in Letter if l.value == simplified_dict[LETTER]), None
        )
        if not target_letter:
            print(
                f"Warning: Letter '{simplified_dict['letter']}' not found in Letter Enum."
            )
            return None

        letter_dicts = self.main_widget.pictograph_dataset.get(target_letter, [])
        for pdict in letter_dicts:
            if (
                pdict.get(START_POS) == simplified_dict[START_POS]
                and pdict.get(END_POS) == simplified_dict[END_POS]
                and pdict.get(BLUE_ATTRS, {}).get(MOTION_TYPE)
                == simplified_dict["blue_motion_type"]
                and pdict.get(RED_ATTRS, {}).get(MOTION_TYPE)
                == simplified_dict["red_motion_type"]
            ):
                return deepcopy(pdict)
        return None
