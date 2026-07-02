import streamlit as st
import random
import time

# ------------------------------------------------------
# 페이지 설정
# ------------------------------------------------------
st.set_page_config(
    page_title="MBTI 몬스터 도감 ✨",
    page_icon="🧬",
    layout="centered",
)

# ------------------------------------------------------
# MBTI별 데이터 (오리지널 '성격 몬스터' - 포켓몬 IP 아님)
# ------------------------------------------------------
MBTI_DATA = {
    "INTJ": {
        "name": "설계충 플랜서",
        "emoji": "🦉🔮",
        "color": "#4B4E6D",
        "desc": "밤에도 전략을 짜는 야행성 전략가 몬스터",
        "jobs": ["🏗️ 건축 설계사", "📊 데이터 사이언티스트", "♟️ 전략 컨설턴트"],
    },
    "INTP": {
        "name": "생각폭발 씽커몬",
        "emoji": "🧠⚡",
        "color": "#3E5C76",
        "desc": "궁금한 게 생기면 눈에서 불꽃이 튀는 이론가 몬스터",
        "jobs": ["🔬 연구원", "💻 소프트웨어 엔지니어", "📐 수학자"],
    },
    "ENTJ": {
        "name": "카리스마 리더로우",
        "emoji": "🦁👑",
        "color": "#8E2DE2",
        "desc": "무리를 이끄는 포효 한 방이 조직력 만점인 몬스터",
        "jobs": ["📈 경영 컨설턴트", "🚀 스타트업 대표", "⚖️ 변호사"],
    },
    "ENTP": {
        "name": "아이디어뱅크 스파클링",
        "emoji": "🦊💡",
        "color": "#FF6B35",
        "desc": "1초에 아이디어 3개씩 뿜어내는 즉흥 발명 몬스터",
        "jobs": ["🎬 광고 기획자", "🧑‍💼 창업가", "🗣️ 토론 전문 강사"],
    },
    "INFJ": {
        "name": "고요한 예언자 뮤스틱",
        "emoji": "🦢🌙",
        "color": "#5D5FEF",
        "desc": "조용히 세상을 관찰하며 깊은 통찰을 주는 신비 몬스터",
        "jobs": ["🖋️ 작가", "🧑‍⚕️ 상담심리사", "🎨 예술 감독"],
    },
    "INFP": {
        "name": "몽상 요정 드리무리",
        "emoji": "🦄🌸",
        "color": "#B983FF",
        "desc": "상상 속 세계를 현실로 데려오는 감성 몬스터",
        "jobs": ["✍️ 소설가", "🎨 일러스트레이터", "🎼 작곡가"],
    },
    "ENFJ": {
        "name": "따뜻한 등불 글로우리",
        "emoji": "🦌🕯️",
        "color": "#F76E11",
        "desc": "주변을 환하게 비추며 사람을 이끄는 힐링 몬스터",
        "jobs": ["🧑‍🏫 교사", "🤝 인사(HR) 매니저", "🎤 커뮤니티 리더"],
    },
    "ENFP": {
        "name": "반짝반짝 파티몬 스파키",
        "emoji": "🦋🎉",
        "color": "#FF4E9A",
        "desc": "가는 곳마다 축제로 만드는 에너지 폭발 몬스터",
        "jobs": ["🎥 방송 PD", "📣 마케터", "🎭 배우"],
    },
    "ISTJ": {
        "name": "철벽수호 가디언록",
        "emoji": "🐢🛡️",
        "color": "#6B705C",
        "desc": "약속과 규칙을 목숨처럼 지키는 견고한 몬스터",
        "jobs": ["🧑‍💼 회계사", "🏛️ 공무원", "🔧 품질관리 엔지니어"],
    },
    "ISFJ": {
        "name": "포근포근 케어퍼프",
        "emoji": "🐑🧺",
        "color": "#A7C957",
        "desc": "말없이 챙겨주는 다정한 살림꾼 몬스터",
        "jobs": ["🏥 간호사", "📚 사서", "🧑‍🍼 보육교사"],
    },
    "ESTJ": {
        "name": "돌격대장 커맨더울프",
        "emoji": "🐺📋",
        "color": "#264653",
        "desc": "체계적으로 무리를 통솔하는 현장 지휘관 몬스터",
        "jobs": ["🏢 프로젝트 매니저", "👮 경찰/군인", "🏭 운영관리자"],
    },
    "ESFJ": {
        "name": "인싸대장 프렌들리",
        "emoji": "🐶🎈",
        "color": "#FFB4A2",
        "desc": "모두와 친해지는 사교왕 몬스터",
        "jobs": ["🎉 이벤트 플래너", "🧑‍💼 영업 매니저", "🏨 호텔리어"],
    },
    "ISTP": {
        "name": "만능손재주 툴리",
        "emoji": "🦎🔧",
        "color": "#577590",
        "desc": "뭐든 뚝딱 고쳐내는 손기술의 달인 몬스터",
        "jobs": ["🛠️ 엔지니어", "✈️ 파일럿", "🏍️ 정비기술자"],
    },
    "ISFP": {
        "name": "감성아티스트 페인트테일",
        "emoji": "🦊🎨",
        "color": "#F4A261",
        "desc": "붓끝에서 무지개가 나오는 조용한 예술가 몬스터",
        "jobs": ["📷 사진작가", "💇 헤어/메이크업 아티스트", "🌿 플로리스트"],
    },
    "ESTP": {
        "name": "액션스타 다이나불",
        "emoji": "🐆🔥",
        "color": "#E63946",
        "desc": "일단 몸부터 움직이는 스릴 만점 행동파 몬스터",
        "jobs": ["🚒 응급구조사", "💰 트레이더", "🏄 스포츠 강사"],
    },
    "ESFP": {
        "name": "무대체질 샤이닝팝",
        "emoji": "🦩🎤",
        "color": "#FF006E",
        "desc": "스포트라이트를 받으면 더 빛나는 흥부자 몬스터",
        "jobs": ["🎤 가수/엔터테이너", "📺 인플루언서", "🎪 이벤트 MC"],
    },
}

