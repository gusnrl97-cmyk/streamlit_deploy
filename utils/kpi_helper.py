from __future__ import annotations

import pandas as pd


def latest_and_prev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series | None]:
    if df.empty:
        raise ValueError("빈 데이터입니다.")
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else None
    return latest, prev


def pct_delta(curr: float, prev: float | None) -> float | None:
    if prev in (None, 0):
        return None
    return ((curr - prev) / prev) * 100.0


def compute_kpis(df: pd.DataFrame) -> dict:
    latest, prev = latest_and_prev(df)
    energy_cols = [c for c in df.columns if c != "연도"]
    total_latest = float(latest[energy_cols].sum())
    total_prev = float(prev[energy_cols].sum()) if prev is not None else None

    def share(col: str) -> float:
        return (float(latest[col]) / total_latest) * 100 if total_latest else 0.0
    
    def share_prev(col: str) -> float | None:
        if prev is None or not total_prev:
            return None
        return (float(prev[col]) / total_prev) * 100 if total_prev else 0.0

    coal_share_latest = share("기력")
    coal_share_previous = share_prev("기력")
    # 석탄 비중이 감소한 경우를 "감소율"로 양수로 표현
    coal_share_decrease_rate_pct = (
        ((coal_share_previous - coal_share_latest) / coal_share_previous) * 100
        if coal_share_previous not in (None, 0)
        else None
    )

    return {
        "latest_year": int(latest["연도"]),
        "total_generation": total_latest,
        "total_generation_delta_pct": pct_delta(total_latest, total_prev),
        "renewable_share": share("신재생"),
        "lng_share": share("복합화력"),
        "coal_share": coal_share_latest,
        "coal_share_decrease_rate_pct": coal_share_decrease_rate_pct,
    }
