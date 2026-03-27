from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.chart_helper import line_generation, line_growth, line_share
from utils.preprocess_energy import make_growth_df, make_share_df

st.title("03. 시각화 분석")

if "df" not in st.session_state:
    st.warning("먼저 `01_업로드_전처리` 페이지에서 데이터를 업로드하세요.")
    st.stop()

df = st.session_state["df"].copy()

if "연도" in df.columns:
    min_year, max_year = int(df["연도"].min()), int(df["연도"].max())
    year_range = st.sidebar.slider("연도 범위", min_year, max_year, (min_year, max_year))
    df = df[(df["연도"] >= year_range[0]) & (df["연도"] <= year_range[1])]

numeric_cols = df.select_dtypes(include="number").columns.tolist()
candidate_y_cols = [c for c in numeric_cols if c != "연도"]

st.subheader("에너지 전용 차트")
required_cols = {"연도", "수력", "기력", "복합화력", "원자력", "신재생"}
if required_cols.issubset(set(df.columns)):
    st.plotly_chart(line_generation(df, "에너지원별 발전량 추이"), use_container_width=True)
    st.plotly_chart(line_share(make_share_df(df), "에너지 믹스 변화 (비중)"), use_container_width=True)
    st.plotly_chart(line_growth(make_growth_df(df), "에너지원별 성장률"), use_container_width=True)
else:
    st.info("에너지 스키마가 없어 범용 차트만 표시합니다.")

st.markdown("---")
st.subheader("범용 차트 생성")

chart_type = st.selectbox(
    "차트 유형",
    ["Bar", "Line", "Area", "Scatter", "Pie", "Histogram", "Box"],
)
x_col = st.selectbox("x축", df.columns.tolist())
y_col = st.selectbox("y축", candidate_y_cols if candidate_y_cols else df.columns.tolist())
color_col = st.selectbox("색상 그룹(hue)", ["없음"] + df.columns.tolist())
agg = st.selectbox("집계 방식", ["sum", "mean", "count", "max", "min"])

plot_df = df.copy()
if agg != "count" and y_col not in plot_df.select_dtypes(include="number").columns:
    st.warning("선택한 y축은 숫자 컬럼이 아닙니다. count 집계를 사용하세요.")
else:
    if chart_type in ("Bar", "Line", "Area"):
        grouped = (
            plot_df.groupby([x_col] + ([] if color_col == "없음" else [color_col]), dropna=False)[y_col]
            .agg(agg)
            .reset_index()
        )
        if chart_type == "Bar":
            fig = px.bar(grouped, x=x_col, y=y_col, color=None if color_col == "없음" else color_col)
        elif chart_type == "Line":
            fig = px.line(grouped, x=x_col, y=y_col, color=None if color_col == "없음" else color_col)
        else:
            fig = px.area(grouped, x=x_col, y=y_col, color=None if color_col == "없음" else color_col)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Scatter":
        fig = px.scatter(plot_df, x=x_col, y=y_col, color=None if color_col == "없음" else color_col)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Pie":
        grouped = plot_df.groupby(x_col, dropna=False)[y_col].agg(agg).reset_index()
        fig = px.pie(grouped, names=x_col, values=y_col, hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Histogram":
        fig = px.histogram(plot_df, x=x_col, color=None if color_col == "없음" else color_col)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Box":
        fig = px.box(plot_df, x=x_col, y=y_col, color=None if color_col == "없음" else color_col)
        st.plotly_chart(fig, use_container_width=True)
