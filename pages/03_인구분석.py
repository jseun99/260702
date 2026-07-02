# -*- coding: utf-8 -*-
"""
🧑‍🤝‍🧑 대한민국 인구 데이터 탐구 대시보드
- KOSIS(통계청) 주민등록 연령별 인구현황(2026년 6월) 데이터를 활용한
  청소년 대상 인구 데이터 리터러시 교육용 대시보드
- Streamlit Community Cloud 배포용
"""

import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# =========================================================
# 0. 기본 설정
# =========================================================
st.set_page_config(
    page_title="대한민국 인구 데이터 탐구 대시보드",
    page_icon="🧑‍🤝‍🧑",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = "data/202606_202606_연령별인구현황_월간.csv"
BASE_YEAR, BASE_MONTH = 2026, 6  # 데이터 기준 시점

# 국가 전체 합계출산율·출생아수 추이 (통계청·국가데이터처 발표 기준, 2025년은 잠정치)
# 출처: 통계청/국가데이터처 「출생통계」, 정책브리핑(2026.02.25 발표) 등 공개 통계 수치를 정리
NATIONAL_TFR = pd.DataFrame(
    {
        "연도": list(range(2015, 2026)),
        "합계출산율": [1.24, 1.17, 1.05, 0.98, 0.92, 0.84, 0.81, 0.78, 0.72, 0.75, 0.80],
        "출생아수(명)": [438420, 406243, 357771, 326822, 302676, 272337,
                     260562, 249186, 230000, 238300, 254500],
    }
)

# 색상 팔레트 (하나로 통일감 있게)
COLOR_MALE = "#4C72B0"
COLOR_FEMALE = "#DD6E7C"
COLOR_ACCENT = "#2E7D6B"
COLOR_WARN = "#E0793C"
COLOR_YOUNG = "#4C9F70"
COLOR_WORK = "#5B8DEF"
COLOR_OLD = "#C96A6A"


# =========================================================
# 1. 데이터 로딩 & 전처리
# =========================================================
@st.cache_data(show_spinner="📂 인구 데이터를 불러오는 중입니다...")
def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="cp949", low_memory=False)
    return df


def _trailing_zeros(code: str) -> int:
    stripped = code.rstrip("0")
    return len(code) - len(stripped)


def _parse_region(region_str: str):
    """'서울특별시  (1100000000)' 같은 문자열을
    (지역명, 코드, 레벨) 로 분해한다.
    레벨은 코드 뒤에 붙은 0의 개수로 판별한다.
      - 시도 레벨   : 뒤에 0이 8개 이상 (예: 1100000000)
      - 시군구 레벨 : 뒤에 0이 5~7개 (예: 1111000000)
      - 읍면동 레벨 : 그 외 (예: 1111051500)
    """
    m = re.search(r"^(.*)\((\d+)\)$", region_str)
    if not m:
        return region_str.strip(), None, "알수없음"
    name_part, code = m.group(1), m.group(2)
    tz = _trailing_zeros(code)
    if tz >= 8:
        level = "시도"
    elif tz >= 5:
        level = "시군구"
    else:
        level = "읍면동"
    return name_part.strip(), code, level


def _parse_columns(columns):
    """'YYYY년MM월_성별_연령' 형태의 컬럼명을 해석해
    (총인구 컬럼 dict, 연령별 컬럼 리스트[(컬럼명, 성별, 나이)]) 를 반환한다."""
    total_cols = {}
    age_cols = []
    pattern = re.compile(r"^\d{4}년\d{2}월_(계|남|여)_(.+)$")
    for c in columns:
        m = pattern.match(c)
        if not m:
            continue
        gender, label = m.group(1), m.group(2)
        if label == "총인구수":
            total_cols[gender] = c
        elif label == "연령구간인구수":
            continue
        else:
            am = re.match(r"^(\d+)세$", label)
            if am:
                age = int(am.group(1))
            elif label.strip() == "100세 이상":
                age = 100
            else:
                continue
            age_cols.append((c, gender, age))
    return total_cols, age_cols


