"""Walk-forward backtesting harness for Phase 3.

**What is walk-forward testing?**

In Phase 2 we used a single 80/20 train/test split.  The problem: if we get
lucky on that one test window, we think the strategy works — but it might just
be an overfit to that particular period.

Walk-forward testing runs *multiple* non-overlapping test windows, each with
its own fresh model trained on the data before it.  If the strategy shows
positive Sharpe in *all* (or most) of those windows, that's much stronger
evidence of a real edge.

Fold geometry (default from config):
    Fold 1:  train=[0    :1800], val=[1800:2400], test=[2400:3000]
    Fold 2:  train=[600  :2400], val=[2400:3000], test=[3000:3600]
    Fold 3:  train=[1200 :3000], val=[3000:3600], test=[3600:4200]
    Fold 4:  train=[1800 :3600], val=[3600:4200], test=[4200:4800]

Each fold trains on a rolling window (not expanding) to give each fold
roughly equal training-set size and recency.
"""
from __future__ import annotations

import warnings

import pandas as pd

from bot.backtest.engine import run_backtest
from bot.backtest.metrics import compute_calibration_metrics, compute_metrics


def _try_shap_importance(model, X_test: pd.DataFrame) -> dict | None:
    """Compute SHAP importance if xgboost_model is available; else return None."""
    try:
        from bot.models.xgboost_model import compute_shap_importance  # noqa: PLC0415
        return compute_shap_importance(model, X_test)
    except Exception:
        return None


