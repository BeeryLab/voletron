import os
import csv
import json
from datetime import datetime, timedelta

# Configuration
# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(BASE_DIR, "experiment")
RAW_FILENAME = "raw_e2e.csv"
ANIMALS_FILENAME = "animals.csv"
VALIDATION_FILENAME = "validation.csv"
APPARATUS_FILENAME = "apparatus.json"
START_TIME = datetime(2022, 1, 1, 12, 0, 0)

# Animal Setup
ANIMALS = [
    {"name": "Animal_A", "tag": "111111111111111", "start": "CentralA"},
    {"name": "Animal_B", "tag": "222222222222222", "start": "CentralA"},
    {"name": "Animal_C", "tag": "333333333333333", "start": "CentralA"},
    {"name": "Animal_D", "tag": "444444444444444", "start": "CentralA"},
]

# Apparatus Spec
APPARATUS_SPEC = {
    "_comment": ["Simplified Apparatus for E2E Test"],
    "olcus_devices": {
        "0": {
            "0": {"tube": "Tube1", "cage": "CentralA"},
            "1": {"tube": "Tube1", "cage": "Cage1"},
            "2": {"tube": "Tube2", "cage": "CentralA"},
            "3": {"tube": "Tube2", "cage": "Cage2"},
            "4": {"tube": "Tube3", "cage": "CentralA"},
            "5": {"tube": "Tube3", "cage": "Cage3"}
        },
        "1": {
            "0": {"tube": "Tube4", "cage": "CentralA"},
            "1": {"tube": "Tube4", "cage": "Cage4"}
        }
    },
    "habitats": {
        "HabitatA": ["CentralA", "Cage1", "Tube1", "Cage2", "Tube2", "Cage3", "Tube3", "Cage4", "Tube4", "Error"]
    }
}

# Automatically generate LOCATIONS from APPARATUS_SPEC
LOCATIONS = {}
for dev_id, antennas in APPARATUS_SPEC["olcus_devices"].items():
    for ant_id, info in antennas.items():
        # Name format: "{tube}_{cage}" (e.g., Tube1_CentralA, Tube1_Cage1)
        name = f"{info['tube']}_{info['cage']}"
        LOCATIONS[name] = (int(dev_id), int(ant_id))

def write_apparatus():
    with open(os.path.join(DIR, APPARATUS_FILENAME), 'w') as f:
        json.dump(APPARATUS_SPEC, f, indent=4)

def write_animals():
    with open(os.path.join(DIR, ANIMALS_FILENAME), 'w') as f:
        f.write("AnimalName,TagId,StartChamber\n")
        for a in ANIMALS:
            f.write(f"{a['name']},{a['tag']},{a['start']}\n")

def write_validation():
    # 4 entries, 1 mismatch
    # Correct: A in Cage1 at T=100s (12:01:40)
    # Correct: C in Cage2 at T=100s (12:01:40)
    # Correct: A in Cage2 at T=400s (12:06:40)
    # Incorrect: B in Cage2 at T=400s (12:06:40) -> Actually in Cage1
    
    entries = [
        (START_TIME + timedelta(seconds=100), "Animal_A", "Cage1"), # Correct
        (START_TIME + timedelta(seconds=100), "Animal_C", "Cage2"), # Correct
        (START_TIME + timedelta(seconds=400), "Animal_A", "Cage2"), # Correct
        (START_TIME + timedelta(seconds=400), "Animal_B", "Cage2"), # Incorrect (Is in Cage1)
    ]
    
    with open(os.path.join(DIR, VALIDATION_FILENAME), 'w') as f:
        f.write("Timestamp,AnimalName,Chamber\n")
        for ts, name, chamber in entries:
            # Format: 01.01.2022 12:01
            ts_str = ts.strftime("%d.%m.%Y %H:%M")
            f.write(f"{ts_str},{name},{chamber}\n")

