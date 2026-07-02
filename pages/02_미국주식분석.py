import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ----------------------------------------
# 기본 설정
# ----------------------------------------
st.set_page_config(page_title="미국 주식 데이터 분석 대시보드", layout="wide")

# ----------------------------------------
# 미국 주요 종목 목록 (yfinance는 티커를 그대로 사용, 별도 접미사 불필요)
# ----------------------------------------
US_STOCKS = {
    "애플 (Apple)": "AAPL",
    "마이크로소프트 (Microsoft)": "MSFT",
    "엔비디아 (NVIDIA)": "NVDA",
    "알파벳/구글 (Alphabet)": "GOOGL",
    "아마존 (Amazon)": "AMZN",
    "메타 (Meta)": "META",
    "테슬라 (Tesla)": "TSLA",
    "브로드컴 (Broadcom)": "AVGO",
    "넷플릭스 (Netflix)": "NFLX",
    "어도비 (Adobe)": "ADBE",
    "세일즈포스 (Salesforce)": "CRM",
    "AMD": "AMD",
    "인텔 (Intel)": "INTC",
    "퀄컴 (Qualcomm)": "QCOM",
    "팔란티어 (Palantir)": "PLTR",
    "코카콜라 (Coca-Cola)": "KO",
    "존슨앤드존슨 (Johnson & Johnson)": "JNJ",
    "JP모건 (JPMorgan Chase)": "JPM",
    "비자 (Visa)": "V",
    "마스터카드 (Mastercard)": "MA",
    "월마트 (Walmart)": "WMT",
    "디즈니 (Disney)": "DIS",
    "나이키 (Nike)": "NKE",
    "스타벅스 (Starbucks)": "SBUX",
    "보잉 (Boeing)": "BA",
    "엑슨모빌 (ExxonMobil)": "XOM",
    "버크셔 해서웨이 (Berkshire Hathaway)": "BRK-B",
    "코스트코 (Costco)": "COST",
    "펩시코 (PepsiCo)": "PEP",
    "맥도날드 (McDonald's)": "MCD",
}

# 비교용 벤치마크 지수/ETF
INDEX_MAP = {
    "S&P 500 (SPY)": "SPY",
    "나스닥 100 (QQQ)": "QQQ",
    "다우존스 (DIA)": "DIA",
}

