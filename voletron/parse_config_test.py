# Copyright 2022-2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from unittest.mock import patch, mock_open
import pytz
from voletron.parse_config import parse_config, parse_validation
from voletron.apparatus_config import load_apparatus_config

class TestParseConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_apparatus_config("apparatus_example.json")

    def test_parse_config_valid(self):
        mock_data = "AnimalName, TagId, StartChamber\nAnimal1, tag1, Cage1\nAnimal2, tag2, Cage2"
        with patch("builtins.open", mock_open(read_data=mock_data)):
            config = parse_config("dummy_path")
            self.assertEqual(config.tag_id_to_name["tag1"], "Animal1")
            self.assertEqual(config.tag_id_to_start_chamber["tag1"], "Cage1")
            self.assertEqual(config.tag_id_to_name["tag2"], "Animal2")

    def test_parse_config_invalid_header(self):
        mock_data = "Wrong, Header, Here\nAnimal1, tag1, Cage1"
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with self.assertRaises(ValueError):
                parse_config("dummy_path")

    def test_parse_config_invalid_chamber(self):
        mock_data = "AnimalName, TagId, StartChamber\nAnimal1, tag1, InvalidChamber"
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with self.assertRaises(ValueError):
                parse_config("dummy_path")

class TestParseValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_apparatus_config("apparatus_example.json")

    def test_parse_validation_valid(self):
        mock_data = "Timestamp, AnimalID, Chamber\n13.09.2020 12:00, Animal1, Cage1"
        name_to_tag = {"Animal1": "tag1"}
        timezone = pytz.timezone("UTC")
        
        with patch("builtins.open", mock_open(read_data=mock_data)):
            validations = parse_validation("dummy_path", name_to_tag, timezone)
            self.assertEqual(len(validations), 1)
            self.assertEqual(validations[0].tag_id, "tag1")
            self.assertEqual(validations[0].chamber, "Cage1")
            # 13.09.2020 12:00 UTC timestamp
            # 1599998400.0
            self.assertEqual(validations[0].timestamp, 1599998400.0)

    def test_parse_validation_unknown_animal(self):
        # Should just skip unknown animals and print a message
        mock_data = "Timestamp, AnimalID, Chamber\n13.09.2020 12:00, UnknownAnimal, Cage1"
        name_to_tag = {"Animal1": "tag1"}
        timezone = pytz.timezone("UTC")
        
        with patch("builtins.open", mock_open(read_data=mock_data)):
            validations = parse_validation("dummy_path", name_to_tag, timezone)
            self.assertEqual(len(validations), 0)

if __name__ == '__main__':
    unittest.main()