@st.cache_data(show_spinner="🧹 데이터를 정리하는 중입니다...")
def prepare_data(path: str):
    df = load_raw(path)
    total_cols, age_cols = _parse_columns(df.columns)

    numeric_cols = list(total_cols.values()) + [c for c, _, _ in age_cols]
    for c in numeric_cols:
        df[c] = (
            df[c].astype(str).str.replace(",", "", regex=False).str.strip()
        )
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(np.int64)

    parsed = df["행정구역"].apply(_parse_region)
    df["지역명"] = parsed.apply(lambda x: x[0])
    df["지역코드"] = parsed.apply(lambda x: x[1])
    df["레벨"] = parsed.apply(lambda x: x[2])
    df["총인구수"] = df[total_cols.get("계", df.columns[0])]

    tokens = df["지역명"].str.split(" ")
    df["시도"] = tokens.apply(lambda t: t[0] if len(t) >= 1 else None)

    # 시군구 레벨인데 지역명이 시도명과 동일한 경우(세종 특수 케이스 등)는
    # UI 혼동을 막기 위해 별도 표시하지 않는다.
    df["시군구_표시"] = None
    mask_sgg = (df["레벨"] == "시군구") & (df["지역명"] != df["시도"])
    df.loc[mask_sgg, "시군구_표시"] = df.loc[mask_sgg, "지역명"]

    df = df.copy()  # 컬럼을 여러 번 추가해 조각난 프레임을 정리(성능 최적화)
    return df, total_cols, age_cols


def clean_data_status(path: str):
    try:
        df, total_cols, age_cols = prepare_data(path)
        return df, total_cols, age_cols, None
    except FileNotFoundError:
        return None, None, None, (
            f"⚠️ 데이터 파일을 찾을 수 없습니다: `{path}`\n\n"
            "저장소(repo)의 `data/` 폴더에 원본 CSV 파일을 함께 업로드했는지 확인해주세요."
        )
    except Exception as e:  # noqa: BLE001
        return None, None, None, f"⚠️ 데이터 로딩 중 오류가 발생했습니다: {e}"


# =========================================================
# 2. 계산 유틸
# =========================================================
def age_distribution(df, age_cols, mask, genders=("계",)):
    """선택된 행(mask)들에 대해 성별을 합산한 연령별 인구수를 반환한다."""
    sub = df.loc[mask]
    agg = {}
    for col, gender, age in age_cols:
        if gender in genders:
            agg[age] = agg.get(age, 0) + int(sub[col].sum())
    ages = sorted(agg.keys())
    return pd.DataFrame({"연령": ages, "인구수": [agg[a] for a in ages]})


def pyramid_table(df, age_cols, mask):
    male = age_distribution(df, age_cols, mask, genders=("남",)).rename(columns={"인구수": "남성"})
    female = age_distribution(df, age_cols, mask, genders=("여",)).rename(columns={"인구수": "여성"})
    merged = pd.merge(male, female, on="연령", how="outer").fillna(0).sort_values("연령")
    merged["남성"] = merged["남성"].astype(int)
    merged["여성"] = merged["여성"].astype(int)
    return merged


def demographic_indices(age_df: pd.DataFrame) -> dict:
    """연령별 인구수 표(연령, 인구수)로부터 유소년/생산연령/고령 지표를 계산한다."""
    total = age_df["인구수"].sum()
    if total == 0:
        return {k: 0 for k in
                ["유소년인구", "생산연령인구", "고령인구", "총인구",
                 "고령화지수", "유소년부양비", "노년부양비", "총부양비",
                 "유소년비율", "고령비율", "중위연령"]}

    young = age_df.loc[age_df["연령"] <= 14, "인구수"].sum()
    work = age_df.loc[(age_df["연령"] >= 15) & (age_df["연령"] <= 64), "인구수"].sum()
    old = age_df.loc[age_df["연령"] >= 65, "인구수"].sum()

    aging_index = (old / young * 100) if young > 0 else np.nan
    youth_dep = (young / work * 100) if work > 0 else np.nan
    old_dep = (old / work * 100) if work > 0 else np.nan
    total_dep = youth_dep + old_dep if work > 0 else np.nan

    # 중위연령 계산: 0세부터 누적 인구가 전체의 50%를 넘는 지점
    sorted_df = age_df.sort_values("연령")
    cum = sorted_df["인구수"].cumsum()
    half = total / 2
    median_age_row = sorted_df.loc[cum >= half].iloc[0] if (cum >= half).any() else sorted_df.iloc[-1]
    median_age = median_age_row["연령"]

    return {
        "유소년인구": int(young),
        "생산연령인구": int(work),
        "고령인구": int(old),
        "총인구": int(total),
        "고령화지수": aging_index,
        "유소년부양비": youth_dep,
        "노년부양비": old_dep,
        "총부양비": total_dep,
        "유소년비율": young / total * 100,
        "고령비율": old / total * 100,
        "중위연령": median_age,
    }


def fmt_int(x):
    try:
        return f"{int(round(x)):,}"
    except (ValueError, TypeError):
        return "-"


