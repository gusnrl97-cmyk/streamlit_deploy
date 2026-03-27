from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ["연도", "수력", "기력", "복합화력", "원자력", "신재생"]


def remove_unnamed_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep_cols = [c for c in df.columns if not str(c).startswith("Unnamed")]
    return df[keep_cols].copy()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # MultiIndex(2단 헤더)를 납작하게 만들면 이후 매핑 로직이 깨질 수 있음.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = pd.MultiIndex.from_tuples([(str(a).strip(), str(b).strip()) for a, b in df.columns])
    else:
        df.columns = [str(c).strip() for c in df.columns]
    return df


def _flatten_multiindex_columns(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.columns, pd.MultiIndex):
        return df
    out = df.copy()
    new_cols = []
    for c0, c1 in out.columns:
        p0 = str(c0).strip()
        p1 = str(c1).strip()
        parts = [p for p in (p0, p1) if p and p != "nan" and not p.startswith("Unnamed")]
        new_cols.append("_".join(parts) if parts else p0 or p1)
    out.columns = new_cols
    return out


def _use_first_row_as_subheader(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    top = [str(c).strip() for c in df.columns]
    sub = [str(v).strip() for v in df.iloc[0].tolist()]
    new_cols = []
    for a, b in zip(top, sub):
        if b and b != "nan" and not b.startswith("Unnamed"):
            new_cols.append(a if a == b else f"{a}_{b}")
        else:
            new_cols.append(a)
    out = df.iloc[1:].copy()
    out.columns = new_cols
    return out


def _find_column(df: pd.DataFrame, required_keywords: list[str], preferred_keywords: list[str] | None = None) -> str | None:
    preferred_keywords = preferred_keywords or []
    cols = [str(c).replace(" ", "") for c in df.columns]

    matches = []
    for i, col in enumerate(cols):
        if all(k in col for k in required_keywords):
            matches.append((i, col))
    if not matches:
        return None

    if preferred_keywords:
        preferred = [m for m in matches if all(k in m[1] for k in preferred_keywords)]
        if preferred:
            return df.columns[preferred[0][0]]
    return df.columns[matches[0][0]]


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def coerce_energy_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    사용자가 요청한 에너지원 분석 스키마로 맞춘다.
    """
    df = normalize_columns(df)

    # 1) MultiIndex(2단 헤더)인 경우: 각 하위 항목을 정확히 합산/선택
    if isinstance(df.columns, pd.MultiIndex):
        year_candidates = [c for c in df.columns if "연도" in str(c[0]) or "년도" in str(c[0]) or "구분" in str(c[0])]
        year_col = year_candidates[0] if year_candidates else df.columns[0]

        hydro_cols = [c for c in df.columns if "수력" in str(c[0])]
        hydro_total_col = next((c for c in hydro_cols if "소계" in str(c[1])), None)
        if hydro_total_col is not None:
            hydro_total = df[hydro_total_col]
        else:
            hydro_total = df[hydro_cols].sum(axis=1) if hydro_cols else pd.Series([None] * len(df), index=df.index)

        # 사용자 요구: 기력 = 석탄 계열(무연탄 + 유연탄)
        coal_subcols = [
            c
            for c in df.columns
            if "기력" in str(c[0]) and (("무연탄" in str(c[1])) or ("유연탄" in str(c[1])))
        ]
        if not coal_subcols:
            # 대체: "탄" 계열이 포함된 기력(단, '가스'/'중유' 등은 제외되도록 단서 추가)
            coal_subcols = [
                c for c in df.columns if "기력" in str(c[0]) and ("탄" in str(c[1]) and "가스" not in str(c[1]))
            ]
        if not coal_subcols:
            # 최후 fallback: 기력 전체
            coal_subcols = [c for c in df.columns if "기력" in str(c[0])]
        coal_total = df[coal_subcols].sum(axis=1) if coal_subcols else pd.Series([None] * len(df), index=df.index)

        # 복합화력: 기본은 '계(소계)'를 사용하고 없으면 LNG로 대체
        lng_subcols = [c for c in df.columns if ("복합화력" in str(c[0])) and ("계" in str(c[1]))]
        if not lng_subcols:
            lng_subcols = [
                c for c in df.columns if ("복합화력" in str(c[0])) and ("LNG" in str(c[1]))
            ]
        if not lng_subcols:
            lng_subcols = [c for c in df.columns if "복합화력" in str(c[0])]
        lng_total = df[lng_subcols].sum(axis=1) if lng_subcols else pd.Series([None] * len(df), index=df.index)

        nuclear_cols = [c for c in df.columns if "원자력" in str(c[0])]
        nuclear_total = df[nuclear_cols].sum(axis=1) if nuclear_cols else pd.Series([None] * len(df), index=df.index)

        renewable_cols = [c for c in df.columns if "신재생" in str(c[0])]
        # 신재생은 하위 종합 값이 없을 수 있으니 합산으로 total 생성
        renewable_total = df[renewable_cols].sum(axis=1) if renewable_cols else pd.Series([None] * len(df), index=df.index)

        out = pd.DataFrame(
            {
                "연도": df[year_col],
                "수력": hydro_total,
                "기력": coal_total,
                "복합화력": lng_total,
                "원자력": nuclear_total,
                "신재생": renewable_total,
            }
        )
    else:
        # 2) 단일 헤더/기타 구조: 기존 로직 + 일부 보강(석탄/신재생은 합산)
        df = _flatten_multiindex_columns(df)
        df = normalize_columns(df)
        df = _use_first_row_as_subheader(df)
        df = normalize_columns(df)
        df = remove_unnamed_columns(df)

        year_col = _find_column(df, ["연도"]) or _find_column(df, ["년도"]) or _find_column(df, ["구분"])
        if year_col is None:
            year_col = df.columns[0]

        hydro_cols = [c for c in df.columns if "수력" in str(c)]
        hydro_total_col = next((c for c in hydro_cols if "소계" in str(c)), None)
        hydro_total = df[hydro_total_col] if hydro_total_col is not None else df[hydro_cols].sum(axis=1)

        coal_subcols = [c for c in df.columns if "기력" in str(c) and (("무연탄" in str(c)) or ("유연탄" in str(c)))]
        if not coal_subcols:
            coal_subcols = [c for c in df.columns if "기력" in str(c) and ("탄" in str(c) and "가스" not in str(c))]
        if not coal_subcols:
            coal_subcols = [c for c in df.columns if "기력" in str(c)]
        coal_total = df[coal_subcols].sum(axis=1)

        lng_subcols = [c for c in df.columns if ("복합화력" in str(c)) and ("계" in str(c))]
        if not lng_subcols:
            lng_subcols = [c for c in df.columns if ("복합화력" in str(c)) and ("LNG" in str(c))]
        if not lng_subcols:
            lng_subcols = [c for c in df.columns if "복합화력" in str(c)]
        lng_total = df[lng_subcols].sum(axis=1)

        nuclear_cols = [c for c in df.columns if "원자력" in str(c)]
        nuclear_total = df[nuclear_cols].sum(axis=1)

        renewable_cols = [c for c in df.columns if "신재생" in str(c)]
        renewable_total = df[renewable_cols].sum(axis=1)

        out = pd.DataFrame(
            {
                "연도": df[year_col],
                "수력": hydro_total,
                "기력": coal_total,
                "복합화력": lng_total,
                "원자력": nuclear_total,
                "신재생": renewable_total,
            }
        )

    out = out.dropna(subset=["연도"])
    out["연도"] = _to_number(out["연도"])
    for col in REQUIRED_COLUMNS[1:]:
        out[col] = _to_number(out[col])

    # 일부 연도(예: 2024)에서 특정 에너지원 하위 값이 NaN으로 들어오는 경우가 있어,
    # 전체 dropna()를 하면 그 연도 행이 통째로 사라질 수 있다.
    # 따라서 연도는 유지하고, 에너지원 결측은 0으로 채워서 "최신 연도"가 누락되지 않게 한다.
    energy_cols = [c for c in REQUIRED_COLUMNS if c != "연도"]
    out = out.dropna(subset=energy_cols, how="all")
    out[energy_cols] = out[energy_cols].fillna(0)
    out = out[(out["연도"] >= 1900) & (out["연도"] <= 2100)]
    out["연도"] = out["연도"].astype(int)
    out = out.sort_values("연도").reset_index(drop=True)
    return out


def make_share_df(df: pd.DataFrame) -> pd.DataFrame:
    base = df.set_index("연도")
    return base.div(base.sum(axis=1), axis=0)


def make_growth_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.set_index("연도").pct_change()
