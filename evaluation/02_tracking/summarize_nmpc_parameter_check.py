"""Summarize whether each NMPC tire-parameter set completes the requested laps."""
import glob
import json
import os
import sys

import numpy as np


RESULTS = sys.argv[1] if len(sys.argv) > 1 else "evaluation/02_tracking/results/nmpc_parameter_check"
REQUESTED_LAPS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
summary = []
found = {os.path.basename(p)[len("log_nmpc_eval_l_shape_param_"):].rsplit("_s", 1)[0]
         for p in glob.glob(os.path.join(RESULTS, "log_nmpc_eval_l_shape_param_*"))}
for setting in sorted(found):
    runs = []
    for path in sorted(glob.glob(os.path.join(RESULTS, f"log_nmpc_eval_l_shape_param_{setting}_s*"))):
        data = json.load(open(path))
        laps = int(np.nanmax(np.asarray(data["lap_n"], float)))
        error = np.asarray(data["tracking_error"], float)
        progress = np.asarray(data["track_progress"], float)
        runs.append({
            "file": os.path.basename(path),
            "completed_laps": laps,
            "left_track": bool(laps < REQUESTED_LAPS),
            "maximum_lateral_error_m": float(np.nanmax(error)),
            "mean_lateral_error_m": float(np.nanmean(error)),
            "final_progress_m": float(progress[-1]),
        })
    row = {"parameter_set": setting, "requested_laps": REQUESTED_LAPS, "runs": runs}
    summary.append(row)
    status = ", ".join(
        f"{run['completed_laps']} laps, {'left track' if run['left_track'] else 'completed'}, mean {100 * run['mean_lateral_error_m']:.1f} cm"
        for run in runs
    )
    print(f"{setting:>10s}: {status}")
with open(os.path.join(RESULTS, "summary.json"), "w") as file:
    json.dump(summary, file, indent=2)