TERM_EXPLANATIONS = {
    "캔들차트(봉차트)": "하루(또는 특정 기간) 동안의 시가·고가·저가·종가를 하나의 막대(봉)로 표시한 차트예요. "
                    "봉이 초록색이면 시가보다 종가가 더 높게 마감(상승), 빨간색이면 종가가 더 낮게 마감(하락)한 걸 의미해요. "
                    "(미국 주식 차트는 관례적으로 상승은 초록, 하락은 빨강으로 표시하는 경우가 많아요.) "
                    "위아래로 뻗은 얇은 선은 그날의 최고가와 최저가를 보여줍니다.",
    "이동평균선(MA)": "최근 N일 동안의 종가를 평균 낸 값을 이어서 그린 선이에요. 예를 들어 '20일 이동평균선'은 최근 20거래일 종가의 평균을 매일 계산해 이은 선입니다. "
                   "주가의 큰 흐름(추세)을 부드럽게 보여주는 역할을 해요.",
    "거래량": "해당 기간 동안 실제로 사고 팔린 주식의 수량이에요. 거래량이 갑자기 늘어나면 그만큼 많은 투자자들이 관심을 갖고 매매에 나섰다는 신호로 해석되기도 해요.",
    "시가/고가/저가/종가": "시가는 장이 시작할 때의 가격, 종가는 장이 마감할 때의 가격이에요. 고가와 저가는 각각 그 기간 중 가장 높았던 가격과 가장 낮았던 가격을 뜻합니다.",
    "등락률": "전날 종가 대비 오늘 종가가 몇 퍼센트(%) 올랐는지 또는 내렸는지를 나타낸 값이에요.",
    "52주 최고/최저가": "최근 1년(52주) 동안 기록한 가장 높은 가격과 가장 낮은 가격이에요. 현재 주가가 이 범위의 어디쯤 있는지를 보면 상대적인 위치를 가늠할 수 있어요.",
    "RSI (상대강도지수)": "최근 일정 기간 동안 주가가 오른 폭과 내린 폭을 비교해 '과매수(너무 많이 사들여진 상태)'인지 '과매도(너무 많이 팔린 상태)'인지를 0~100 사이 숫자로 보여주는 지표예요. "
                      "일반적으로 70 이상이면 과매수, 30 이하면 과매도 구간으로 해석해요. (참고용이며 절대적인 매매 신호는 아니에요!)",
    "PER (주가수익비율)": "현재 주가가 그 회사의 '1주당 순이익'의 몇 배인지를 나타내는 지표예요. 숫자가 낮을수록 상대적으로 저평가, 높을수록 고평가되었다고 해석하는 경우가 많지만, 업종마다 평균 수준이 다르니 비교할 때 주의가 필요해요.",
    "시가총액": "현재 주가에 전체 발행 주식 수를 곱한 값으로, '이 회사 전체를 지금 가격으로 사려면 얼마가 필요한가'를 보여주는 지표예요. 회사의 규모를 비교할 때 자주 사용돼요.",
    "배당수익률(Dividend Yield)": "1년 동안 받는 배당금이 현재 주가의 몇 퍼센트인지를 나타내는 지표예요. 예를 들어 배당수익률이 3%라면, 주가 대비 매년 3%만큼을 배당금으로 돌려받는 셈이에요. 미국 주식은 배당을 중요하게 보는 투자자가 많아요.",
    "티커(Ticker)": "주식시장에서 각 종목을 구분하기 위해 붙이는 알파벳 코드예요. 예를 들어 애플은 'AAPL', 테슬라는 'TSLA'처럼 표기해요.",
    "S&P 500 / 나스닥 / 다우존스": "모두 미국을 대표하는 주가지수예요. S&P 500은 미국 대형기업 500개, 나스닥은 기술주 중심 종목들, 다우존스는 오래된 우량기업 30개로 구성돼 있어요. 특정 종목의 흐름을 전체 시장과 비교할 때 자주 기준으로 사용돼요.",
}

# ----------------------------------------
# 사이드바 - 종목 선택
# ----------------------------------------
st.sidebar.title("🇺🇸 미국 주식 선택")

select_mode = st.sidebar.radio("종목 선택 방식", ["목록에서 선택", "티커 직접 입력"])

if select_mode == "목록에서 선택":
    name = st.sidebar.selectbox("종목 선택", list(US_STOCKS.keys()))
    ticker = US_STOCKS[name]
    display_name = name
else:
    ticker = st.sidebar.text_input(
        "티커(Ticker) 직접 입력",
        value="AAPL",
        help="예) 'AAPL', 'TSLA', 'NVDA'처럼 알파벳 코드를 입력해 주세요."
    ).strip().upper()
    display_name = ticker

st.sidebar.markdown("---")
st.sidebar.subheader("📅 기간 선택")

period_option = st.sidebar.selectbox(
    "조회 기간",
    ["1개월", "3개월", "6개월", "1년", "3년", "5년", "전체", "직접 설정"]
)

period_map = {
    "1개월": 30, "3개월": 90, "6개월": 180,
    "1년": 365, "3년": 365 * 3, "5년": 365 * 5
}

end_date = datetime.today()
if period_option == "전체":
    start_date = None
elif period_option == "직접 설정":
    start_date = st.sidebar.date_input("시작일", value=end_date - timedelta(days=180))
    end_date = st.sidebar.date_input("종료일", value=end_date)
else:
    start_date = end_date - timedelta(days=period_map[period_option])

