from __future__ import annotations

import streamlit as st

from utils.export_helper import to_csv_bytes, to_excel_bytes
from utils.kpi_helper import compute_kpis

st.title("05. 리포트 및 Export")

if "df" not in st.session_state:
    st.warning("먼저 `01_업로드_전처리` 페이지에서 데이터를 업로드하세요.")
    st.stop()

df = st.session_state["df"].copy()

st.subheader("핵심 인사이트")
required = {"연도", "수력", "기력", "복합화력", "원자력", "신재생"}
if required.issubset(set(df.columns)):
    k = compute_kpis(df)
    st.markdown(
        f"""
- 최신 연도(`{k["latest_year"]}`) 기준, 신재생 비중은 **{k["renewable_share"]:.2f}%** 입니다.
- LNG(복합화력) 비중은 **{k["lng_share"]:.2f}%**, 석탄(기력) 비중은 **{k["coal_share"]:.2f}%** 입니다.
- 에너지 믹스는 화석연료 중심에서 신재생 및 LNG 중심으로 점진적 이동 가능성이 보입니다.
"""
    )
else:
    st.info("에너지 전용 인사이트는 필수 컬럼이 있을 때 생성됩니다.")

st.markdown("---")
st.subheader("데이터 다운로드")

c1, c2 = st.columns(2)
with c1:
    st.download_button(
        "정제 데이터 CSV 다운로드",
        data=to_csv_bytes(df),
        file_name="processed_data.csv",
        mime="text/csv",
    )
with c2:
    st.download_button(
        "정제 데이터 Excel 다운로드",
        data=to_excel_bytes(df, sheet_name="Processed"),
        file_name="processed_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

if "pivot_df" in st.session_state:
    st.markdown("---")
    st.subheader("피벗 결과 다운로드")
    pivot_df = st.session_state["pivot_df"]
    p1, p2 = st.columns(2)
    with p1:
        st.download_button(
            "피벗 CSV 다운로드",
            data=to_csv_bytes(pivot_df),
            file_name="pivot_data.csv",
            mime="text/csv",
        )
    with p2:
        st.download_button(
            "피벗 Excel 다운로드",
            data=to_excel_bytes(pivot_df, sheet_name="Pivot"),
            file_name="pivot_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
