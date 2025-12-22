import os
from voletron.time_span_analyzer import TimeSpanAnalyzer
from voletron.types import Config

def write_pair_inclusive_cohabs(
    config: Config, out_dir: str, exp_name: str, analyzer: TimeSpanAnalyzer
):
    with open(os.path.join(out_dir, exp_name + ".pair-inclusive.cohab.csv"), "w") as f:
        f.write("Animal A,Animal B,dwells,seconds,test_duration\n")
        for codwell_aggregate in analyzer.get_pair_inclusive_stats():
            animal_a, animal_b = codwell_aggregate.tag_ids
            f.write(
                "{},{},{},{:.0f},{:.0f}\n".format(
                    config.tag_id_to_name[animal_a],
                    config.tag_id_to_name[animal_b],
                    codwell_aggregate.count,
                    codwell_aggregate.duration_seconds,
                    analyzer.duration,
                )
            )
