#!/usr/bin/env bash
# Reproduce the preliminary NMPC tire-parameter comparison on the L-shaped track (run 2026-11-01 before the weight tuning,
# i.e. with q_lat 16.8: NMPC_MPC_PARAMS_FILE=../../../evaluation/02_tracking/results/nmpc_weight_sensitivity/MPC_params_qlat16p8_rsr264p9.yaml).
# Usage from the repository root: [SETTINGS="mu05 midpoint mu11"] evaluation/02_tracking/run_nmpc_parameter_check.sh [seeds] [laps]
set -ef

SEEDS=${1:-"1 2 3"}
LAPS=${2:-3}
OUT=evaluation/02_tracking/results/nmpc_parameter_check
mkdir -p "$OUT"
export PYTHONPATH="$PWD/external/dpc:$PWD/external/nmpc"
export NUMBA_CACHE_DIR=${NUMBA_CACHE_DIR:-/tmp/multisurface-numba}
export MPLCONFIGDIR=${MPLCONFIGDIR:-/tmp/multisurface-mpl}
export ACADOS_SOURCE_DIR=${ACADOS_SOURCE_DIR:-/Users/juliusbeerwerth/dev/acados}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-/Users/juliusbeerwerth/dev/acados/lib}

for setting in ${SETTINGS:-mu05 midpoint mu11}; do
  case "$setting" in
    mu05) tire="RoboRacer-Multibody/pacejka_params_mu05.yaml" ;;
    midpoint) tire="RoboRacer-Multibody/pacejka_params_midpoint_hybrid.yaml" ;;
    mu11) tire="RoboRacer-Multibody/pacejka_params_mu11.yaml" ;;
    mu05fit) tire="RoboRacer-Multibody/pacejka_params_mu05fit.yaml" ;;
    mu08fit) tire="RoboRacer-Multibody/pacejka_params_mu08fit.yaml" ;;
    midfit) tire="RoboRacer-Multibody/pacejka_params_midfit.yaml" ;;
    pooledfit) tire="RoboRacer-Multibody/pacejka_params_pooledfit.yaml" ;;
    pooled0511fit) tire="RoboRacer-Multibody/pacejka_params_pooled0511fit.yaml" ;;
  esac
  for seed in $SEEDS; do
    name="log_nmpc_eval_l_shape_param_${setting}_s${seed}"
    [ -f "$OUT/$name" ] && continue
    env DPC_MAP_NAME=l_shape DPC_NUMBER_OF_LAPS="$LAPS" DPC_VELOCITY_MAX=20 DPC_ABORT_ERROR=5 \
      DPC_SEED="$seed" DPC_LOG_SUFFIX="_param_${setting}_s${seed}" NMPC_TIRE_PARAMS_FILE="$tire" \
      .venv/bin/python evaluation/02_tracking/run_nmpc_headless.py
    mv "$name" "$OUT/"
  done
done

.venv/bin/python evaluation/02_tracking/summarize_nmpc_parameter_check.py "$OUT" "$LAPS"
