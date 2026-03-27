from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ENERGY_COLOR_MAP = {
    "수력": "#1f77b4",
    "기력": "#7f7f7f",
    "복합화력": "#ff7f0e",
    "원자력": "#9467bd",
    "신재생": "#2ca02c",
}


def melt_energy(df: pd.DataFrame) -> pd.DataFrame:
    return df.melt(id_vars=["연도"], var_name="에너지원", value_name="값")


def line_generation(df: pd.DataFrame, title: str):
    m = melt_energy(df)
    return px.line(m, x="연도", y="값", color="에너지원", color_discrete_map=ENERGY_COLOR_MAP, title=title)


def line_share(df_share: pd.DataFrame, title: str):
    plot_df = df_share.reset_index().melt(id_vars=["연도"], var_name="에너지원", value_name="비중")
    return px.line(plot_df, x="연도", y="비중", color="에너지원", color_discrete_map=ENERGY_COLOR_MAP, title=title)


def line_growth(df_growth: pd.DataFrame, title: str):
    plot_df = df_growth.reset_index().melt(id_vars=["연도"], var_name="에너지원", value_name="증감률")
    return px.line(plot_df, x="연도", y="증감률", color="에너지원", color_discrete_map=ENERGY_COLOR_MAP, title=title)


def line_actual_plus_forecast(
    df_hist: pd.DataFrame,
    forecast_by_col: dict[str, "pd.Series"],
    title: str,
) -> go.Figure:
    """
    실제(전체 이력) + 예측(점선)을 한 화면에. 홈 대시보드와 동일 색상 팔레트.
    """
    d = df_hist.sort_values("연도").copy()
    fig = go.Figure()
    energy_order = list(forecast_by_col.keys())
    for i, col in enumerate(energy_order):
        color = ENERGY_COLOR_MAP.get(col, None)
        fut = forecast_by_col[col]
        # 실제: 전체 연도
        fig.add_trace(
            go.Scatter(
                x=d["연도"],
                y=d[col],
                mode="lines",
                name=col,
                line=dict(color=color, width=2),
                legendgroup=col,
            )
        )
        # 예측: 점선 (범례는 과밀 방지를 위해 첫 번째 전원만 ‘예측’ 표시)
        fig.add_trace(
            go.Scatter(
                x=fut.index,
                y=fut.values,
                mode="lines",
                name="",
                line=dict(color=color, width=2, dash="dash"),
                legendgroup=col,
                showlegend=False,
            )
        )
    fig.update_layout(
        title=title,
        xaxis_title="연도",
        yaxis_title="발전량",
        hovermode="x unified",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
    )
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0,
        y=-0.12,
        showarrow=False,
        text="실선: 실제 데이터 / 점선: 동일 설정으로 예측한 구간",
        font=dict(size=12),
    )
    return fig
