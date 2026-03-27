from __future__ import annotations

import streamlit as st
import pandas as pd

from utils.export_helper import to_csv_bytes, to_excel_bytes

st.title("04. 피벗 테이블")

if "df" not in st.session_state:
    st.warning("먼저 `01_업로드_전처리` 페이지에서 데이터를 업로드하세요.")
    st.stop()

df = st.session_state["df"].copy()

all_cols = df.columns.tolist()
numeric_cols = df.select_dtypes(include="number").columns.tolist()

rows = st.multiselect("행(index) 컬럼", all_cols, default=["연도"] if "연도" in all_cols else None)
cols = st.multiselect("열(columns) 컬럼", all_cols)
value_col = st.selectbox("값(values) 컬럼", numeric_cols if numeric_cols else all_cols)
aggfunc = st.selectbox("요약 방식", ["sum", "mean", "count", "max", "min"])

if st.button("피벗 생성"):
    if not rows:
        st.error("최소 1개 이상의 행 컬럼을 선택하세요.")
        st.stop()
    pivot_df = pd.pivot_table(
        df,
        index=rows,
        columns=cols if cols else None,
        values=value_col,
        aggfunc=aggfunc,
        fill_value=0,
    )
    pivot_reset = pivot_df.reset_index()
    st.session_state["pivot_df"] = pivot_reset

if "pivot_df" in st.session_state:
    pivot_df = st.session_state["pivot_df"]
    st.subheader("피벗 결과")
    st.dataframe(pivot_df, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "CSV 다운로드",
            data=to_csv_bytes(pivot_df),
            file_name="pivot_table.csv",
            mime="text/csv",
        )
    with c2:
        st.download_button(
            "Excel 다운로드",
            data=to_excel_bytes(pivot_df, sheet_name="Pivot"),
            file_name="pivot_table.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
