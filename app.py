import streamlit as st

from utils.chart_helper import line_generation, line_growth, line_share
from utils.kpi_helper import compute_kpis
from utils.preprocess_energy import coerce_energy_schema, make_growth_df, make_share_df

PREPROCESS_VERSION = 6

st.set_page_config(
    page_title="Energy Insight Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)

# 앱 첫 진입 시 예측 메인 페이지를 랜딩으로 사용
if not st.session_state.get("landing_redirected"):
    st.session_state["landing_redirected"] = True
    st.switch_page("pages/00_예측_투자아이디어.py")

st.title("Energy Insight Dashboard")
st.markdown(
    """
업로드된 CSV/XLSX 데이터를 기반으로 전처리, KPI, 시각화, 피벗 분석까지 진행하는 대시보드입니다.

왼쪽 사이드바에서 페이지를 선택해 진행하세요.
"""
)

# Streamlit Share 호환:
# - 로컬 절대경로 의존 제거
# - 세션에 raw_df가 있으면 재전처리만 수행
if "raw_df" in st.session_state and st.session_state.get("preprocess_version", 0) < PREPROCESS_VERSION:
    try:
        st.session_state["df"] = coerce_energy_schema(st.session_state["raw_df"])
        st.session_state["preprocess_version"] = PREPROCESS_VERSION
    except Exception as e:
        st.warning(f"세션 데이터 재전처리 실패: {e}")

if "df" in st.session_state:
    df = st.session_state["df"].copy()
    required = {"연도", "수력", "기력", "복합화력", "원자력", "신재생"}
    if required.issubset(set(df.columns)):
        # KPI cards (대시보드 맨 위)
        k = compute_kpis(df)
        st.subheader("핵심 KPI")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            delta = (
                f"{k['total_generation_delta_pct']:.2f}%"
                if k["total_generation_delta_pct"] is not None
                else None
            )
            st.metric(
                f"총 발전량 (최신 {k['latest_year']})",
                f"{k['total_generation']:,.0f}",
                delta=delta,
            )
        with c2:
            st.metric("LNG 비중 (%)", f"{k['lng_share']:.2f}%")
        with c3:
            st.metric("신재생 비중 (%)", f"{k['renewable_share']:.2f}%")
        with c4:
            decrease = (
                f"{k['coal_share_decrease_rate_pct']:.2f}%"
                if k["coal_share_decrease_rate_pct"] is not None
                else "-"
            )
            st.metric("석탄 비중 감소율 (%)", decrease)

        st.markdown("---")
        st.subheader("핵심 분석 그래프")
        st.plotly_chart(line_generation(df, "에너지원별 발전량 추이"), use_container_width=True)
        st.plotly_chart(line_share(make_share_df(df), "에너지 믹스 변화 (비중)"), use_container_width=True)
        st.plotly_chart(line_growth(make_growth_df(df), "에너지원별 성장률"), use_container_width=True)
    else:
        st.info("현재 데이터는 에너지 분석 스키마가 아니라서 홈 차트를 표시하지 않습니다.")
else:
    st.info("시작은 `01_업로드_전처리` 페이지에서 파일을 올리는 것부터입니다.")
