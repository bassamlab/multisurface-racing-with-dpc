"""Summarize the NMPC weight tuning (lap error as in Table I: median per 2 m progress bin, averaged over the lap) and select a setting:
the lowest lap lateral error among the settings that complete all laps in every run."""
import glob
import json
import os
import re
import sys

import numpy as np
import yaml


RESULTS = sys.argv[1] if len(sys.argv) > 1 else "evaluation/02_tracking/results/nmpc_weight_sensitivity"
LAPS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
WAYPOINTS = np.loadtxt(yaml.safe_load(open("configs/config_l_shape.yaml"))["wpt_path"], delimiter=";", skiprows=3)
N_BINS = int(np.ceil(WAYPOINTS[-1, 0] / 2.0))


def lap_error(files):
    bins = [[] for _ in range(N_BINS)]
    completed, all_completed = 0, True
    for path in files:
        data = json.load(open(path))
        lap = np.asarray(data["lap_n"], float)
        progress = np.asarray(data["track_progress"], float)
        error = np.asarray(data["tracking_error"], float)
        completed += max(int(np.nanmax(lap)) - 1, 0)
        all_completed &= int(np.nanmax(lap)) >= LAPS
        for index in np.where(lap >= 1)[0]:
            bins[min(int(progress[index] // 2.0), N_BINS - 1)].append(error[index])
    profile = np.asarray([np.median(values) if values else np.nan for values in bins])
    return 100.0 * float(np.nanmean(profile)) if completed else float("nan"), completed, all_completed


summary = []
pattern = re.compile(r"_qlat([0-9p]+)_rsr([0-9p]+)_s[0-9]+$")
for label in sorted({pattern.search(p).groups() for p in glob.glob(os.path.join(RESULTS, "log_nmpc_eval_l_shape_sensitivity_*"))}):
    files = sorted(glob.glob(os.path.join(RESULTS, f"log_nmpc_eval_l_shape_sensitivity_qlat{label[0]}_rsr{label[1]}_s*")))
    error_cm, laps, ok = lap_error(files)
    summary.append({"q_lat": float(label[0].replace("p", ".")), "r_steering_rate": float(label[1].replace("p", ".")),
                    "runs": len(files), "evaluated_laps": laps, "all_laps_completed": bool(ok), "lateral_error_cm": error_cm})
summary.sort(key=lambda row: (row["q_lat"], row["r_steering_rate"]))
for row in summary:
    print(f"q_lat={row['q_lat']:>5.1f}, r_steering_rate={row['r_steering_rate']:>6.1f}: {row['lateral_error_cm']:.2f} cm over "
          f"{row['evaluated_laps']} evaluated laps{'' if row['all_laps_completed'] else ' (left the track)'}")
valid = [row for row in summary if row["all_laps_completed"]]
selected = min(valid, key=lambda row: row["lateral_error_cm"]) if valid else None
if selected:
    print(f"selected: q_lat={selected['q_lat']}, r_steering_rate={selected['r_steering_rate']}")
with open(os.path.join(RESULTS, "summary.json"), "w") as file:
    json.dump({"settings": summary, "selected": selected}, file, indent=2)
