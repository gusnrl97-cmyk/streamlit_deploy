from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.chart_helper import line_generation, line_growth, line_share
from utils.data_loader import get_excel_sheet_names, get_file_ext, load_dataframe
from utils.preprocess_energy import coerce_energy_schema, make_growth_df, make_share_df

PREPROCESS_VERSION = 6

st.title("01. 업로드 및 전처리")

uploaded = st.file_uploader("CSV 또는 XLSX 파일 업로드", type=["csv", "xlsx", "xls"])

raw_df = None
data_name = None

if uploaded:
    ext = get_file_ext(uploaded.name)
    sheet_name = None
    if ext in ("xlsx", "xls"):
        sheets = get_excel_sheet_names(uploaded)
        sheet_name = st.selectbox("시트 선택", sheets)
    raw_df = load_dataframe(uploaded, ext, sheet_name=sheet_name)
    data_name = uploaded.name
else:
    default_path = Path(r"C:\Users\user\Downloads\HOME_발전·판매_발전량_전원별.xlsx")
    if default_path.exists():
        raw_df = pd.read_excel(default_path, header=[0, 1])
        data_name = default_path.name
        st.info(f"업로드 파일이 없어 기본 데이터셋을 자동 사용합니다: {data_name}")
    else:
        st.info("파일을 업로드하면 전처리 후 다음 페이지에서 분석할 수 있습니다.")
        st.stop()

st.subheader("원본 데이터 미리보기 (상위 5행)")
st.dataframe(raw_df.head(5), use_container_width=True)

st.markdown("---")
st.subheader("전처리 옵션")
apply_energy_schema = st.checkbox(
    "에너지 분석 스키마 적용 (연도/수력/기력/복합화력/원자력/신재생)",
    value=True,
)

try:
    processed_df = coerce_energy_schema(raw_df) if apply_energy_schema else raw_df.copy()
except Exception as e:
    st.error(f"전처리 실패: {e}")
    st.stop()

st.success("전처리가 완료되었습니다.")
st.subheader("전처리 결과 (상위 5행)")
st.dataframe(processed_df.head(5), use_container_width=True)

st.session_state["raw_df"] = raw_df
st.session_state["df"] = processed_df
st.session_state["data_filename"] = data_name
st.session_state["preprocess_version"] = PREPROCESS_VERSION

required_cols = {"연도", "수력", "기력", "복합화력", "원자력", "신재생"}
if required_cols.issubset(set(processed_df.columns)):
    st.markdown("---")
    st.subheader("바로 보는 핵심 그래프")
    st.plotly_chart(line_generation(processed_df, "에너지원별 발전량 추이"), use_container_width=True)
    st.plotly_chart(line_share(make_share_df(processed_df), "에너지 믹스 변화 (비중)"), use_container_width=True)
    st.plotly_chart(line_growth(make_growth_df(processed_df), "에너지원별 성장률"), use_container_width=True)

st.caption("요약 지표는 `02_데이터_요약_KPI` 페이지에서 확인할 수 있습니다.")
