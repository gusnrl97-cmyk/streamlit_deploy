from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except ImportError:  # pragma: no cover
    ExponentialSmoothing = None


def _linear_forecast(years: np.ndarray, values: np.ndarray, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """최소제곱 1차 추세로 향후 연도·값 예측."""
    x = years.astype(float)
    v = values.astype(float)
    coef = np.polyfit(x, v, 1)
    poly = np.poly1d(coef)
    last_year = int(x[-1])
    fut_years = np.arange(last_year + 1, last_year + 1 + horizon, dtype=int)
    fut_vals = poly(fut_years.astype(float))
    return fut_years, np.maximum(fut_vals, 0.0)


def forecast_series(
    df: pd.DataFrame,
    value_col: str,
    n_recent_years: int,
    horizon: int,
    method: str = "ets",
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    연도 기준 시계열을 최근 n_recent_years만 학습해 horizon년 앞까지 예측.
    반환: (과거 학습 구간 시리즈, 예측 연도 인덱스, 예측 값)
    """
    d = df.sort_values("연도").dropna(subset=["연도", value_col]).copy()
    d = d.tail(n_recent_years)
    if len(d) < 3:
        raise ValueError("학습에 필요한 연도가 부족합니다. (최소 3년 이상)")

    years = d["연도"].astype(int).values
    values = d[value_col].astype(float).values

    if method == "linear":
        fut_years, fut_vals = _linear_forecast(years, values, horizon)
        hist = pd.Series(values, index=years, name=value_col)
        fut = pd.Series(fut_vals, index=fut_years, name=value_col)
        return hist, fut, fut

    if method != "ets" or ExponentialSmoothing is None:
        fut_years, fut_vals = _linear_forecast(years, values, horizon)
        hist = pd.Series(values, index=years, name=value_col)
        fut = pd.Series(fut_vals, index=fut_years, name=value_col)
        return hist, fut, fut

    # 연 단위 데이터: DatetimeIndex(연초)로 두면 statsmodels 예측 인덱스 경고가 줄어듦
    last_year = int(years[-1])
    fut_index_int = list(range(last_year + 1, last_year + 1 + horizon))
    try:
        idx = pd.date_range(start=f"{int(years[0])}-01-01", periods=len(years), freq="YS")
        s_dt = pd.Series(values, index=idx, name=value_col)
        model = ExponentialSmoothing(s_dt, trend="add", seasonal=None)
        fit = model.fit(optimized=True)
        pred = fit.forecast(horizon)
        fut_vals = np.maximum(np.asarray(pred.values, dtype=float), 0.0)
        fut_years = [int(ts.year) for ts in pred.index]
        fut = pd.Series(fut_vals, index=fut_years, name=value_col)
        s_out = pd.Series(values, index=years.astype(int), name=value_col)
        return s_out, fut, fut
    except Exception:
        fut_years, fut_vals = _linear_forecast(years, values, horizon)
        s_out = pd.Series(values, index=years.astype(int), name=value_col)
        fut = pd.Series(fut_vals, index=fut_years, name=value_col)
        return s_out, fut, fut


def forecast_all_sources(
    df: pd.DataFrame,
    energy_cols: list[str],
    n_recent_years: int,
    horizon: int,
    method: str,
    scenario_mult: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.Series]]:
    """
    발전원별 예측. scenario_mult: {'신재생': 1.1} → 예측값에 곱함.
    반환: (wide 예측표 연도×에너지원, 성장 요약 테이블, 시나리오 반영 예측 시리즈 dict)
    """
    scenario_mult = scenario_mult or {}
    rows = []
    summary = []
    forecast_by_col: dict[str, pd.Series] = {}

    for col in energy_cols:
        hist, fut, _ = forecast_series(df, col, n_recent_years, horizon, method=method)
        mult = float(scenario_mult.get(col, 1.0))
        fut_adj = fut * mult
        forecast_by_col[col] = fut_adj
        last_val = float(hist.iloc[-1])
        train_end_year = int(hist.index[-1])
        end_val = float(fut_adj.iloc[-1])
        end_year = int(fut_adj.index[-1])
        # 학습 구간 마지막 연도 → 예측 말년까지의 기간으로 CAGR 근사
        years_span = max(end_year - train_end_year, 1)
        cagr = (end_val / last_val) ** (1.0 / years_span) - 1.0 if last_val > 0 else np.nan

        for y, v in fut_adj.items():
            rows.append({"연도": y, "에너지원": col, "예측값": v})
        summary.append(
            {
                "에너지원": col,
                "기준_마지막연도": train_end_year,
                "최근값": last_val,
                f"{end_year}년_예측": end_val,
                "연평균성장률_근사": cagr,
            }
        )

    wide = pd.DataFrame(rows)
    if not wide.empty:
        wide = wide.pivot(index="연도", columns="에너지원", values="예측값").reset_index()
    summary_df = pd.DataFrame(summary).sort_values("연평균성장률_근사", ascending=False, na_position="last")
    return wide, summary_df, forecast_by_col
