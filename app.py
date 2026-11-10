import streamlit as st
import sqlite3
import datetime
import json
import base64
import os
import random

# Streamlit Page Config (모바일 중심 뷰)
st.set_page_config(
    page_title="하루담 (HARUDAM)",
    page_icon="🏡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# SQLite 데이터베이스 설정
DB_FILE = "harudam.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS family (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_name TEXT NOT NULL,
            invite_code TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            character_id INTEGER DEFAULT 1,
            growth_stage INTEGER DEFAULT 1,
            growth_points INTEGER DEFAULT 0,
            created_at DATE DEFAULT CURRENT_DATE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            title TEXT,
            birthdate DATE,
            blood_type TEXT NOT NULL,
            FOREIGN KEY (family_id) REFERENCES family (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            question_date DATE NOT NULL,
            question_text TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            emotion TEXT DEFAULT '😊',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (family_id) REFERENCES family (id),
            FOREIGN KEY (member_id) REFERENCES members (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS mood_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            note TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (family_id) REFERENCES family (id),
            FOREIGN KEY (member_id) REFERENCES members (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            member_id INTEGER,
            title TEXT NOT NULL,
            event_date DATE NOT NULL,
            event_type TEXT DEFAULT '일정',
            is_completed INTEGER DEFAULT 0,
            FOREIGN KEY (family_id) REFERENCES family (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS future_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            recipient_name TEXT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            open_date DATE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (family_id) REFERENCES family (id),
            FOREIGN KEY (sender_id) REFERENCES members (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bucketlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            is_completed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (family_id) REFERENCES family (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS family_memos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            writer_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (family_id) REFERENCES family (id),
            FOREIGN KEY (writer_id) REFERENCES members (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 15종 독창적 3D 스타일 캐릭터 데이터 정의
CHARACTERS = [
    {"id": 1, "name": "포근이 퐁퐁이", "type": "파스텔 토끼", "desc": "복슬복슬한 분홍빛 털과 둥근 볼을 가진 따뜻한 마음의 수호자입니다.", "icon": "🐰", "bg_color": "#FFE5EC", "accent": "#FFB3C6"},
    {"id": 2, "name": "구름곰 몽몽", "type": "크림 아기곰", "desc": "몽실몽실 구름 같은 감촉으로 따스한 안아주기를 좋아하는 베어.", "icon": "🐻", "bg_color": "#FFF3BF", "accent": "#FFD43B"},
    {"id": 3, "name": "별밤여우 루니", "type": "세이지 아기여우", "desc": "밤하늘 별빛을 담은 풍성한 꼬리로 온 가족의 꿈을 지켜줍니다.", "icon": "🦊", "bg_color": "#E6FCF5", "accent": "#63E6BE"},
    {"id": 4, "name": "달콩이 판다", "type": "모찌 판다", "desc": "말랑말랑한 찹쌀떡 느낌의 판다로 웃음과 행복을 가져다줍니다.", "icon": "🐼", "bg_color": "#E9ECEF", "accent": "#CED4DA"},
    {"id": 5, "name": "무지개 고양이 코코", "type": "파스텔 고양이", "desc": "살랑거리는 파스텔 꼬리로 언제나 다정한 인사를 건네는 야옹이.", "icon": "🐱", "bg_color": "#F3D9FA", "accent": "#DA77F2"},
    {"id": 6, "name": "솔바람 람쥐 찌구", "type": "버터 다람쥐", "desc": "도토리 케이크를 좋아하는 동글동글 볼의 숲속 마스코트.", "icon": "🐿️", "bg_color": "#FFF4E6", "accent": "#FFC078"},
    {"id": 7, "name": "물방울 오리 둥둥", "type": "민트 아기오리", "desc": "노란 작은 리본을 매고 촉촉한 맑은 연못에서 헤엄치는 오리.", "icon": "🐥", "bg_color": "#E7F5FF", "accent": "#74C0FC"},
    {"id": 8, "name": "하늘공룡 뽀요", "type": "파스텔 브라키오", "desc": "동글동글 매끄러운 3D 질감의 귀여운 꼬마 파스텔 공룡.", "icon": "🦕", "bg_color": "#D0EBFF", "accent": "#4DABF7"},
    {"id": 9, "name": "퐁당이 사슴 로이", "type": "베이지 꼬마사슴", "desc": "작고 귀여운 뿔과 맑은 눈망울로 따스함을 전하는 아기사슴.", "icon": "🦌", "bg_color": "#FDF2E9", "accent": "#F5C6CB"},
    {"id": 10, "name": "꿈결펭귄 핑구", "type": "솜사탕 펭귄", "desc": "폭신폭신한 목도리를 두르고 뚱뚱한 볼살을 자랑하는 펭귄.", "icon": "🐧", "bg_color": "#E3FAFC", "accent": "#66D9E8"},
    {"id": 11, "name": "달콤이 강아지 멍뽀", "type": "밀크 비숑", "desc": "동그란 솜사탕 모양의 머리를 가진 꼬리 치기 대장 비숑.", "icon": "🐶", "bg_color": "#FFF5F5", "accent": "#FFC9C9"},
    {"id": 12, "name": "자몽이 햄스터 모카", "type": "피치 햄스터", "desc": "볼 가득 해바라기 씨앗을 물고 오물거리는 귀요미 햄스터.", "icon": "🐹", "bg_color": "#FFE8CC", "accent": "#FFA8A8"},
    {"id": 13, "name": "은하수 아기유니콘 라라", "type": "은하수 드림", "desc": "반짝이는 파스텔 갈기와 작고 빛나는 뿔을 가진 신비로운 유니콘.", "icon": "🦄", "bg_color": "#F8F0FC", "accent": "#EEBEFA"},
    {"id": 14, "name": "초코 해달 모네", "type": "밀크 해달", "desc": "배 위에 하트 조개를 얹고 둥둥 떠다니는 느긋한 해달.", "icon": "🦦", "bg_color": "#EBFBEE", "accent": "#8CE99A"},
    {"id": 15, "name": "별빛 아기부엉이 오울", "type": "지혜 아기부엉", "desc": "동그란 안경 모자를 쓰고 밤마다 안락한 쉼터를 전해주는 부엉이.", "icon": "🦉", "bg_color": "#F1F3F5", "accent": "#ADB5BD"}
]

# 혈액형 조합 기반 결정 알고리즘 (순서 상관없이 동일 조합 = 동일 캐릭터)
def get_character_from_blood_types(blood_types):
    sorted_bt = sorted([bt.upper().strip() for bt in blood_types])
    combined_str = "".join(sorted_bt)
    hash_val = sum(ord(c) for c in combined_str)
    return (hash_val % 15) + 1

# 매일 자동 변경되는 오늘의 가족 질문 목록
DAILY_QUESTIONS = [
    "오늘 우리 가족에게 일어난 가장 행복했던 순간은?",
    "다음 주말에 가족과 함께 꼭 가보고 싶은 장소는?",
    "요즘 마음속으로 가장 고맙고 감사하게 느끼는 사람은?",
    "오늘 하루 지친 가족 구성원에게 건네고 싶은 따뜻한 한마디는?",
    "가족과 함께 먹었던 음식 중 다시 먹고 싶은 최고의 메뉴는?",
    "가족 구성원의 어릴 적 모습 중 가장 인상 깊은 기억은?",
    "요즘 내가 느끼는 소소하지만 확실한 행복(소확행)은?"
]

def get_today_question():
    return DAILY_QUESTIONS[datetime.date.today().toordinal() % len(DAILY_QUESTIONS)]

# 모바일 UI 전용 커스텀 CSS (크림/아이보리/세이지그린, 둥근 모서리, max-width: 500px, 하단 메뉴 고정)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Gamja+Flower&display=swap');
    html, body, [class*="css"] {
        font-family: 'Gowun Dodum', sans-serif;
        background-color: #FAF8F5;
        color: #4A3E3D;
    }
    .block-container {
        max-width: 500px !important;
        padding-top: 1rem !important;
        padding-bottom: 90px !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto !important;
    }
    .app-header {
        background: linear-gradient(135deg, #FFFDF9 0%, #F5EFE6 100%);
        padding: 14px 18px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(210, 190, 175, 0.15);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        border: 1px solid #EFE6DC;
    }
    .app-header-title {
        font-family: 'Gamja Flower', cursive;
        font-size: 26px;
        color: #7A6855;
        font-weight: bold;
        margin: 0;
    }
    .app-header-sub { font-size: 13px; color: #A08C78; }
    .hd-card {
        background-color: #FFFFFF;
        border-radius: 22px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 6px 18px rgba(180, 160, 140, 0.08);
        border: 1px solid #F0E8DF;
    }
    .hd-card-title {
        font-family: 'Gamja Flower', cursive;
        font-size: 20px;
        color: #5C4C3E;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .char-box {
        background: linear-gradient(180deg, #FFFDF9 0%, #F4EFEB 100%);
        border-radius: 24px;
        padding: 20px;
        text-align: center;
        border: 2px solid #EAE0D5;
        box-shadow: inset 0 2px 6px rgba(255,255,255,0.8), 0 8px 20px rgba(185, 165, 145, 0.12);
    }
    .char-avatar-3d {
        width: 120px;
        height: 120px;
        border-radius: 60px;
        margin: 0 auto 12px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 60px;
        box-shadow: 0 8px 24px rgba(120, 100, 80, 0.15);
        border: 4px solid #FFFFFF;
        background: radial-gradient(circle at 30% 30%, #FFFFFF, #F5E8DD);
    }
    .progress-bar-bg {
        background-color: #EFE8DF;
        border-radius: 12px;
        height: 14px;
        width: 100%;
        overflow: hidden;
        margin: 10px 0 6px 0;
    }
    .progress-bar-fill {
        background: linear-gradient(90deg, #B5C99A 0%, #86A789 100%);
        height: 100%;
        border-radius: 12px;
    }
    div.element-container:has(div.nav-anchor) {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 99999;
        background: #FFFFFF;
        box-shadow: 0 -4px 20px rgba(150, 130, 110, 0.12);
        border-top: 1px solid #EFE6DC;
    }
    .stButton > button {
        border-radius: 16px !important;
        background: linear-gradient(135deg, #E6D7C3 0%, #D8C4B6 100%) !important;
        color: #4A3E3D !important;
        font-weight: bold !important;
        border: none !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 10px rgba(180, 160, 140, 0.15) !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "splash_done" not in st.session_state:
    st.session_state.splash_done = False
if "current_nav" not in st.session_state:
    st.session_state.current_nav = "홈"
if "family_id" not in st.session_state:
    st.session_state.family_id = None
if "member_id" not in st.session_state:
    st.session_state.member_id = None

# 스플래시 화면 (최초 1회 실행)
if not st.session_state.splash_done:
    st.markdown("""
    <div style="text-align: center; padding: 100px 20px 40px 20px; background: linear-gradient(180deg, #FFFDF9 0%, #F5EFE6 100%); border-radius: 30px; border: 1px solid #EFE6DC;">
        <div style="font-size: 80px; margin-bottom: 20px;">🏡</div>
        <h1 style="font-family: 'Gamja Flower', cursive; font-size: 48px; color: #7A6855; margin-bottom: 10px;">하루담</h1>
        <p style="font-size: 18px; color: #A08C78; font-weight: 500;">가족의 하루를 담다</p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("🌱 하루담 시작하기", use_container_width=True):
        st.session_state.splash_done = True
        st.rerun()
    st.stop()

def get_family_info(family_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM family WHERE id = ?", (family_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_family_members(family_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE family_id = ?", (family_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_growth_points(family_id, points):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT growth_points, growth_stage FROM family WHERE id = ?", (family_id,))
    row = c.fetchone()
    if row:
        curr_pts = row["growth_points"] + points
        curr_stage = row["growth_stage"]
        new_stage = curr_stage
        if curr_pts >= 120:
            new_stage = 4
        elif curr_pts >= 70:
            new_stage = 3
        elif curr_pts >= 30:
            new_stage = 2
        else:
            new_stage = 1
        c.execute("UPDATE family SET growth_points = ?, growth_stage = ? WHERE id = ?", (curr_pts, new_stage, family_id))
        conn.commit()
    conn.close()

# 가족 생성 및 로그인 시스템 (초대코드 및 비밀번호 사용)
if st.session_state.family_id is None:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0;">
        <h2 style="font-family: 'Gamja Flower', cursive; color: #7A6855; font-size: 32px;">🏡 하루담 가족 공간</h2>
        <p style="color: #8C7A6B; font-size: 14px;">우리 가족만의 따뜻한 소통 공간으로 들어오세요</p>
    </div>
    """, unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["✨ 새로운 가족 만들기", "🔑 기존 가족 참여하기"])
    with tab1:
        st.subheader("새로운 가족 등록")
        fam_name = st.text_input("가족 이름 (예: 행복한 우리집)", key="new_fam_name")
        fam_pwd = st.text_input("가족 비밀번호", type="password", key="new_fam_pwd")
        st.markdown("---")
        st.markdown("**첫 번째 가족 구성원(나) 정보**")
        m_name = st.text_input("내 이름 / 별명", key="c_m_name")
        m_role = st.selectbox("가족 내 역할", ["아빠", "엄마", "첫째 자녀", "둘째 자녀", "셋째 자녀", "조부모", "기타"], key="c_m_role")
        m_title = st.text_input("호칭 (예: 아빠, 딸래미, 아들)", key="c_m_title")
        m_birth = st.date_input("생년월일", value=datetime.date(2010, 1, 1), key="c_m_birth")
        m_blood = st.selectbox("혈액형", ["A형", "B형", "O형", "AB형"], key="c_m_blood")
        if st.button("가족 공간 만들기", use_container_width=True):
            if fam_name and fam_pwd and m_name:
                conn = get_db()
                c = conn.cursor()
                invite_code = f"HD{random.randint(1000, 9999)}"
                char_id = get_character_from_blood_types([m_blood])
                c.execute("INSERT INTO family (family_name, invite_code, password, character_id) VALUES (?, ?, ?, ?)", (fam_name, invite_code, fam_pwd, char_id))
                new_fam_id = c.lastrowid
                c.execute("INSERT INTO members (family_id, name, role, title, birthdate, blood_type) VALUES (?, ?, ?, ?, ?, ?)", (new_fam_id, m_name, m_role, m_title, m_birth, m_blood))
                new_mem_id = c.lastrowid
                conn.commit()
                conn.close()
                st.session_state.family_id = new_fam_id
                st.session_state.member_id = new_mem_id
                st.success(f"가족 공간이 생성되었습니다! 초대코드: {invite_code}")
                st.rerun()
            else:
                st.warning("모든 필드를 입력해 주세요.")
    with tab2:
        st.subheader("초대 코드로 참여")
        inv_code = st.text_input("초대 코드 (예: HD1234)", key="join_inv_code")
        inv_pwd = st.text_input("가족 비밀번호", type="password", key="join_inv_pwd")
        st.markdown("---")
        st.markdown("**내 정보 등록**")
        j_name = st.text_input("내 이름 / 별명", key="j_m_name")
        j_role = st.selectbox("가족 내 역할", ["아빠", "엄마", "첫째 자녀", "둘째 자녀", "셋째 자녀", "조부모", "기타"], key="j_m_role")
        j_title = st.text_input("호칭 (예: 엄마, 둘째)", key="j_m_title")
        j_birth = st.date_input("생년월일", value=datetime.date(2010, 3, 18), key="j_m_birth")
        j_blood = st.selectbox("혈액형", ["A형", "B형", "O형", "AB형"], key="j_m_blood")
        if st.button("가족 합류하기", use_container_width=True):
            if inv_code and inv_pwd and j_name:
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT * FROM family WHERE invite_code = ? AND password = ?", (inv_code.strip(), inv_pwd.strip()))
                fam = c.fetchone()
                if fam:
                    c.execute("SELECT COUNT(*) as cnt FROM members WHERE family_id = ?", (fam["id"],))
                    if c.fetchone()["cnt"] >= 4:
                        st.error("가족 공간은 최대 4명까지만 참여 가능합니다.")
                        conn.close()
                    else:
                        c.execute("INSERT INTO members (family_id, name, role, title, birthdate, blood_type) VALUES (?, ?, ?, ?, ?, ?)", (fam["id"], j_name, j_role, j_title, j_birth, j_blood))
                        new_mem_id = c.lastrowid
                        c.execute("SELECT blood_type FROM members WHERE family_id = ?", (fam["id"],))
                        all_bloods = [r["blood_type"] for r in c.fetchall()]
                        new_char_id = get_character_from_blood_types(all_bloods)
                        c.execute("UPDATE family SET character_id = ? WHERE id = ?", (new_char_id, fam["id"]))
                        conn.commit()
                        conn.close()
                        st.session_state.family_id = fam["id"]
                        st.session_state.member_id = new_mem_id
                        st.success("가족 공간에 참가되었습니다!")
                        st.rerun()
                else:
                    st.error("초대 코드 또는 비밀번호가 올바르지 않습니다.")
                    conn.close()
            else:
                st.warning("정보를 올바르게 입력해 주세요.")
    st.stop()

family = get_family_info(st.session_state.family_id)
members = get_family_members(st.session_state.family_id)
current_member = next((m for m in members if m["id"] == st.session_state.member_id), None)

# 혈액형 조합에 맞추어 가족 캐릭터 실시간 갱신
all_blood_types = [m["blood_type"] for m in members]
calculated_char_id = get_character_from_blood_types(all_blood_types)
if calculated_char_id != family["character_id"]:
    conn = get_db()
    conn.execute("UPDATE family SET character_id = ? WHERE id = ?", (calculated_char_id, family["id"]))
    conn.commit()
    conn.close()
    family = get_family_info(st.session_state.family_id)

active_char = CHARACTERS[family["character_id"] - 1]

# 모바일 상단 바
st.markdown(f"""
<div class="app-header">
    <div>
        <div class="app-header-title">🏡 {family['family_name']}</div>
        <div class="app-header-sub">반가워요, {current_member['title'] if current_member else '가족'}님!</div>
    </div>
    <div style="background: #EFE6DC; padding: 6px 12px; border-radius: 14px; font-size: 12px; font-weight: bold; color: #6B5B4D;">
        🔑 {family['invite_code']}
    </div>
</div>
""", unsafe_allow_html=True)

curr_tab = st.session_state.current_nav

# --- 1. 홈 화면 ---
if curr_tab == "홈":
    created_date = datetime.datetime.strptime(family["created_at"], "%Y-%m-%d").date()
    days_together = (datetime.date.today() - created_date).days + 1
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 12px;">
        <span style="background: #F0E6D8; color: #7A6855; padding: 4px 14px; border-radius: 12px; font-size: 13px; font-weight: bold;">
            ❤️ 함께한 지 <b>{days_together}</b>일째 되는 날
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    stage = family["growth_stage"]
    points = family["growth_points"]
    pct = min(int((points / 120) * 100), 100)
    
    stage_names = {1: "1단계: 신비로운 알 🥚", 2: "2단계: 아기 부화 🐣", 3: "3단계: 아기 캐릭터 🧸", 4: "4단계: 최종 성장 ✨"}
    stage_desc = {
        1: "따뜻한 관심으로 알을 품어주세요! (0~29pt)",
        2: "알에 금이 가며 귀여운 모습이 보이기 시작해요! (30~69pt)",
        3: "장난기 가득한 아기 캐릭터로 자라났어요! (70~119pt)",
        4: f"축하합니다! 완성된 3D 펫 '{active_char['name']}'으로 대성장했어요! 🎉"
    }
    
    display_icon = "🥚"
    if stage == 2:
        display_icon = "🐣"
    elif stage in (3, 4):
        display_icon = active_char["icon"]

    st.markdown(f"""
    <div class="char-box">
        <div style="font-size: 13px; color: #9E8B7A; font-weight: bold; margin-bottom: 6px;">우리 가족 대표 캐릭터</div>
        <div style="font-family: 'Gamja Flower', cursive; font-size: 26px; color: #5C4C3E; margin-bottom: 8px;">
            {active_char['name']} <span style="font-size:14px; background:{active_char['accent']}; color:#FFF; padding:2px 8px; border-radius:10px;">{stage_names[stage].split(':')[0]}</span>
        </div>
        <div class="char-avatar-3d" style="background: {active_char['bg_color']};">{display_icon}</div>
        <div style="font-size: 13px; color: #7A6A5C; margin-bottom: 10px;">{stage_desc[stage]}</div>
        <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: {pct}%;"></div></div>
        <div style="font-size: 12px; color: #8A7A6C; display: flex; justify-content: space-between; margin-top: 4px;">
            <span>성장 포인트: <b>{points} PT</b></span>
            <span>달성률: {pct}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="hd-card"><div class="hd-card-title">🌱 오늘 우리 가족 안부 신호</div>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    m_cols = st.columns(len(members))
    for idx, mem in enumerate(members):
        c.execute("SELECT mood FROM mood_signals WHERE member_id = ? ORDER BY updated_at DESC LIMIT 1", (mem["id"],))
        ms = c.fetchone()
        mood_txt = ms["mood"] if ms else "기분 등록 전"
        with m_cols[idx]:
            st.markdown(f"""
            <div style="background: #FBF8F3; padding: 10px; border-radius: 14px; text-align: center; border: 1px solid #EFE8DF;">
                <div style="font-size: 12px; font-weight: bold; color: #7A6855;">{mem['title']}</div>
                <div style="font-size: 20px; margin: 4px 0;">{mood_txt.split()[0] if ms else '💬'}</div>
                <div style="font-size: 11px; color: #9E8B7A;">{mood_txt.split()[1] if ms and ' ' in mood_txt else mood_txt}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    today_q = get_today_question()
    st.markdown(f"""
    <div class="hd-card" style="background: linear-gradient(135deg, #FFFDF7 0%, #F8F1E9 100%);">
        <div class="hd-card-title">❓ 오늘의 가족 질문</div>
        <div style="font-size: 15px; font-weight: bold; color: #605043; margin-bottom: 8px;">"{today_q}"</div>
        <div style="font-size: 12px; color: #9E8B7A;">답변 작성 시 <b>성장 포인트 +10 PT</b> 획득!</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_b, col_m = st.columns(2)
    with col_b:
        st.markdown('<div class="hd-card" style="min-height: 120px;"><div class="hd-card-title">🪣 버킷리스트</div>', unsafe_allow_html=True)
        c.execute("SELECT title, is_completed FROM bucketlist WHERE family_id = ? ORDER BY id DESC LIMIT 2", (family["id"],))
        b_items = c.fetchall()
        if b_items:
            for bi in b_items:
                chk = "✅" if bi["is_completed"] else "📌"
                st.markdown(f"<div style='font-size: 12px; color: #5C4C3E; margin-bottom: 4px;'>{chk} {bi['title']}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size: 12px; color: #AAA;'>등록된 목록이 없어요</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_m:
        st.markdown('<div class="hd-card" style="min-height: 120px;"><div class="hd-card-title">📝 최근 메모</div>', unsafe_allow_html=True)
        c.execute("SELECT content FROM family_memos WHERE family_id = ? ORDER BY created_at DESC LIMIT 2", (family["id"],))
        m_items = c.fetchall()
        if m_items:
            for mi in m_items:
                st.markdown(f"<div style='font-size: 12px; color: #5C4C3E; margin-bottom: 4px;'>💬 {mi['content'][:15]}...</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size: 12px; color: #AAA;'>작성된 메모가 없어요</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    conn.close()

# --- 2. 질문 화면 ---
elif curr_tab == "질문":
    st.markdown('<div class="hd-card"><div class="hd-card-title">❓ 오늘의 가족 질문</div>', unsafe_allow_html=True)
    today_q = get_today_question()
    st.markdown(f"<h3 style='color: #5C4C3E; font-size: 18px; margin-bottom: 12px;'>{today_q}</h3>", unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM answers WHERE family_id = ? AND member_id = ? AND question_date = CURRENT_DATE", (family["id"], st.session_state.member_id))
    my_ans = c.fetchone()
    
    with st.form("ans_form"):
        ans_input = st.text_area("나의 답변 쓰기", value=my_ans["answer_text"] if my_ans else "", placeholder="가족들과 공유하고 싶은 답변을 따뜻하게 적어주세요.")
        emotion_sel = st.selectbox("답변 감정 표정", ["😊 행복해요", "🥰 고마워요", "😌 편안해요", "🥹 감동이에요", "💪 힘내요"], index=0)
        submit_ans = st.form_submit_button("답변 등록하기 (+10 PT)")
        if submit_ans and ans_input.strip():
            emo_icon = emotion_sel.split()[0]
            if my_ans:
                c.execute("UPDATE answers SET answer_text = ?, emotion = ? WHERE id = ?", (ans_input.strip(), emo_icon, my_ans["id"]))
                st.success("답변이 수정되었습니다!")
            else:
                c.execute("INSERT INTO answers (family_id, member_id, question_date, question_text, answer_text, emotion) VALUES (?, ?, CURRENT_DATE, ?, ?, ?)", (family["id"], st.session_state.member_id, today_q, ans_input.strip(), emo_icon))
                add_growth_points(family["id"], 10)
                st.success("답변이 등록되었으며 성장 포인트 +10 PT를 획득했습니다!")
            conn.commit()
            st.rerun()
            
    st.markdown("---")
    st.markdown("**우리 가족의 오늘 답변 현황**")
    c.execute("SELECT a.*, m.title, m.name FROM answers a JOIN members m ON a.member_id = m.id WHERE a.family_id = ? AND a.question_date = CURRENT_DATE", (family["id"],))
    all_ans = c.fetchall()
    if all_ans:
        for row in all_ans:
            st.markdown(f"""
            <div style="background: #FFFDF9; border: 1px solid #EFE6DC; padding: 12px 15px; border-radius: 16px; margin-bottom: 8px;">
                <div style="font-size: 13px; font-weight: bold; color: #7A6855;">{row['title']} ({row['name']}) {row['emotion']}</div>
                <div style="font-size: 14px; color: #4A3E3D; margin-top: 4px;">{row['answer_text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("아직 오늘 답변을 남긴 가족이 없습니다. 첫 번째 답변을 작성해보세요!")
    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 3. 달력 화면 ---
elif curr_tab == "달력":
    st.markdown('<div class="hd-card"><div class="hd-card-title">📅 가족 달력 & 일정</div>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    with st.expander("➕ 새 일정 / 기념일 등록", expanded=False):
        with st.form("cal_form"):
            ev_title = st.text_input("일정 제목")
            ev_date = st.date_input("날짜", value=datetime.date.today())
            ev_type = st.selectbox("분류", ["일정", "기념일", "가족여행", "생일"])
            ev_sub = st.form_submit_button("일정 추가하기 (+5 PT)")
            if ev_sub and ev_title.strip():
                c.execute("INSERT INTO calendar_events (family_id, member_id, title, event_date, event_type) VALUES (?, ?, ?, ?, ?)", (family["id"], st.session_state.member_id, ev_title.strip(), ev_date, ev_type))
                add_growth_points(family["id"], 5)
                conn.commit()
                st.success("일정이 추가되었습니다!")
                st.rerun()
                
    st.markdown("### 🗓️ 다가오는 가족 일정")
    c.execute("SELECT * FROM calendar_events WHERE family_id = ? ORDER BY event_date ASC", (family["id"],))
    events = c.fetchall()
    if events:
        for ev in events:
            st.markdown(f"""
            <div style="background: #FDFBF7; border-left: 4px solid #86A789; padding: 10px 14px; border-radius: 12px; margin-bottom: 8px; display: flex; justify-content: space-between;">
                <div>
                    <span style="font-size: 11px; background: #EFE6DC; padding: 2px 6px; border-radius: 6px; color: #6B5B4D;">{ev['event_type']}</span>
                    <strong style="margin-left: 6px; color: #4A3E3D;">{ev['title']}</strong>
                    <div style="font-size: 12px; color: #8A7A6C; margin-top: 2px;">📆 {ev['event_date']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("등록된 가족 일정이 없습니다. 특별한 날을 기록해보세요!")
    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 4. 편지 화면 ---
elif curr_tab == "편지":
    st.markdown('<div class="hd-card"><div class="hd-card-title">💌 미래의 비밀 편지</div>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    tab_l1, tab_l2 = st.tabs(["✍️ 편지 쓰기", "📬 편지함 보기"])
    with tab_l1:
        with st.form("letter_form"):
            l_rec = st.text_input("받는 사람 (예: 우리 딸, 아빠, 또는 온 가족)")
            l_title = st.text_input("편지 제목")
            l_open_date = st.date_input("열람 가능 날짜", value=datetime.date.today() + datetime.timedelta(days=7))
            l_content = st.text_area("편지 내용", placeholder="미래의 가족에게 전하고 싶은 따뜻한 마음을 적어보세요.")
            l_sub = st.form_submit_button("비밀 편지 봉인하기")
            if l_sub and l_title.strip() and l_content.strip():
                c.execute("INSERT INTO future_letters (family_id, sender_id, recipient_name, title, content, open_date) VALUES (?, ?, ?, ?, ?, ?)", (family["id"], st.session_state.member_id, l_rec.strip(), l_title.strip(), l_content.strip(), l_open_date))
                conn.commit()
                st.success(f"편지가 {l_open_date}까지 비밀 보관됩니다!")
                st.rerun()
    with tab_l2:
        c.execute("SELECT l.*, m.title as sender_title FROM future_letters l JOIN members m ON l.sender_id = m.id WHERE l.family_id = ? ORDER BY l.open_date ASC", (family["id"],))
        letters = c.fetchall()
        today_date = datetime.date.today()
        if letters:
            for let in letters:
                open_d = datetime.datetime.strptime(let["open_date"], "%Y-%m-%d").date()
                if today_date >= open_d:
                    st.markdown(f"""
                    <div style="background: #FFFDF7; border: 1px solid #D8C4B6; padding: 14px; border-radius: 16px; margin-bottom: 10px;">
                        <div style="font-size: 12px; color: #B5C99A; font-weight: bold;">🔓 열린 편지 ({let['open_date']})</div>
                        <div style="font-weight: bold; font-size: 16px; color: #5C4C3E;">{let['title']}</div>
                        <div style="font-size: 12px; color: #8A7A6C;">보낸이: {let['sender_title']} | 받는이: {let['recipient_name']}</div>
                        <hr style="margin: 8px 0; border: none; border-top: 1px solid #EFE6DC;">
                        <div style="font-size: 14px; color: #4A3E3D; white-space: pre-line;">{let['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #F8F5F0; border: 1px dashed #C5B0A1; padding: 14px; border-radius: 16px; margin-bottom: 10px; text-align: center;">
                        <div style="font-size: 24px;">🔒</div>
                        <div style="font-weight: bold; color: #7A6855;">{let['title']}</div>
                        <div style="font-size: 12px; color: #9E8B7A;">보낸이: {let['sender_title']} → {let['recipient_name']}</div>
                        <div style="font-size: 11px; color: #E68A8A; margin-top: 4px;">{let['open_date']}에 공개됩니다</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("보관된 비밀 편지가 없습니다.")
    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 더보기 화면 ---
elif curr_tab == "더보기":
    st.markdown('<div class="hd-card"><div class="hd-card-title">⭐ 더보기 & 15종 캐릭터 도감</div>', unsafe_allow_html=True)
    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["📖 캐릭터 도감", "💓 안부 신호", "🪣 버킷리스트", "📝 메모"])
    conn = get_db()
    c = conn.cursor()
    with sub_tab1:
        st.markdown("### 📖 15종 전설의 가족 펫 도감")
        st.caption("가족 구성원의 혈액형 조합에 따라 우리 가족만의 고유한 3D 수집형 캐릭터가 탄생합니다!")
        for ch in CHARACTERS:
            is_our_char = (ch["id"] == family["character_id"])
            border_css = "3px solid #86A789" if is_our_char else "1px solid #EFE6DC"
            badge = "<span style='background:#86A789; color:#FFF; font-size:11px; padding:2px 8px; border-radius:10px;'>우리 가족 대표 펫</span>" if is_our_char else ""
            st.markdown(f"""
            <div style="background: {ch['bg_color']}; border: {border_css}; padding: 12px 16px; border-radius: 18px; margin-bottom: 10px; display: flex; align-items: center; gap: 14px;">
                <div style="font-size: 40px; background: #FFF; border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center;">{ch['icon']}</div>
                <div style="flex: 1;">
                    <div style="font-weight: bold; font-size: 16px; color: #4A3E3D;">{ch['name']} {badge}</div>
                    <div style="font-size: 11px; color: #7A6855; font-weight: bold;">{ch['type']}</div>
                    <div style="font-size: 12px; color: #665647; margin-top: 2px;">{ch['desc']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    with sub_tab2:
        st.markdown("### 💓 나의 오늘 기분 알리기")
        with st.form("mood_form"):
            my_mood = st.selectbox("오늘 나의 기분 상태", ["😊 행복해요", "👍 괜찮아요", "☕ 조금 지쳐요", "🤗 위로가 필요해요", "🗣️ 이야기하고 싶어요"])
            mood_note = st.text_input("한 줄 메시지 (선택)")
            m_sub = st.form_submit_button("기분 업데이트 (+5 PT)")
            if m_sub:
                c.execute("INSERT INTO mood_signals (family_id, member_id, mood, note) VALUES (?, ?, ?, ?)", (family["id"], st.session_state.member_id, my_mood, mood_note))
                add_growth_points(family["id"], 5)
                conn.commit()
                st.success("오늘의 안부 신호가 공유되었습니다!")
                st.rerun()
    with sub_tab3:
        st.markdown("### 🪣 가족 공동 버킷리스트")
        with st.form("bucket_form"):
            b_title = st.text_input("목표 입력")
            b_sub = st.form_submit_button("버킷리스트 추가")
            if b_sub and b_title.strip():
                c.execute("INSERT INTO bucketlist (family_id, title) VALUES (?, ?)", (family["id"], b_title.strip()))
                conn.commit()
                st.rerun()
        c.execute("SELECT * FROM bucketlist WHERE family_id = ?", (family["id"],))
        b_list = c.fetchall()
        for b in b_list:
            col_t, col_b = st.columns([4, 1])
            with col_t:
                st.write(f"{'✅' if b['is_completed'] else '⭕'} {b['title']}")
            with col_b:
                if not b["is_completed"]:
                    if st.button("완료", key=f"b_{b['id']}"):
                        c.execute("UPDATE bucketlist SET is_completed = 1 WHERE id = ?", (b["id"],))
                        add_growth_points(family["id"], 20)
                        conn.commit()
                        st.rerun()
    with sub_tab4:
        st.markdown("### 📝 가족 메모장")
        with st.form("memo_form"):
            memo_txt = st.text_area("가족들에게 남길 메모")
            memo_sub = st.form_submit_button("메모 남기기 (+3 PT)")
            if memo_sub and memo_txt.strip():
                c.execute("INSERT INTO family_memos (family_id, writer_id, content) VALUES (?, ?, ?)", (family["id"], st.session_state.member_id, memo_txt.strip()))
                add_growth_points(family["id"], 3)
                conn.commit()
                st.success("메모가 등록되었습니다!")
                st.rerun()
        c.execute("SELECT fm.*, m.title FROM family_memos fm JOIN members m ON fm.writer_id = m.id WHERE fm.family_id = ? ORDER BY fm.created_at DESC", (family["id"],))
        memos = c.fetchall()
        for m in memos:
            st.markdown(f"""
            <div style="background: #FFFDF5; border-left: 3px solid #FFD43B; padding: 10px 14px; border-radius: 10px; margin-bottom: 8px;">
                <div style="font-size: 11px; color: #8A7A6C;"><b>{m['title']}</b> | {m['created_at']}</div>
                <div style="font-size: 13px; color: #4A3E3D; margin-top: 4px;">{m['content']}</div>
            </div>
            """, unsafe_allow_html=True)
    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# 하단 고정 5대 대표 메뉴바 (홈, 질문, 달력, 편지, 더보기)
st.markdown('<div class="nav-anchor"></div>', unsafe_allow_html=True)
nav_cols = st.columns(5)
nav_items = [("홈", "🏠"), ("질문", "❓"), ("달력", "📅"), ("편지", "💌"), ("더보기", "⭐")]
for idx, (item, icon) in enumerate(nav_items):
    with nav_cols[idx]:
        if st.button(f"{icon} {item}", key=f"nav_btn_{item}", use_container_width=True):
            st.session_state.current_nav = item
            st.rerun()
