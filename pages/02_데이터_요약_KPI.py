from __future__ import annotations

import streamlit as st
import pandas as pd

from utils.kpi_helper import compute_kpis

st.title("02. 데이터 요약 및 KPI")

if "df" not in st.session_state:
    st.warning("먼저 `01_업로드_전처리` 페이지에서 데이터를 업로드하세요.")
    st.stop()

df = st.session_state["df"].copy()

st.subheader("데이터 정보 요약")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("행 개수", f"{len(df):,}")
with col2:
    st.metric("열 개수", f"{df.shape[1]:,}")
with col3:
    st.metric("결측치 수", f"{int(df.isna().sum().sum()):,}")
with col4:
    st.metric("연도 범위", f"{df['연도'].min()} ~ {df['연도'].max()}" if "연도" in df.columns else "N/A")

type_counts = {
    "numeric": len(df.select_dtypes(include="number").columns),
    "categorical": len(df.select_dtypes(include="object").columns),
    "datetime": len(df.select_dtypes(include="datetime").columns),
}
st.write("타입 분포:", type_counts)

st.markdown("---")
st.subheader("KPI 카드")

required = {"연도", "수력", "기력", "복합화력", "원자력", "신재생"}
if required.issubset(set(df.columns)):
    k = compute_kpis(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("최신 연도 총 발전량", f"{k['total_generation']:,.0f}", f"{(k['total_generation_delta_pct'] or 0):.2f}%")
    c2.metric("신재생 비중", f"{k['renewable_share']:.2f}%")
    c3.metric("LNG(복합화력) 비중", f"{k['lng_share']:.2f}%")
    c4.metric("석탄(기력) 비중", f"{k['coal_share']:.2f}%")
else:
    st.info("에너지 KPI는 에너지 스키마 컬럼이 있을 때 표시됩니다.")

st.subheader("데이터프레임 미리보기")
st.dataframe(df.head(20), use_container_width=True)
