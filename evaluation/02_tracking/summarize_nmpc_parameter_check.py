"""Summarize whether each NMPC tire-parameter set completes the requested laps and its lap error (as in Table I: median per
2 m progress bin over the laps after the first, averaged over the lap)."""
import glob
import json
import os
import sys

import numpy as np
import yaml


RESULTS = sys.argv[1] if len(sys.argv) > 1 else "evaluation/02_tracking/results/nmpc_parameter_check"
REQUESTED_LAPS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
WAYPOINTS = np.loadtxt(yaml.safe_load(open("configs/config_l_shape.yaml"))["wpt_path"], delimiter=";", skiprows=3)
N_BINS = int(np.ceil(WAYPOINTS[-1, 0] / 2.0))
summary = []
found = {os.path.basename(p)[len("log_nmpc_eval_l_shape_param_"):].rsplit("_s", 1)[0]
         for p in glob.glob(os.path.join(RESULTS, "log_nmpc_eval_l_shape_param_*"))}
for setting in sorted(found):
    runs, bins = [], [[] for _ in range(N_BINS)]
    for path in sorted(glob.glob(os.path.join(RESULTS, f"log_nmpc_eval_l_shape_param_{setting}_s*"))):
        data = json.load(open(path))
        laps = int(np.nanmax(np.asarray(data["lap_n"], float)))
        error = np.asarray(data["tracking_error"], float)
        progress = np.asarray(data["track_progress"], float)
        for index in np.where(np.asarray(data["lap_n"], float) >= 1)[0]:
            bins[min(int(progress[index] // 2.0), N_BINS - 1)].append(error[index])
        runs.append({
            "file": os.path.basename(path),
            "completed_laps": laps,
            "left_track": bool(laps < REQUESTED_LAPS),
            "maximum_lateral_error_m": float(np.nanmax(error)),
            "mean_lateral_error_m": float(np.nanmean(error)),
            "final_progress_m": float(progress[-1]),
        })
    lap_error_cm = 100.0 * float(np.nanmean([np.median(values) if values else np.nan for values in bins]))
    row = {"parameter_set": setting, "requested_laps": REQUESTED_LAPS, "lap_error_cm": lap_error_cm, "runs": runs}
    summary.append(row)
    status = ", ".join(
        f"{run['completed_laps']} laps, {'left track' if run['left_track'] else 'completed'}, mean {100 * run['mean_lateral_error_m']:.1f} cm"
        for run in runs
    )
    print(f"{setting:>10s}: lap error {lap_error_cm:.1f} cm; {status}")
with open(os.path.join(RESULTS, "summary.json"), "w") as file:
    json.dump(summary, file, indent=2)