# ------------------------------------------------------
# 커스텀 CSS
# ------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 50%, #1e1e2f 100%);
    }
    .big-emoji {
        font-size: 90px;
        text-align: center;
        animation: bounce 1.6s infinite;
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
    }
    .monster-card {
        border-radius: 24px;
        padding: 30px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .monster-name {
        font-size: 30px;
        font-weight: 800;
        color: white;
        margin-top: 10px;
    }
    .monster-desc {
        font-size: 15px;
        color: #eeeeee;
        margin-top: 6px;
        font-style: italic;
    }
    .job-chip {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.4);
        border-radius: 999px;
        padding: 10px 18px;
        margin: 6px;
        font-size: 16px;
        color: white;
        font-weight: 600;
        backdrop-filter: blur(4px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------
# 헤더
# ------------------------------------------------------
st.markdown(
    "<h1 style='text-align:center; color:white;'>🧬✨ MBTI 몬스터 도감 ✨🧬</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:#cccccc;'>당신의 MBTI를 소환하면, 성격 몬스터와 찰떡궁합 직업 3가지가 짠! 🪄</p>",
    unsafe_allow_html=True,
)
st.write("")

# ------------------------------------------------------
# MBTI 선택
# ------------------------------------------------------
mbti = st.selectbox(
    "🔍 당신의 MBTI를 선택하세요",
    options=["선택 안 함"] + list(MBTI_DATA.keys()),
)

if mbti != "선택 안 함":
    data = MBTI_DATA[mbti]

    with st.spinner("🔮 몬스터를 소환하는 중..."):
        time.sleep(0.8)

    # 소환 이펙트
    effect = random.choice(["balloons", "snow"])
    if effect == "balloons":
        st.balloons()
    else:
        st.snow()

    st.markdown(
        f"""
        <div class="monster-card" style="background: linear-gradient(160deg, {data['color']}dd, {data['color']}55);">
            <div class="big-emoji">{data['emoji']}</div>
            <div class="monster-name">{mbti} · {data['name']}</div>
            <div class="monster-desc">"{data['desc']}"</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<h3 style='text-align:center; color:white;'>💼 찰떡궁합 추천 직업 TOP 3</h3>",
        unsafe_allow_html=True,
    )

    chips_html = "".join(
        f"<span class='job-chip'>{job}</span>" for job in data["jobs"]
    )
    st.markdown(f"<div style='text-align:center;'>{chips_html}</div>", unsafe_allow_html=True)

    st.write("")
    st.info("🎯 Tip: 같은 MBTI라도 개인차가 크니, 참고용 재미로 봐주세요! 😉")
else:
    st.markdown(
        "<div style='text-align:center; font-size:60px; margin-top:40px;'>🥚❓</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#999999;'>아직 알을 깨지 않은 상태예요. MBTI를 선택해 몬스터를 소환해보세요!</p>",
        unsafe_allow_html=True,
    )

st.markdown("---")
st.caption("Made with 🧪 Streamlit · 이미지는 포켓몬 공식 이미지가 아닌 오리지널 이모지 몬스터입니다.")