def write_raw_data():
    events = []
    
    # Map "A" -> tag, etc.
    animal_tags = {a["name"].split("_")[1]: a["tag"] for a in ANIMALS}
    
    def add_event(seconds_offset, animal_suffix, location_key):
        tag = animal_tags[animal_suffix]
        device, antenna = LOCATIONS[location_key]
        ts = START_TIME + timedelta(seconds=seconds_offset)
        # cantimestamp is just loose int, let's say 1000 * seconds
        cants = int(seconds_offset * 1000)
        events.append((cants, ts, device, antenna, tag))

    # --- BIN 1 (0 - 300s) ---
    # Setup: A & B to Cage 1, C to Cage 2, D to Cage 3
    # Just after start (T=1s)
    add_event(1.0, "A", "Tube1_CentralA") # A at CentralA
    add_event(2.0, "A", "Tube1_Cage1")    # A enters Cage1
    
    add_event(3.0, "B", "Tube1_CentralA") # B at CentralA
    add_event(4.0, "B", "Tube1_Cage1")    # B enters Cage1
    
    add_event(5.0, "C", "Tube2_CentralA") # C at CentralA
    add_event(6.0, "C", "Tube2_Cage2")    # C enters Cage2
    
    add_event(7.0, "D", "Tube3_CentralA") # D at CentralA
    add_event(8.0, "D", "Tube3_Cage3")    # D enters Cage3
    
    # Refresh reads at T=150s (mid-bin) to keep them alive
    add_event(150.0, "A", "Tube1_Cage1")
    add_event(151.0, "B", "Tube1_Cage1")
    add_event(152.0, "C", "Tube2_Cage2")
    add_event(153.0, "D", "Tube3_Cage3")

    # --- BIN 2 (300 - 600s) ---
    # A moves from Cage 1 to Cage 2 (Joins C)
    # T=310s
    add_event(310.0, "A", "Tube1_Cage1")    # A leaving Cage1
    add_event(312.0, "A", "Tube1_CentralA") # A in Central
    add_event(315.0, "A", "Tube2_CentralA") # A near Cage2
    add_event(318.0, "A", "Tube2_Cage2")    # A enters Cage2
    
    # Others stay put, refresh at T=450
    add_event(450.0, "B", "Tube1_Cage1") # B still alone in Cage1
    add_event(451.0, "C", "Tube2_Cage2") # C with A in Cage2
    add_event(452.0, "A", "Tube2_Cage2") # A with C in Cage2
    add_event(453.0, "D", "Tube3_Cage3") # D still alone in Cage3

    # --- BIN 3 (600 - 900s) ---
    # Everyone moves to Cage 4
    # T=610
    
    # A & C leave Cage 2
    add_event(610.0, "A", "Tube2_Cage2")
    add_event(612.0, "A", "Tube2_CentralA")
    add_event(611.0, "C", "Tube2_Cage2")
    add_event(613.0, "C", "Tube2_CentralA")
    
    # B leaves Cage 1
    add_event(615.0, "B", "Tube1_Cage1")
    add_event(617.0, "B", "Tube1_CentralA")

    # D leaves Cage 3
    add_event(620.0, "D", "Tube3_Cage3")
    add_event(622.0, "D", "Tube3_CentralA")
    
    # All enter Cage 4 around T=650
    add_event(650.0, "A", "Tube4_CentralA")
    add_event(652.0, "A", "Tube4_Cage4")
    
    add_event(651.0, "B", "Tube4_CentralA")
    add_event(653.0, "B", "Tube4_Cage4")
    
    add_event(654.0, "C", "Tube4_CentralA")
    add_event(656.0, "C", "Tube4_Cage4")
    
    add_event(655.0, "D", "Tube4_CentralA")
    add_event(657.0, "D", "Tube4_Cage4")

    # Write file
    with open(os.path.join(DIR, RAW_FILENAME), 'w') as f:
        f.write("cantimestamp;datetimestamp;deviceid;antennaID;data\n")
        for (cants, ts, device, antenna, tag) in events:
            # Format: 25.08.2020 15:04:56:974
            ts_str = ts.strftime("%d.%m.%Y %H:%M:%S:%f")[:-3]
            f.write(f"{cants};{ts_str};{device};{antenna};{tag}\n")

if __name__ == "__main__":
    os.makedirs(DIR, exist_ok=True)
    write_apparatus()
    write_animals()
    write_validation()
    write_raw_data()
    print(f"Generated test dataset in {DIR}")
