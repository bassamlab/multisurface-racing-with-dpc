#!/usr/bin/env bash
# NMPC tire-parameter comparison on the L-shaped track (Sec. IV-B): the fits at mu 0.5 and 1.1 and their midpoint (the default
# pacejka_params.yaml), 3 seeds x 3 laps, with the weights before the tuning (q_lat 16.8, run_nmpc_weight_sensitivity.sh).
# Usage from the repository root: [SETTINGS="mu05fit midfit mu11"] evaluation/02_tracking/run_nmpc_parameter_check.sh [seeds] [laps]
set -ef

SEEDS=${1:-"1 2 3"}
LAPS=${2:-3}
OUT=evaluation/02_tracking/results/nmpc_parameter_check
PARAMS=evaluation/02_tracking/results/nmpc_weight_sensitivity/MPC_params_qlat16p8_rsr264p9.yaml
mkdir -p "$OUT"
export PYTHONPATH="$PWD/external/dpc:$PWD/external/nmpc"
export NUMBA_CACHE_DIR=${NUMBA_CACHE_DIR:-/tmp/multisurface-numba}
export MPLCONFIGDIR=${MPLCONFIGDIR:-/tmp/multisurface-mpl}
export ACADOS_SOURCE_DIR=${ACADOS_SOURCE_DIR:-$HOME/dev/acados} LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-$HOME/dev/acados/lib}
export PYGLET_SHADOW_WINDOW=0   # no display needed (rendering is disabled)

for setting in ${SETTINGS:-mu05fit midfit mu11}; do
  case "$setting" in
    mu05fit) tire="RoboRacer-Multibody/pacejka_params_mu05fit.yaml" ;;
    midfit) tire="RoboRacer-Multibody/pacejka_params_midfit.yaml" ;;
    mu11) tire="RoboRacer-Multibody/pacejka_params_mu11.yaml" ;;
  esac
  for seed in $SEEDS; do
    name="log_nmpc_eval_l_shape_param_${setting}_s${seed}"
    [ -f "$OUT/$name" ] && continue
    env DPC_MAP_NAME=l_shape DPC_NUMBER_OF_LAPS="$LAPS" DPC_VELOCITY_MAX=20 DPC_ABORT_ERROR=5 \
      DPC_SEED="$seed" DPC_LOG_SUFFIX="_param_${setting}_s${seed}" NMPC_TIRE_PARAMS_FILE="$tire" \
      NMPC_MPC_PARAMS_FILE="../../../$PARAMS" .venv/bin/python evaluation/02_tracking/run_nmpc_headless.py
    mv "$name" "$OUT/"
  done
done

.venv/bin/python evaluation/02_tracking/summarize_nmpc_parameter_check.py "$OUT" "$LAPS"