def run_walkforward(
    df: pd.DataFrame,
    n_folds: int,
    train_bars: int,
    val_bars: int,
    test_bars: int,
    feature_fn,
    label_fn,
    model_fn,
    policy_fn,
) -> list[dict]:
    """Execute a rolling walk-forward backtest and return per-fold results.

    For each fold the pipeline is:
        1. Slice the raw DataFrame into train / val / test windows.
        2. ``feature_fn(df_train_raw)``  → feature DataFrame (engineering).
        3. ``label_fn(df_train_feat, compute_thresholds=True)``
               → (X_train, y_train, lower_thresh, upper_thresh).
           Thresholds are derived from training data *only* — no leakage.
        4. ``model_fn(X_train, y_train)``  → fitted model.
        5. Generate P(long) on the test feature DataFrame.
        6. ``policy_fn(prob_series)``  → discrete signal series.
        7. ``run_backtest(df_test_with_signal)``  → equity curve.
        8. ``compute_metrics(results)``  → performance dict.
        9. ``compute_calibration_metrics``  → Brier score.

    If a fold fails for any reason (e.g. not enough labeled bars), that fold
    is skipped with a warning and all metric values are set to ``None``.
    This ensures the caller always receives exactly ``n_folds`` dicts.

    Args:
        df:           Raw OHLCV DataFrame (datetime index, sorted ascending).
        n_folds:      Number of folds to attempt.
        train_bars:   Number of bars in each fold's training window.
        val_bars:     Number of bars reserved for validation (currently passed
                      to model_fn as part of the training window; reserved for
                      future threshold-tuning use).
        test_bars:    Number of OOS bars evaluated per fold.
        feature_fn:   ``feature_fn(df_slice) → pd.DataFrame``
                      Applies feature engineering to a raw slice.
        label_fn:     ``label_fn(df_feat, compute_thresholds=False, lower=None,
                      upper=None) → (X, y [, lower, upper])``
                      Produces labeled (X, y) pairs.
        model_fn:     ``model_fn(X_train, y_train) → fitted_model``
                      Trains and returns a fitted sklearn-compatible model.
        policy_fn:    ``policy_fn(prob_series) → pd.Series[int]``
                      Converts probabilities to a 0/1 signal series.

    Returns:
        List of exactly ``n_folds`` dicts, each containing:
            fold, train_start, train_end, test_start, test_end,
            total_return, sharpe_ratio, max_drawdown, num_trades,
            win_rate, brier_score
        Skipped folds have ``None`` for every metric key.
    """
    folds: list[dict] = []

    for k in range(n_folds):
        # ── Fold boundary computation ────────────────────────────────────────
        # Each fold shifts the test window forward by test_bars.
        # Train and val windows move with it (rolling, fixed-size windows).
        train_start = k * test_bars
        train_end   = train_start + train_bars
        val_end     = train_end   + val_bars
        test_end    = val_end     + test_bars

        try:
            if test_end > len(df):
                raise ValueError(
                    f"Not enough bars for fold {k + 1}: need {test_end}, "
                    f"have {len(df)}.  Reduce n_folds or bar counts in config."
                )

            # ── Raw slices ───────────────────────────────────────────────────
            # We capture timestamps BEFORE calling feature_fn because
            # compute_features does reset_index(drop=True), which loses datetime.
            df_train_raw = df.iloc[train_start:train_end]
            df_val_raw   = df.iloc[train_end:val_end]
            df_test_raw  = df.iloc[val_end:test_end]

            # Capture start/end timestamps for the fold result record
            train_start_ts = df_train_raw.index[0]  if len(df_train_raw) else None
            train_end_ts   = df_train_raw.index[-1] if len(df_train_raw) else None
            test_start_ts  = df_test_raw.index[0]   if len(df_test_raw)  else None
            test_end_ts    = df_test_raw.index[-1]  if len(df_test_raw)  else None

            # ── Step 1: Feature engineering ──────────────────────────────────
            # Apply the same feature pipeline to both train and test slices.
            # feature_fn resets the index, so both dfs now have 0-based integer indices.
            df_train_feat = feature_fn(df_train_raw.copy())
            df_test_feat  = feature_fn(df_test_raw.copy())

            # ── Step 2: Labels (thresholds from training data only) ──────────
            # IMPORTANT: compute_thresholds=True on TRAINING slice only.
            # Then we *apply* those thresholds to the test slice without recomputing.
            # Recomputing on test data would be leakage (peeking at the future).
            label_result = label_fn(df_train_feat, compute_thresholds=True)
            X_train, y_train, lower_thresh, upper_thresh = label_result

            X_test, y_test = label_fn(
                df_test_feat, lower=lower_thresh, upper=upper_thresh
            )

            # ── Step 3: Train model ──────────────────────────────────────────
            # A fresh model is trained from scratch for every fold.
            # No information carries over between folds.
            fitted_model = model_fn(X_train, y_train)

            # ── Step 4: Inference on test features ───────────────────────────
            # Predict P(long) for every bar in the test feature DataFrame.
            # We use the same feature columns the model was trained on.
            feature_cols = X_train.columns.tolist()
            prob_values = fitted_model.predict_proba(
                df_test_feat[feature_cols]
            )[:, 1]  # index 1 = probability of class 1 (long)

            prob_series = pd.Series(
                prob_values, index=df_test_feat.index, name="prob_long"
            )

            # ── Step 5: Apply signal policy ──────────────────────────────────
            # Convert probabilities to 0/1 signals using the abstain-band policy.
            signal_series = policy_fn(prob_series)

            # Attach signal to the test feature DataFrame for run_backtest
            df_test_bt = df_test_feat.copy()
            df_test_bt["signal"] = signal_series

            # ── Step 6: Backtest ─────────────────────────────────────────────
            bt_results = run_backtest(df_test_bt)
            strategy_m, _ = compute_metrics(bt_results)

            # ── Step 7: Calibration metrics (on labeled test rows) ───────────
            # y_test keeps the *index labels* from df_test_feat after filtering.
            # When regime features drop warm-up rows, those labels are often not
            # a 0..N-1 RangeIndex. Using .iloc with label values then interprets
            # them as positional indices and can raise "out-of-bounds".
            #
            # Use .loc so we match by index label, then reset for metric code.
            prob_test_labeled = prob_series.loc[y_test.index].reset_index(drop=True)
            y_test_aligned    = y_test.reset_index(drop=True)

            cal_metrics = compute_calibration_metrics(y_test_aligned, prob_test_labeled)

            # ── Step 8: SHAP feature importance ──────────────────────────────────
            # Compute mean |SHAP| per feature for the test set.  Returns None
            # for non-XGBoost models (e.g. logistic regression in Phase 3).
            shap_importance = _try_shap_importance(
                fitted_model, df_test_feat[feature_cols]
            )

            fold_result = {
                "fold":             k + 1,
                "train_start":      train_start_ts,
                "train_end":        train_end_ts,
                "test_start":       test_start_ts,
                "test_end":         test_end_ts,
                "total_return":     strategy_m["total_return"],
                "sharpe_ratio":     strategy_m["sharpe_ratio"],
                "max_drawdown":     strategy_m["max_drawdown"],
                "num_trades":       strategy_m["num_trades"],
                "win_rate":         strategy_m["win_rate"],
                "brier_score":      cal_metrics["brier_score"],
                "shap_importance":  shap_importance,
            }

        except Exception as exc:
            warnings.warn(
                f"Walk-forward fold {k + 1} failed and will be skipped: {exc}",
                UserWarning,
                stacklevel=2,
            )
            fold_result = {
                "fold":             k + 1,
                "train_start":      None,
                "train_end":        None,
                "test_start":       None,
                "test_end":         None,
                "total_return":     None,
                "sharpe_ratio":     None,
                "max_drawdown":     None,
                "num_trades":       None,
                "win_rate":         None,
                "brier_score":      None,
                "shap_importance":  None,
            }

        folds.append(fold_result)

    return folds
