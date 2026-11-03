"""Evaluation measures shared by the paper figures and Table I."""
import os
import numpy as np

# predicted points per prediction in the paper's closed-loop prediction error: 1 = one step, the only point predicted for the input
# that is actually applied (the controller re-plans afterwards); PRED_STEPS=0: the whole horizon
PRED_STEPS = int(os.environ.get("PRED_STEPS", "1")) or None


def prediction_offset(pred_xy, x, y):
    """which logged step the first predicted point belongs to (the logger's offset: -1, 0 or 1)"""
    best = None
    for off in (-1, 0, 1):
        e0 = [np.hypot(p[0][0] - x[k + off], p[1][0] - y[k + off]) for k, p in enumerate(pred_xy) if p is not None and 0 <= k + off < len(x)]
        if best is None or np.median(e0) < best[1]:
            best = (off, np.median(e0))
    return best[0]


def prediction_error(pred_xy, x, y, offset=None, steps=None):
    """rms position error over the horizon (or its first steps) of each logged prediction; the first predicted point belongs to
    the logged step that fits it best (the logger's offset), or to the given offset."""
    horizon = next(len(p[0]) for p in pred_xy if p is not None)
    horizon = min(horizon, steps) if steps else horizon
    pred_xy = [None if p is None else (p[0][:horizon], p[1][:horizon]) for p in pred_xy]
    off = prediction_offset(pred_xy, x, y) if offset is None else offset
    err = np.full(len(x), np.nan)
    for k, p in enumerate(pred_xy):
        j = k + off
        if p is not None and j >= 0 and j + horizon <= len(x):
            err[k] = np.sqrt(np.mean((np.asarray(p[0]) - x[j:j + horizon]) ** 2 + (np.asarray(p[1]) - y[j:j + horizon]) ** 2))
    return err
