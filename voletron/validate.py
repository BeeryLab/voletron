# Copyright 2022 Google LLC
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


import os

from voletron.parse_config import parse_validation
from voletron.util import format_time


def validate(tag_ids, out_dir, exp_name, trajectories, tag_id_to_name, validations):
    print("\nValidation:")
    print("-----------------------------")

    validations = [vv for vv in validations if vv.tag_id in tag_ids]

    with open(os.path.join(out_dir, exp_name + ".validate.csv"), "w") as f:
        f.write("Correct,Timestamp,AnimalID,Expected,Observed\n")
        correct = 0
        for v in validations:
            # Charitably use a 2-minute window
            actual = trajectories.get_locations_between(
                v.tag_id, v.timestamp - 30, v.timestamp + 90
            )
            ok = v.chamber in actual
            correct += ok

            f.write("{},{},{},{},{}\n".format(ok,format_time(v.timestamp),tag_id_to_name[v.tag_id], v.chamber, actual))

    print(
        "{} of {} ({:>6.2%}) validation points correct.".format(
            correct, len(validations), correct / len(validations)
        )
    )

