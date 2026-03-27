from __future__ import annotations

import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def get_excel_sheet_names(uploaded_file) -> list[str]:
    uploaded_file.seek(0)
    xls = pd.ExcelFile(uploaded_file)
    return xls.sheet_names


@st.cache_data(show_spinner=False)
def load_dataframe(uploaded_file, file_ext: str, sheet_name: str | None = None) -> pd.DataFrame:
    uploaded_file.seek(0)
    if file_ext == "csv":
        return pd.read_csv(uploaded_file)
    if file_ext in ("xlsx", "xls"):
        # 이 프로젝트 대상 엑셀은 2단 헤더(상위: 에너지원, 하위: 합계/하위종류) 구조인 경우가 많음
        # MultiIndex가 유지되어 전처리에서 정확한 매핑이 가능
        return pd.read_excel(uploaded_file, sheet_name=sheet_name, header=[0, 1])
    raise ValueError(f"지원하지 않는 확장자입니다: {file_ext}")


def get_file_ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