def fmt_pct(x, digit=1):
    try:
        return f"{x:.{digit}f}%"
    except (ValueError, TypeError):
        return "-"


# =========================================================
# 3. 지역 선택 UI (사이드바)
# =========================================================
def region_selector(df: pd.DataFrame, key_prefix: str):
    """사이드바 등에서 재사용하는 지역 선택 위젯.
    반환값: (표시용 라벨, 해당 지역을 가리키는 boolean mask)
    """
    sido_rows = df[df["레벨"] == "시도"]
    sido_list = list(pd.unique(sido_rows["지역명"]))

    scope = st.radio(
        "분석 범위 선택",
        ["🇰🇷 전국", "🏙️ 시/도", "🏘️ 시/군/구", "🏠 읍/면/동"],
        horizontal=False,
        key=f"{key_prefix}_scope",
    )

    if scope == "🇰🇷 전국":
        mask = df["레벨"] == "시도"  # 17개 시도를 모두 더하면 전국 총계
        return "전국", mask

    sido_choice = st.selectbox("시/도 선택", sido_list, key=f"{key_prefix}_sido")

    if scope == "🏙️ 시/도":
        mask = (df["레벨"] == "시도") & (df["지역명"] == sido_choice)
        return sido_choice, mask

    sgg_candidates = df[
        (df["레벨"] == "시군구") & (df["시도"] == sido_choice) & df["시군구_표시"].notna()
    ]
    sgg_list = list(pd.unique(sgg_candidates["지역명"]))

    if not sgg_list:
        st.caption("ℹ️ 이 시/도는 시/군/구 구분 없이 읍/면/동으로 바로 구성되어 있어요.")
        emd_candidates = df[(df["레벨"] == "읍면동") & (df["시도"] == sido_choice)]
        emd_list = list(pd.unique(emd_candidates["지역명"]))
        if scope == "🏘️ 시/군/구" or not emd_list:
            mask = (df["레벨"] == "시도") & (df["지역명"] == sido_choice)
            return sido_choice, mask
        emd_choice = st.selectbox(
            "읍/면/동 선택", emd_list, key=f"{key_prefix}_emd_direct",
            format_func=lambda x: x.replace(sido_choice, "").strip(),
        )
        mask = (df["레벨"] == "읍면동") & (df["지역명"] == emd_choice)
        return emd_choice, mask

    sgg_choice = st.selectbox(
        "시/군/구 선택", sgg_list, key=f"{key_prefix}_sgg",
        format_func=lambda x: x.replace(sido_choice, "").strip(),
    )

    if scope == "🏘️ 시/군/구":
        mask = (df["레벨"] == "시군구") & (df["지역명"] == sgg_choice)
        return sgg_choice, mask

    emd_candidates = df[(df["레벨"] == "읍면동") & (df["지역명"].str.startswith(sgg_choice))]
    emd_list = list(pd.unique(emd_candidates["지역명"]))
    if not emd_list:
        st.caption("ℹ️ 하위 읍/면/동 데이터가 없어 시/군/구 데이터를 표시합니다.")
        mask = (df["레벨"] == "시군구") & (df["지역명"] == sgg_choice)
        return sgg_choice, mask

    emd_choice = st.selectbox(
        "읍/면/동 선택", emd_list, key=f"{key_prefix}_emd",
        format_func=lambda x: x.replace(sgg_choice, "").strip(),
    )
    mask = (df["레벨"] == "읍면동") & (df["지역명"] == emd_choice)
    return emd_choice, mask