st.sidebar.markdown("---")
show_ma = st.sidebar.checkbox("이동평균선 표시", value=True)
ma_periods = []
if show_ma:
    ma_periods = st.sidebar.multiselect("이동평균 기간(일)", [5, 20, 60, 120, 200], default=[5, 20, 60])
show_rsi = st.sidebar.checkbox("RSI 보조지표 표시", value=False)

st.sidebar.markdown("---")
compare_index = st.sidebar.checkbox("주요 지수(ETF)와 비교", value=False)
if compare_index:
    index_choice = st.sidebar.selectbox("비교할 지수", list(INDEX_MAP.keys()))

# ----------------------------------------
# 데이터 불러오기
# ----------------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker_symbol, start, end, period_all=False):
    tk = yf.Ticker(ticker_symbol)
    if period_all:
        df = tk.history(period="max")
    else:
        df = tk.history(start=start, end=end)
    try:
        info = tk.info
    except Exception:
        info = {}
    return df, info


st.title("🇺🇸 미국 주식 데이터 분석 대시보드")
st.caption("yfinance + plotly 기반 인터랙티브 미국 주가 분석 도구")

if not ticker:
    st.warning("왼쪽 사이드바에서 종목을 선택하거나 티커를 입력해 주세요.")
    st.stop()

with st.spinner(f"{ticker} 데이터를 불러오는 중입니다..."):
    try:
        if period_option == "전체":
            df, info = load_data(ticker, None, None, period_all=True)
        else:
            df, info = load_data(ticker, start_date, end_date)
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        st.stop()

if df is None or df.empty:
    st.error("해당 티커의 데이터를 찾을 수 없습니다. 티커 표기가 올바른지 확인해 주세요. (예: AAPL, MSFT, TSLA)")
    st.stop()

df = df.reset_index()
if "Date" not in df.columns and "Datetime" in df.columns:
    df.rename(columns={"Datetime": "Date"}, inplace=True)

# ----------------------------------------
# 상단 요약 지표
# ----------------------------------------
company_name = info.get("longName") or info.get("shortName") or display_name
currency = info.get("currency", "USD")

last_close = df["Close"].iloc[-1]
prev_close = df["Close"].iloc[-2] if len(df) > 1 else last_close
change = last_close - prev_close
change_pct = (change / prev_close * 100) if prev_close != 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("현재가(최근 종가)", f"${last_close:,.2f}", f"{change:,.2f} ({change_pct:+.2f}%)")
col2.metric("거래량", f"{int(df['Volume'].iloc[-1]):,}")
col3.metric("52주 최고", f"${info.get('fiftyTwoWeekHigh', df['High'].max()):,.2f}")
col4.metric("52주 최저", f"${info.get('fiftyTwoWeekLow', df['Low'].min()):,.2f}")
market_cap = info.get("marketCap")
col5.metric("시가총액", f"${market_cap:,.0f}" if market_cap else "정보 없음")

dividend_yield = info.get("dividendYield")
if dividend_yield:
    st.caption(f"💰 배당수익률: 약 {dividend_yield * 100:.2f}% (참고용, 실시간과 차이가 있을 수 있어요)")

st.subheader(f"{company_name} ({ticker})")

