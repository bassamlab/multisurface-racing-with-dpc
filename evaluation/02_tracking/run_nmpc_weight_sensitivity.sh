#!/usr/bin/env bash
# NMPC weight tuning with the budget of the DPC check (run_dpc_weight_sensitivity.sh): two weights, the nominal setting and
# half / double of each one at a time, 3 seeds x 3 laps on l_shape, first lap discarded. Weights: lateral tracking (q_lat)
# and steering-rate input cost (r_steering_rate) of external/nmpc/Config/RoboRacer-Multibody/MPC_params.yaml; nominal = the
# setting before this tuning (16.8, 264.9). Selection: lowest lap error among the settings that complete every lap (q_lat 33.6).
# Usage from the repository root: evaluation/02_tracking/run_nmpc_weight_sensitivity.sh [seeds] [laps]
set -ef

SEEDS=${1:-"1 2 3"}
LAPS=${2:-3}
OUT=evaluation/02_tracking/results/nmpc_weight_sensitivity
SETTINGS=${SETTINGS:-"16.8,264.9 8.4,264.9 33.6,264.9 16.8,132.45 16.8,529.8"}

mkdir -p "$OUT"
export PYTHONPATH="$PWD/external/dpc:$PWD/external/nmpc"
export NUMBA_CACHE_DIR=${NUMBA_CACHE_DIR:-/tmp/multisurface-numba}
export MPLCONFIGDIR=${MPLCONFIGDIR:-/tmp/multisurface-mpl}
export ACADOS_SOURCE_DIR=${ACADOS_SOURCE_DIR:-$HOME/dev/acados} LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-$HOME/dev/acados/lib}
export PYGLET_SHADOW_WINDOW=0   # no display needed (rendering is disabled)

for setting in $SETTINGS; do
  q=${setting%,*}
  r=${setting#*,}
  label="qlat${q/./p}_rsr${r/./p}"
  params="$OUT/MPC_params_$label.yaml"
  .venv/bin/python -c "import sys, yaml
p = yaml.safe_load(open('external/nmpc/Config/RoboRacer-Multibody/MPC_params.yaml'))
p['q_lat'], p['r_steering_rate'] = float(sys.argv[1]), float(sys.argv[2])
yaml.safe_dump(p, open(sys.argv[3], 'w'), sort_keys=False)" "$q" "$r" "$params"
  for seed in $SEEDS; do
    name="log_nmpc_eval_l_shape_sensitivity_${label}_s${seed}"
    [ -f "$OUT/$name" ] && continue
    env DPC_MAP_NAME=l_shape DPC_NUMBER_OF_LAPS="$LAPS" DPC_VELOCITY_MAX=20 DPC_ABORT_ERROR=5 \
      DPC_SEED="$seed" DPC_LOG_SUFFIX="_sensitivity_${label}_s${seed}" NMPC_MPC_PARAMS_FILE="../../../$params" \
      .venv/bin/python evaluation/02_tracking/run_nmpc_headless.py
    mv "$name" "$OUT/"
  done
done

.venv/bin/python evaluation/02_tracking/summarize_nmpc_weight_sensitivity.py "$OUT" "$LAPS"