# =========================================================
# 4. 앱 본문
# =========================================================
def main():
    df, total_cols, age_cols, err = clean_data_status(DATA_PATH)

    st.title("🧑‍🤝‍🧑 대한민국 인구 데이터 탐구 대시보드")
    st.caption(
        f"📅 데이터 기준: **{BASE_YEAR}년 {BASE_MONTH}월** 주민등록 인구현황(통계청 KOSIS) "
        "· 함께 인구 구조를 읽고, 우리 동네와 대한민국의 이야기를 데이터로 확인해봐요 ✨"
    )

    if err:
        st.error(err)
        st.stop()

    with st.sidebar:
        st.header("🔎 탐색 설정")
        st.markdown("아래에서 살펴보고 싶은 지역을 선택하세요. "
                     "탭마다 이 지역 선택이 함께 적용됩니다.")
        region_label, region_mask = region_selector(df, key_prefix="main")
        st.markdown("---")
        with st.expander("📚 용어 사전 (헷갈릴 때 클릭!)"):
            st.markdown(
                """
- **합계출산율(TFR)**: 여성 1명이 평생 낳을 것으로 예상되는 평균 자녀 수
- **유소년인구**: 0~14세 인구
- **생산연령인구**: 15~64세 인구 (일할 수 있는 나이)
- **고령인구**: 65세 이상 인구
- **고령화지수**: 유소년인구 100명당 고령인구 수 `(고령인구/유소년인구)×100`
- **노년부양비**: 생산연령인구 100명이 부양해야 하는 고령인구 수
- **중위연령**: 전체 인구를 나이순으로 세웠을 때 정확히 가운데에 있는 사람의 나이
                """
            )
        st.markdown("---")
        st.caption("Made with ❤️ using Streamlit + Plotly · 데이터: 통계청 KOSIS")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🗺️ 전국 개요", "🧑‍🤝‍🧑 인구 피라미드", "👶 출생 반등 인사이트",
         "⚖️ 지역 비교", "📊 데이터 탐색기"]
    )

    with tab1:
        render_overview(df)

    with tab2:
        render_pyramid(df, age_cols, region_label, region_mask)

    with tab3:
        render_birth_insight(df, age_cols, region_label, region_mask)

    with tab4:
        render_compare(df, age_cols)

    with tab5:
        render_explorer(df, total_cols, region_label, region_mask)


