from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.chart_helper import line_actual_plus_forecast
from utils.forecast_helper import forecast_all_sources, forecast_series
from utils.investment_themes import DISCLAIMER, THEMES, get_leading_stock_hint, get_stock_picks
from utils.preprocess_energy import coerce_energy_schema

st.set_page_config(page_title="예측 투자아이디어", layout="wide")

st.markdown(
    """
<style>
.stApp { background: #ffffff; }
.hero-wrap {
  background: linear-gradient(110deg, #f4f8ff 0%, #eef5ff 45%, #eaf4ff 100%);
  border: 1px solid #d7e6ff; border-radius: 16px;
  padding: 20px 24px; margin: 8px 0 18px 0;
}
.hero-title { font-size: 28px; font-weight: 800; color: #10315f; margin-bottom: 6px; }
.hero-sub { color: #375a89; font-size: 14px; }
.hero-chip {
  display: inline-block; margin-top: 12px; margin-right: 8px; padding: 6px 10px;
  border-radius: 999px; background: #dbe9ff; color: #1f4880; font-size: 12px;
}
</style>
<div class="hero-wrap">
  <div class="hero-title">예측 · 투자 아이디어</div>
  <div class="hero-sub">최근 데이터를 학습한 후 향후 성장폭이 큰 분야와 관련 대형주를 추천을 한 화면에서 확인하세요.</div>
  <span class="hero-chip">Forecast</span>
  <span class="hero-chip">Investment Idea</span>
</div>
""",
    unsafe_allow_html=True,
)

st.warning(DISCLAIMER)

if "df" not in st.session_state:
    default_path = Path(__file__).resolve().parents[1] / "HOME_발전·판매_발전량_전원별.xlsx"
    if default_path.exists():
        try:
            auto_raw = pd.read_excel(default_path, header=[0, 1])
            st.session_state["raw_df"] = auto_raw
            st.session_state["df"] = coerce_energy_schema(auto_raw)
            st.session_state["data_filename"] = default_path.name
            st.success(f"기본 데이터 자동 로드 완료: {default_path.name}")
        except Exception as e:
            st.error(f"기본 데이터 자동 로드 실패: {e}")
            st.stop()
    else:
        st.error("기본 데이터 파일을 찾을 수 없습니다: `HOME_발전·판매_발전량_전원별.xlsx`")
        st.stop()

df = st.session_state["df"].copy()
required = {"연도", "수력", "기력", "복합화력", "원자력", "신재생"}
if not required.issubset(df.columns):
    st.error("에너지 스키마 데이터가 필요합니다.")
    st.stop()

energy_cols = ["수력", "기력", "복합화력", "원자력", "신재생"]

col_a, col_b = st.columns(2)
with col_a:
    n_recent = st.slider("학습에 쓸 최근 연수 (N)", min_value=5, max_value=min(30, len(df)), value=min(15, len(df)))
with col_b:
    horizon = st.slider("예측 기간 (년)", min_value=1, max_value=30, value=3)

method = "ets"
try:
    wide, summary, forecast_by_col = forecast_all_sources(
        df, energy_cols, n_recent_years=n_recent, horizon=horizon, method=method
    )
except Exception as e:
    st.error(str(e))
    st.stop()

st.session_state["forecast_wide"] = wide
st.session_state["forecast_summary"] = summary
st.session_state["forecast_by_col"] = forecast_by_col

if "forecast_summary" in st.session_state:
    summary = st.session_state["forecast_summary"]
    forecast_by_col = st.session_state.get("forecast_by_col", {})
    top = summary.iloc[0]
    cagr = top.get("연평균성장률_근사")
    cagr_txt = f"{float(cagr):.2%}" if pd.notna(cagr) else "—"
    pred_cols = [c for c in summary.columns if str(c).endswith("년_예측")]
    pred_val = f"{float(top[pred_cols[0]]):,.0f}" if pred_cols else "—"

    st.subheader("핵심 인사이트")
    ic1, ic2 = st.columns(2)
    with ic1:
        st.metric("가장 상승폭이 큰 분야 (연평균 성장률 근사)", f"{top['에너지원']}", delta=cagr_txt)
    with ic2:
        st.markdown("**해당 분야 참고 대장주(교육용)**")
        st.write(get_leading_stock_hint(str(top["에너지원"])))
    st.caption(f"예측 말년 발전량(해당 전원): {pred_val}")

    st.subheader("에너지원별 발전량 추이 — 실제 + 예측 연장")
    if forecast_by_col:
        fig_all = line_actual_plus_forecast(
            df, forecast_by_col,
            title=f"에너지원별 발전량 추이 (실선: 전체 실제, 점선: 최근 {n_recent}년 학습, {horizon}년 예측)",
        )
        st.plotly_chart(fig_all, use_container_width=True)

    st.subheader("발전원별 향후 성장(연평균 성장률 근사) 순위 — 1위~5위")
    disp = summary.reset_index(drop=True).copy()
    disp.insert(0, "순위", range(1, len(disp) + 1))
    disp_show = disp.copy()
    if "연평균성장률_근사" in disp_show.columns:
        disp_show["연평균성장률_근사"] = disp_show["연평균성장률_근사"].apply(
            lambda x: "" if pd.isna(x) else f"{float(x):.2%}"
        )
    st.dataframe(disp_show, use_container_width=True, hide_index=True)

    st.subheader("투자 테마 참고 — 순위 1위 → 5위 (동일 순서)")
    for rank, (_, row) in enumerate(summary.reset_index(drop=True).iterrows(), start=1):
        src = str(row["에너지원"])
        st.markdown(f"##### {rank}. {src}")
        st.markdown(get_leading_stock_hint(src))
        picks = get_stock_picks(src)
        if picks:
            st.dataframe(pd.DataFrame(picks), use_container_width=True, hide_index=True)
        if src in THEMES:
            with st.expander(f"{rank}위 {src} — 테마 요약", expanded=True):
                for trow in THEMES[src]:
                    st.markdown(f"- **{trow['테마']}**: {trow['예시_국내_대형주_참고']}")
        if rank < len(summary):
            st.divider()
