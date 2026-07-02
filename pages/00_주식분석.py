import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ----------------------------------------
# 기본 설정
# ----------------------------------------
st.set_page_config(page_title="주식 데이터 분석 대시보드", layout="wide")

# 자주 찾는 한국 주식 (yfinance는 코스피 종목에 .KS, 코스닥 종목에 .KQ를 붙여야 합니다)
KOREA_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "현대차": "005380.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "셀트리온": "068270.KS",
    "포스코홀딩스": "005490.KS",
    "카카오뱅크": "323410.KS",
    "에코프로": "086520.KQ",
    "에코프로비엠": "247540.KQ",
}

GLOBAL_STOCKS = {
    "애플 (Apple)": "AAPL",
    "마이크로소프트 (Microsoft)": "MSFT",
    "엔비디아 (NVIDIA)": "NVDA",
    "구글 (Alphabet)": "GOOGL",
    "아마존 (Amazon)": "AMZN",
    "테슬라 (Tesla)": "TSLA",
    "메타 (Meta)": "META",
    "넷플릭스 (Netflix)": "NFLX",
}

TERM_EXPLANATIONS = {
    "캔들차트(봉차트)": "하루(또는 특정 기간) 동안의 시가·고가·저가·종가를 하나의 막대(봉)로 표시한 차트예요. "
                    "봉이 빨간색(또는 채워짐)이면 시가보다 종가가 낮게 마감(하락), 파란색(또는 비어있음)이면 종가가 더 높게 마감(상승)한 걸 의미해요. "
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
}

# ----------------------------------------
# 사이드바 - 종목 선택
# ----------------------------------------
st.sidebar.title("📈 종목 선택")

market = st.sidebar.radio("시장 선택", ["한국 주식", "글로벌 주식", "직접 입력"])

ticker = None
display_name = None

if market == "한국 주식":
    name = st.sidebar.selectbox("종목 선택", list(KOREA_STOCKS.keys()))
    ticker = KOREA_STOCKS[name]
    display_name = name
elif market == "글로벌 주식":
    name = st.sidebar.selectbox("종목 선택", list(GLOBAL_STOCKS.keys()))
    ticker = GLOBAL_STOCKS[name]
    display_name = name
else:
    ticker = st.sidebar.text_input(
        "티커(Ticker) 직접 입력",
        value="AAPL",
        help="예) 미국 주식은 'AAPL', 'TSLA'처럼 입력하고, "
             "한국 주식은 종목코드 뒤에 코스피는 '.KS', 코스닥은 '.KQ'를 붙여주세요. (예: 005930.KS)"
    )
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
    info = {}
    try:
        info = tk.info
    except Exception:
        info = {}
    return df, info


st.title("🌍 글로벌·한국 주식 데이터 분석 대시보드")
st.caption("yfinance + plotly 기반 인터랙티브 주가 분석 도구")

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
    st.error("해당 티커의 데이터를 찾을 수 없습니다. 티커 표기가 올바른지 확인해 주세요. "
             "(한국 주식은 종목코드 뒤에 .KS 또는 .KQ를 붙여야 합니다)")
    st.stop()

df = df.reset_index()
if "Date" not in df.columns and "Datetime" in df.columns:
    df.rename(columns={"Datetime": "Date"}, inplace=True)

# ----------------------------------------
# 상단 요약 지표
# ----------------------------------------
company_name = info.get("longName") or info.get("shortName") or display_name
currency = info.get("currency", "")

last_close = df["Close"].iloc[-1]
prev_close = df["Close"].iloc[-2] if len(df) > 1 else last_close
change = last_close - prev_close
change_pct = (change / prev_close * 100) if prev_close != 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("현재가(최근 종가)", f"{last_close:,.2f} {currency}", f"{change:,.2f} ({change_pct:+.2f}%)")
col2.metric("거래량", f"{int(df['Volume'].iloc[-1]):,}")
col3.metric("52주 최고", f"{info.get('fiftyTwoWeekHigh', df['High'].max()):,.2f}")
col4.metric("52주 최저", f"{info.get('fiftyTwoWeekLow', df['Low'].min()):,.2f}")
market_cap = info.get("marketCap")
col5.metric("시가총액", f"{market_cap:,.0f}" if market_cap else "정보 없음")

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
rows = 2 if show_rsi else 1
row_heights = [0.6, 0.2, 0.2] if show_rsi else [0.7, 0.3]
n_rows = 3 if show_rsi else 2

fig = make_subplots(
    rows=n_rows, cols=1, shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=row_heights,
    subplot_titles=None
)

fig.add_trace(go.Candlestick(
    x=df["Date"], open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"], name="주가"
), row=1, col=1)

colors = ["#e74c3c", "#2ecc71", "#3498db", "#9b59b6", "#f39c12"]
if show_ma:
    for i, p in enumerate(ma_periods):
        ma_series = df["Close"].rolling(window=p).mean()
        fig.add_trace(go.Scatter(
            x=df["Date"], y=ma_series, mode="lines",
            name=f"{p}일 이동평균", line=dict(width=1.5, color=colors[i % len(colors)])
        ), row=1, col=1)

vol_colors = ["#e74c3c" if c >= o else "#3498db" for o, c in zip(df["Open"], df["Close"])]
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
fig.update_yaxes(title_text="가격", row=1, col=1)
fig.update_yaxes(title_text="거래량", row=2, col=1)
if show_rsi:
    fig.update_yaxes(title_text="RSI", row=3, col=1)

st.plotly_chart(fig, use_container_width=True)

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