# ---------------------------------------------------------
# 탭 1. 전국 개요
# ---------------------------------------------------------
def render_overview(df):
    st.subheader("🗺️ 대한민국 시/도별 인구 한눈에 보기")
    st.markdown(
        "우리나라는 17개의 시/도로 이루어져 있어요. 아래 그래프로 어느 지역에 "
        "사람이 많이 사는지 살펴볼까요?"
    )

    sido_df = df[df["레벨"] == "시도"].copy().sort_values("총인구수", ascending=False)
    total_national = sido_df["총인구수"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("🇰🇷 전국 총인구", f"{fmt_int(total_national)}명")
    c2.metric("🏙️ 인구 최다 시/도", sido_df.iloc[0]["지역명"], f"{fmt_int(sido_df.iloc[0]['총인구수'])}명")
    c3.metric("🏞️ 인구 최소 시/도", sido_df.iloc[-1]["지역명"], f"{fmt_int(sido_df.iloc[-1]['총인구수'])}명")

    fig_bar = px.bar(
        sido_df,
        x="총인구수", y="지역명",
        orientation="h",
        text=sido_df["총인구수"].apply(fmt_int),
        color="총인구수",
        color_continuous_scale=["#CDE7DD", COLOR_ACCENT],
        title=f"{BASE_YEAR}년 {BASE_MONTH}월 시/도별 총인구",
    )
    fig_bar.update_layout(
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
        height=560,
        margin=dict(l=10, r=10, t=60, b=10),
        xaxis_title="총인구수(명)", yaxis_title=None,
    )
    fig_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### 🧩 시/도 → 시/군/구 인구 구조 (트리맵)")
    st.markdown(
        "사각형이 클수록 인구가 많은 지역이에요. 마우스를 올리면 자세한 숫자가 나오고, "
        "클릭하면 해당 시/도 내부를 확대해서 볼 수 있어요."
    )
    sgg_df = df[(df["레벨"] == "시군구") & df["시군구_표시"].notna()].copy()
    sgg_df["시군구_이름"] = sgg_df.apply(
        lambda r: r["지역명"].replace(r["시도"], "").strip(), axis=1
    )
    sgg_df = sgg_df[sgg_df["총인구수"] > 0]

    fig_tree = px.treemap(
        sgg_df,
        path=[px.Constant("대한민국"), "시도", "시군구_이름"],
        values="총인구수",
        color="시도",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_tree.update_traces(
        textinfo="label+value",
        texttemplate="%{label}<br>%{value:,}명",
    )
    fig_tree.update_layout(height=560, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_tree, use_container_width=True)

    st.info(
        "💡 **선생님 Tip** : 수도권(서울·인천·경기)에 우리나라 인구의 상당 부분이 "
        "몰려 있는 것을 확인할 수 있어요. 이런 현상을 **인구의 수도권 집중**이라고 부릅니다. "
        "학생들과 함께 '왜 특정 지역에 인구가 몰릴까?'를 토론해보세요."
    )


# ---------------------------------------------------------
# 탭 2. 인구 피라미드
# ---------------------------------------------------------
def render_pyramid(df, age_cols, region_label, region_mask):
    st.subheader(f"🧑‍🤝‍🧑 인구 피라미드 — {region_label}")
    st.markdown(
        "인구 피라미드는 왼쪽엔 남성, 오른쪽엔 여성 인구를 나이별로 쌓아 올린 그래프예요. "
        "모양만 보고도 그 지역이 '젊은 도시'인지 '고령화된 도시'인지 짐작할 수 있답니다."
    )

    pt = pyramid_table(df, age_cols, region_mask)
    if pt.empty or pt[["남성", "여성"]].sum().sum() == 0:
        st.warning("선택한 지역의 연령별 데이터가 없어요. 다른 지역을 선택해보세요.")
        return

    all_age = age_distribution(df, age_cols, region_mask, genders=("계",))
    idx = demographic_indices(all_age)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=pt["연령"], x=-pt["남성"], name="남성", orientation="h",
        marker_color=COLOR_MALE,
        hovertemplate="만 %{y}세 · 남성 %{customdata:,}명<extra></extra>",
        customdata=pt["남성"],
    ))
    fig.add_trace(go.Bar(
        y=pt["연령"], x=pt["여성"], name="여성", orientation="h",
        marker_color=COLOR_FEMALE,
        hovertemplate="만 %{y}세 · 여성 %{x:,}명<extra></extra>",
    ))
    max_val = max(pt["남성"].max(), pt["여성"].max())
    fig.update_layout(
        barmode="overlay",
        bargap=0.1,
        title=f"{region_label} 인구 피라미드 ({BASE_YEAR}년 {BASE_MONTH}월)",
        xaxis=dict(
            title="인구수(명)",
            tickvals=[-max_val, -max_val/2, 0, max_val/2, max_val],
            ticktext=[fmt_int(max_val), fmt_int(max_val/2), "0", fmt_int(max_val/2), fmt_int(max_val)],
        ),
        yaxis=dict(title="만 나이"),
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=80, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 📈 인구 구조 지표")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("중위연령", f"만 {fmt_int(idx['중위연령'])}세")
    c2.metric("고령화지수", fmt_int(idx["고령화지수"]) if idx["고령화지수"] == idx["고령화지수"] else "-")
    c3.metric("노년부양비", fmt_pct(idx["노년부양비"]))
    c4.metric("유소년부양비", fmt_pct(idx["유소년부양비"]))

    ratio_df = pd.DataFrame({
        "구분": ["유소년(0~14세)", "생산연령(15~64세)", "고령(65세이상)"],
        "인구수": [idx["유소년인구"], idx["생산연령인구"], idx["고령인구"]],
    })
    fig_pie = px.pie(
        ratio_df, names="구분", values="인구수", hole=0.5,
        color="구분",
        color_discrete_map={
            "유소년(0~14세)": COLOR_YOUNG,
            "생산연령(15~64세)": COLOR_WORK,
            "고령(65세이상)": COLOR_OLD,
        },
    )
    fig_pie.update_traces(textinfo="label+percent")
    fig_pie.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10),
                           title="연령대별 인구 구성비")
    st.plotly_chart(fig_pie, use_container_width=True)

    # 고령사회 단계 판정 (UN/통계청 기준: 고령인구 비율 7%~14%~20%)
    old_ratio = idx["고령비율"]
    if old_ratio >= 20:
        stage, msg = "초고령사회 🔴", "전체 인구 중 65세 이상이 20% 이상으로, 초고령사회에 해당해요."
    elif old_ratio >= 14:
        stage, msg = "고령사회 🟠", "전체 인구 중 65세 이상이 14~20%로, 고령사회에 해당해요."
    elif old_ratio >= 7:
        stage, msg = "고령화사회 🟡", "전체 인구 중 65세 이상이 7~14%로, 고령화사회에 해당해요."
    else:
        stage, msg = "청년사회 🟢", "아직 고령인구 비율이 7% 미만인, 상대적으로 젊은 지역이에요."
    st.success(f"**이 지역의 단계 : {stage}** — {msg} (고령인구 비율 {fmt_pct(old_ratio)})")