# ----------------------------------------
# RSI 계산 함수
# ----------------------------------------
def calc_rsi(series, window=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ----------------------------------------
# 차트 (캔들 + 거래량 + RSI)
# ----------------------------------------
n_rows = 3 if show_rsi else 2
row_heights = [0.6, 0.2, 0.2] if show_rsi else [0.7, 0.3]

fig = make_subplots(
    rows=n_rows, cols=1, shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=row_heights,
)

fig.add_trace(go.Candlestick(
    x=df["Date"], open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"], name="주가",
    increasing_line_color="#2ecc71", decreasing_line_color="#e74c3c",
), row=1, col=1)

colors = ["#3498db", "#f39c12", "#9b59b6", "#e74c3c", "#1abc9c"]
if show_ma:
    for i, p in enumerate(ma_periods):
        ma_series = df["Close"].rolling(window=p).mean()
        fig.add_trace(go.Scatter(
            x=df["Date"], y=ma_series, mode="lines",
            name=f"{p}일 이동평균", line=dict(width=1.5, color=colors[i % len(colors)])
        ), row=1, col=1)

vol_colors = ["#2ecc71" if c >= o else "#e74c3c" for o, c in zip(df["Open"], df["Close"])]
fig.add_trace(go.Bar(
    x=df["Date"], y=df["Volume"], name="거래량", marker_color=vol_colors
), row=2, col=1)

if show_rsi:
    rsi = calc_rsi(df["Close"])
    fig.add_trace(go.Scatter(x=df["Date"], y=rsi, mode="lines", name="RSI", line=dict(color="#8e44ad")), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="blue", row=3, col=1)

fig.update_layout(
    height=750,
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=10, r=10, t=30, b=10),
)
fig.update_yaxes(title_text="가격 (USD)", row=1, col=1)
fig.update_yaxes(title_text="거래량", row=2, col=1)
if show_rsi:
    fig.update_yaxes(title_text="RSI", row=3, col=1)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------
# 지수 비교 (선택 시)
# ----------------------------------------
if compare_index:
    st.subheader(f"📊 {display_name} vs {index_choice} 수익률 비교")
    with st.spinner("지수 데이터를 불러오는 중입니다..."):
        try:
            idx_symbol = INDEX_MAP[index_choice]
            if period_option == "전체":
                idx_df, _ = load_data(idx_symbol, None, None, period_all=True)
            else:
                idx_df, _ = load_data(idx_symbol, start_date, end_date)
            idx_df = idx_df.reset_index()
            if "Date" not in idx_df.columns and "Datetime" in idx_df.columns:
                idx_df.rename(columns={"Datetime": "Date"}, inplace=True)

            stock_norm = df["Close"] / df["Close"].iloc[0] * 100
            idx_norm = idx_df["Close"] / idx_df["Close"].iloc[0] * 100

            cmp_fig = go.Figure()
            cmp_fig.add_trace(go.Scatter(x=df["Date"], y=stock_norm, mode="lines", name=display_name))
            cmp_fig.add_trace(go.Scatter(x=idx_df["Date"], y=idx_norm, mode="lines", name=index_choice))
            cmp_fig.update_layout(
                height=400,
                yaxis_title="상대 수익률 (시작일=100)",
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(cmp_fig, use_container_width=True)
            st.caption("두 선 모두 조회 시작일 값을 100으로 맞춰(정규화) 비교했어요. 선이 위에 있을수록 그 기간 동안 더 많이 올랐다는 뜻이에요.")
        except Exception as e:
            st.warning(f"지수 데이터를 불러오지 못했습니다: {e}")

# ----------------------------------------
# 데이터 테이블 + 다운로드
# ----------------------------------------
st.subheader("📋 원본 데이터")
show_cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
st.dataframe(df[show_cols].sort_values("Date", ascending=False), use_container_width=True, height=300)

csv = df[show_cols].to_csv(index=False).encode("utf-8-sig")
st.download_button("CSV로 다운로드", data=csv, file_name=f"{ticker}_data.csv", mime="text/csv")

# ----------------------------------------
# 주식 용어 설명
# ----------------------------------------
st.markdown("---")
st.subheader("📘 주식 용어 쉽게 알아보기")
st.caption("차트나 지표에 나오는 용어가 헷갈릴 때 펼쳐서 확인해 보세요.")

for term, explanation in TERM_EXPLANATIONS.items():
    with st.expander(term):
        st.write(explanation)

st.markdown("---")
st.caption("⚠️ 본 대시보드는 교육용 데이터 시각화 도구이며, 투자 판단이나 매매 추천을 위한 자료가 아닙니다. "
           "데이터 출처: Yahoo Finance(yfinance)")