# ---------------------------------------------------------
# 탭 3. 출생 반등 인사이트  (핵심 탭)
# ---------------------------------------------------------
def render_birth_insight(df, age_cols, region_label, region_mask):
    st.subheader("👶 대한민국 출생율 반등 이야기")
    st.markdown(
        """
    2015년부터 계속 떨어지기만 하던 우리나라 합계출산율이, 최근 흥미로운 반전을 맞이했어요.
    이 탭에서는 **실제 공개 통계**와 **업로드하신 인구 데이터에 숨어있는 흔적**을 함께 살펴보며,
    데이터로 사회 현상을 읽는 법을 연습해볼게요. 🕵️
        """
    )

    # --- 1) 국가 통계 추이 ---
    st.markdown("#### 1️⃣ 진짜로 반등했을까? — 국가 통계로 확인하기")
    fig_tfr = go.Figure()
    fig_tfr.add_trace(go.Scatter(
        x=NATIONAL_TFR["연도"], y=NATIONAL_TFR["합계출산율"],
        mode="lines+markers+text", name="합계출산율(명)",
        line=dict(color=COLOR_WARN, width=3),
        text=NATIONAL_TFR["합계출산율"], textposition="top center",
        yaxis="y1",
    ))
    fig_tfr.add_trace(go.Bar(
        x=NATIONAL_TFR["연도"], y=NATIONAL_TFR["출생아수(명)"],
        name="출생아수(명)", marker_color="#BFD7EA", opacity=0.7,
        yaxis="y2",
    ))
    fig_tfr.update_layout(
        title="대한민국 합계출산율 · 출생아수 추이 (2015~2025, 통계청·국가데이터처)",
        xaxis=dict(title="연도", dtick=1),
        yaxis=dict(title="합계출산율(명)", side="left"),
        yaxis2=dict(title="출생아수(명)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
        height=460, margin=dict(l=10, r=10, t=70, b=10),
    )
    # 2023년 저점, 2024·2025년 반등 구간 강조
    fig_tfr.add_vrect(x0=2022.5, x1=2023.5, fillcolor="#E0793C", opacity=0.12,
                       line_width=0, annotation_text="역대 최저(0.72)", annotation_position="top left")
    fig_tfr.add_vrect(x0=2023.5, x1=2025.5, fillcolor="#2E7D6B", opacity=0.10,
                       line_width=0, annotation_text="2년 연속 반등", annotation_position="top right")
    st.plotly_chart(fig_tfr, use_container_width=True)

    st.caption(
        "📌 2023년 합계출산율 0.72명(역대 최저) → 2024년 0.75명 → 2025년 0.80명(잠정)으로 "
        "**2년 연속 반등**했습니다. 2025년 출생아 수는 25만 4,500명으로 전년 대비 6.8% 늘었어요."
    )

    # --- 2) 코호트(연령별 인구) 로 확인하는 반등의 흔적 ---
    st.markdown("---")
    st.markdown(f"#### 2️⃣ 업로드한 데이터에서도 반등의 흔적을 찾을 수 있을까? — {region_label}")
    st.markdown(
        """
    이 데이터는 **2026년 6월 한 시점**의 스냅샷이라서 "연도별 출생아 수"를 직접 보여주지는 않아요.
    하지만 힌트가 있어요! **나이가 어릴수록 그 나이만큼 최근에 태어났다는 뜻**이므로,
    0세~9세처럼 어린 연령대의 인구수를 비교하면 최근 몇 년간 태어난 아기 수의 변화를
    간접적으로 추정할 수 있습니다. (물론 전입·전출 등 다른 요인도 섞여 있을 수 있어 **참고용 추정**이에요.)
        """
    )

    young_df = age_distribution(df, age_cols, region_mask, genders=("계",))
    young_df = young_df[young_df["연령"] <= 9].copy()

    if young_df.empty or young_df["인구수"].sum() == 0:
        st.warning("선택한 지역의 0~9세 데이터가 부족해요. 인구가 더 많은 지역(예: 전국, 시/도)을 선택해보세요.")
    else:
        young_df["추정 출생년도(대략)"] = young_df["연령"].apply(lambda a: f"~{BASE_YEAR - a}년")
        min_row = young_df.loc[young_df["인구수"].idxmin()]

        colors = [COLOR_WARN if a == min_row["연령"] else COLOR_ACCENT for a in young_df["연령"]]
        fig_cohort = go.Figure(go.Bar(
            x=young_df["연령"], y=young_df["인구수"],
            marker_color=colors,
            text=young_df["인구수"].apply(fmt_int), textposition="outside",
            hovertemplate="만 %{x}세 (대략 %{customdata} 출생) · %{y:,}명<extra></extra>",
            customdata=young_df["추정 출생년도(대략)"],
        ))
        fig_cohort.update_layout(
            title=f"{region_label} — 0~9세 연령별 인구수",
            xaxis=dict(title="만 나이", dtick=1),
            yaxis=dict(title="인구수(명)"),
            height=440, margin=dict(l=10, r=10, t=60, b=10),
        )
        st.plotly_chart(fig_cohort, use_container_width=True)

        if min_row["연령"] not in (0, young_df["연령"].max()):
            st.success(
                f"🔍 **발견!** {region_label}에서는 **만 {int(min_row['연령'])}세** 인구가 0~9세 중 "
                f"가장 적어요({fmt_int(min_row['인구수'])}명). 이 나이보다 **더 어린 연령(0~{int(min_row['연령'])-1}세)** "
                "의 인구가 다시 늘어난다면, 이는 최근 출생아 수가 반등했다는 신호로 해석할 수 있어요! "
                "실제로 전국 데이터에서는 만 2세(2023년 무렵 출생, 역대 최저 출산율 시기) 인구가 가장 적고, "
                "0~1세 인구가 다시 늘어나는 모습이 뚜렷하게 나타납니다."
            )
        else:
            st.info(
                "이 지역은 표본 인구가 적어 뚜렷한 저점이 보이지 않을 수 있어요. "
                "'전국'이나 인구가 많은 시/도를 선택하면 반등의 흔적이 더 잘 보입니다."
            )

    # --- 3) 에코붐 세대 ---
    st.markdown("---")
    st.markdown("#### 3️⃣ 반등의 숨은 주인공 — '2차 에코붐 세대'")
    st.markdown(
        f"""
    최근 출산율 반등의 배경에는 **1991~1996년생('2차 에코붐 세대')**이 30대에 접어들며
    결혼·출산이 늘어난 영향이 크다는 분석이 있어요. 이 세대는 한 해 약 70만 명씩 태어나
    바로 윗세대(1980년대 후반생, 약 60만 명대)보다 인구가 많습니다. {BASE_YEAR}년 기준
    이들은 만 **{BASE_YEAR-1996}~{BASE_YEAR-1991}세**에 해당해요.
        """
    )
    adult_df = age_distribution(df, age_cols, region_mask, genders=("계",))
    adult_df = adult_df[(adult_df["연령"] >= 20) & (adult_df["연령"] <= 49)].copy()

    if not adult_df.empty and adult_df["인구수"].sum() > 0:
        eco_lo, eco_hi = BASE_YEAR - 1996, BASE_YEAR - 1991
        colors2 = [COLOR_WARN if eco_lo <= a <= eco_hi else "#B8C4D0" for a in adult_df["연령"]]
        fig_eco = go.Figure(go.Bar(
            x=adult_df["연령"], y=adult_df["인구수"], marker_color=colors2,
            hovertemplate="만 %{x}세 · %{y:,}명<extra></extra>",
        ))
        fig_eco.add_vrect(x0=eco_lo - 0.5, x1=eco_hi + 0.5, fillcolor=COLOR_WARN, opacity=0.08,
                           line_width=0, annotation_text="2차 에코붐 세대", annotation_position="top")
        fig_eco.update_layout(
            title=f"{region_label} — 20~49세 인구 분포 (혼인·출산 주요 연령대)",
            xaxis=dict(title="만 나이", dtick=2),
            yaxis=dict(title="인구수(명)"),
            height=440, margin=dict(l=10, r=10, t=60, b=10),
        )
        st.plotly_chart(fig_eco, use_container_width=True)
        st.caption(
            f"🟧 주황색으로 표시된 만 {eco_lo}~{eco_hi}세 구간이 '2차 에코붐 세대'예요. "
            "이 구간이 주변 연령대보다 볼록하게 튀어나와 있는지 확인해보세요."
        )

    with st.expander("🎓 선생님을 위한 수업 포인트 더 보기"):
        st.markdown(
            """
- **인과관계 vs 상관관계**: 에코붐 세대의 존재와 출산율 반등이 동시에 일어났다고 해서
  100% 원인이라고 단정할 수는 없어요. 혼인 증가, 결혼·출산에 대한 인식 변화, 정책 효과 등
  여러 요인이 함께 작용했습니다. 학생들과 "이 데이터만으로 원인을 확신할 수 있을까?"를 토론해보세요.
- **지역 데이터 vs 전국 데이터**: 인구가 적은 읍/면/동 단위에서는 우연한 변동(노이즈)이
  커서 전국 수준의 패턴이 안 보일 수 있어요. 표본 크기와 데이터 신뢰도의 관계를 설명하기 좋은 예시입니다.
- **스냅샷 데이터의 한계**: 이 대시보드의 원본 데이터는 특정 시점(1개월) 자료이기 때문에,
  실제 "연도별 출생아 수" 통계와는 다르게 코호트 크기로 '추정'만 가능하다는 점을 꼭 짚어주세요.
            """
        )


# ---------------------------------------------------------
# 탭 4. 지역 비교
# ---------------------------------------------------------
def render_compare(df, age_cols):
    st.subheader("⚖️ 시/도별 인구 구조 비교하기")
    st.markdown("비교하고 싶은 시/도를 2곳 이상 선택해보세요. 어느 지역이 더 '젊은지', '고령화됐는지' 한눈에 비교할 수 있어요.")

    sido_list = list(pd.unique(df[df["레벨"] == "시도"]["지역명"]))
    default_sel = [s for s in ["서울특별시", "전라남도", "세종특별자치시"] if s in sido_list][:3] or sido_list[:3]
    selected = st.multiselect("비교할 시/도 선택 (2개 이상 권장)", sido_list, default=default_sel)

    if not selected:
        st.info("👆 비교할 지역을 1개 이상 선택해주세요.")
        return

    rows = []
    for sido in selected:
        mask = (df["레벨"] == "시도") & (df["지역명"] == sido)
        ad = age_distribution(df, age_cols, mask, genders=("계",))
        idx = demographic_indices(ad)
        rows.append({
            "지역": sido,
            "총인구": idx["총인구"],
            "유소년비율(%)": round(idx["유소년비율"], 1),
            "고령비율(%)": round(idx["고령비율"], 1),
            "중위연령": idx["중위연령"],
            "고령화지수": round(idx["고령화지수"], 1) if idx["고령화지수"] == idx["고령화지수"] else None,
            "노년부양비": round(idx["노년부양비"], 1),
        })
    comp_df = pd.DataFrame(rows)

    col_a, col_b = st.columns(2)
    with col_a:
        fig1 = px.bar(
            comp_df.sort_values("고령비율(%)"), x="고령비율(%)", y="지역",
            orientation="h", color="고령비율(%)",
            color_continuous_scale=["#CDE7DD", COLOR_OLD],
            title="고령인구 비율(65세 이상) 비교",
            text="고령비율(%)",
        )
        fig1.update_layout(coloraxis_showscale=False, height=420, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig1, use_container_width=True)
    with col_b:
        fig2 = px.bar(
            comp_df.sort_values("유소년비율(%)"), x="유소년비율(%)", y="지역",
            orientation="h", color="유소년비율(%)",
            color_continuous_scale=["#F4DCC8", COLOR_YOUNG],
            title="유소년인구 비율(0~14세) 비교",
            text="유소년비율(%)",
        )
        fig2.update_layout(coloraxis_showscale=False, height=420, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### 🕸️ 종합 비교 (레이더 차트)")
    radar_metrics = ["유소년비율(%)", "고령비율(%)", "노년부양비", "고령화지수"]
    fig_radar = go.Figure()
    for _, r in comp_df.iterrows():
        vals = [r[m] if r[m] is not None else 0 for m in radar_metrics]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=radar_metrics + [radar_metrics[0]],
            fill="toself", name=r["지역"],
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True, height=520, margin=dict(l=40, r=40, t=40, b=40),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("#### 📋 요약 표")
    show_df = comp_df.copy()
    show_df["총인구"] = show_df["총인구"].apply(fmt_int)
    st.dataframe(show_df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------
# 탭 5. 데이터 탐색기
# ---------------------------------------------------------
def render_explorer(df, total_cols, region_label, region_mask):
    st.subheader("📊 원자료 탐색기")
    st.markdown("선택한 지역 범위에 포함된 원본 데이터 행을 직접 확인하고 CSV로 내려받을 수 있어요.")

    show_cols = ["지역명", "레벨", "총인구수"]
    result = df.loc[region_mask, show_cols].sort_values("총인구수", ascending=False).reset_index(drop=True)
    result["총인구수"] = result["총인구수"].apply(fmt_int)

    st.dataframe(result, use_container_width=True, height=420)
    st.caption(f"현재 선택 범위: **{region_label}** · 총 {len(result)}개 행")

    csv_bytes = df.loc[region_mask, show_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ 선택 범위 데이터 CSV로 내려받기",
        data=csv_bytes,
        file_name=f"population_{region_label}.csv",
        mime="text/csv",
    )

    with st.expander("🗂️ 전체 원본 컬럼 미리보기 (상위 20행)"):
        st.dataframe(pd.read_csv(DATA_PATH, encoding="cp949", nrows=20, low_memory=False))


if __name__ == "__main__":
    main()
