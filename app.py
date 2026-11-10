import streamlit as st
import sqlite3
import datetime
import os
import random

st.set_page_config(
    page_title="하루담 (HARUDAM)",
    page_icon="🏡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DB_FILE = "harudam.db"

def get_db():
    # SQLite Lock 방지를 위한 timeout 20초 설정
    conn = sqlite3.connect(DB_FILE, timeout=20.0)
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
    
    # family 테이블 컬럼 검사 및 자동 마이그레이션 (DB 오류 완벽 방지)
    c.execute("PRAGMA table_info(family)")
    fam_cols = [col[1] for col in c.fetchall()]
    if "growth_points" not in fam_cols:
        try: c.execute("ALTER TABLE family ADD COLUMN growth_points INTEGER DEFAULT 0")
        except Exception: pass
    if "growth_stage" not in fam_cols:
        try: c.execute("ALTER TABLE family ADD COLUMN growth_stage INTEGER DEFAULT 1")
        except Exception: pass
    if "character_id" not in fam_cols:
        try: c.execute("ALTER TABLE family ADD COLUMN character_id INTEGER DEFAULT 1")
        except Exception: pass
    if "created_at" not in fam_cols:
        try: c.execute("ALTER TABLE family ADD COLUMN created_at DATE DEFAULT CURRENT_DATE")
        except Exception: pass

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
    
    c.execute("PRAGMA table_info(answers)")
    ans_cols = [col[1] for col in c.fetchall()]
    if "emotion" not in ans_cols:
        try: c.execute("ALTER TABLE answers ADD COLUMN emotion TEXT DEFAULT '😊'")
        except Exception: pass

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

EMOTION_OPTIONS = [
    "😊 행복해요",
    "🥰 사랑스러워요",
    "😌 편안해요",
    "🥹 감동이에요",
    "💪 힘내요",
    "🤣 신나요/웃겨요",
    "☕ 피곤해요/지쳐요",
    "🥺 위로가 필요해요",
    "😟 걱정돼요",
    "🤔 생각이 많아요",
    "😡 속상해요",
    "✨ 설레요"
]

def get_character_from_blood_types(blood_types):
    if not blood_types:
        return 1
    sorted_bt = sorted([bt.upper().strip() for bt in blood_types])
    combined_str = "".join(sorted_bt)
    hash_val = sum(ord(c) for c in combined_str)
    return (hash_val % 15) + 1

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

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Gamja+Flower&display=swap');
    html, body, [class*="css"] {
        font-family: 'Gowun Dodum', sans-serif;
        background-color: #FAF8F5;
        color: #4A3E3D;
    }
    .block-container {
        max-width: 480px !important;
        padding-top: 0.5rem !important;
        padding-bottom: 75px !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        margin: 0 auto !important;
    }
    .app-header {
        background: linear-gradient(135deg, #FFFDF9 0%, #F5EFE6 100%);
        padding: 10px 14px;
        border-radius: 16px;
        box-shadow: 0 2px 10px rgba(210, 190, 175, 0.12);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        border: 1px solid #EFE6DC;
    }
    .app-header-title {
        font-family: 'Gamja Flower', cursive;
        font-size: 22px;
        color: #7A6855;
        font-weight: bold;
        margin: 0;
    }
    .app-header-sub { font-size: 11px; color: #A08C78; }
    .hd-card {
        background-color: #FFFFFF;
        border-radius: 18px;
        padding: 12px 14px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(180, 160, 140, 0.06);
        border: 1px solid #F0E8DF;
    }
    .hd-card-title {
        font-family: 'Gamja Flower', cursive;
        font-size: 18px;
        color: #5C4C3E;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .char-box {
        background: linear-gradient(180deg, #FFFDF9 0%, #F4EFEB 100%);
        border-radius: 20px;
        padding: 12px 14px;
        text-align: center;
        border: 1.5px solid #EAE0D5;
        margin-bottom: 10px;
    }
    .char-avatar-3d {
        width: 75px;
        height: 75px;
        border-radius: 38px;
        margin: 0 auto 6px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        box-shadow: 0 4px 14px rgba(120, 100, 80, 0.12);
        border: 3px solid #FFFFFF;
        background: radial-gradient(circle at 30% 30%, #FFFFFF, #F5E8DD);
    }
    .progress-bar-bg {
        background-color: #EFE8DF;
        border-radius: 10px;
        height: 10px;
        width: 100%;
        overflow: hidden;
        margin: 6px 0 4px 0;
    }
    .progress-bar-fill {
        background: linear-gradient(90deg, #B5C99A 0%, #86A789 100%);
        height: 100%;
        border-radius: 10px;
    }
    div.element-container:has(div.nav-anchor) {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 99999;
        background: #FFFFFF;
        box-shadow: 0 -4px 15px rgba(150, 130, 110, 0.1);
        border-top: 1px solid #EFE6DC;
    }
    .stButton > button {
        border-radius: 14px !important;
        background: linear-gradient(135deg, #E6D7C3 0%, #D8C4B6 100%) !important;
        color: #4A3E3D !important;
        font-weight: bold !important;
        border: none !important;
        padding: 6px 10px !important;
        font-size: 13px !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Session State 지속성 보장
if "splash_done" not in st.session_state:
    st.session_state.splash_done = True
if "current_nav" not in st.session_state:
    st.session_state.current_nav = "홈"
if "family_id" not in st.session_state:
    st.session_state.family_id = None
if "member_id" not in st.session_state:
    st.session_state.member_id = None

def get_family_info(family_id):
    if not family_id: return None
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM family WHERE id = ?", (family_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_family_members(family_id):
    if not family_id: return []
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE family_id = ?", (family_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_growth_points(family_id, points):
    if not family_id: return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT growth_points, growth_stage FROM family WHERE id = ?", (family_id,))
    row = c.fetchone()
    if row:
        curr_pts = (row["growth_points"] or 0) + points
        curr_stage = row["growth_stage"] or 1
        new_stage = 4 if curr_pts >= 120 else (3 if curr_pts >= 70 else (2 if curr_pts >= 30 else 1))
        c.execute("UPDATE family SET growth_points = ?, growth_stage = ? WHERE id = ?", (curr_pts, new_stage, family_id))
        conn.commit()
    conn.close()

# 로그인 / 가족 생성 처리
if st.session_state.family_id is None or st.session_state.member_id is None:
    st.markdown("""
    <div style="text-align:center; padding: 15px 0;">
        <h2 style="font-family: 'Gamja Flower', cursive; color: #7A6855; font-size: 28px; margin:0;">🏡 하루담 로그인</h2>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 기존 가족 로그인", "✨ 새로운 가족 등록"])
    
    with tab1:
        with st.form("login_form"):
            inv_code = st.text_input("초대 코드 (예: HD4767)", key="join_inv_code")
            inv_pwd = st.text_input("비밀번호", type="password", key="join_inv_pwd")
            j_name = st.text_input("내 이름/별명", key="j_m_name")
            login_btn = st.form_submit_button("하루담 입장하기", use_container_width=True)
            
            if login_btn:
                if inv_code and inv_pwd and j_name:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("SELECT * FROM family WHERE UPPER(invite_code) = ? AND password = ?", (inv_code.strip().upper(), inv_pwd.strip()))
                    fam = c.fetchone()
                    if fam:
                        c.execute("SELECT * FROM members WHERE family_id = ? AND name = ?", (fam["id"], j_name.strip()))
                        mem = c.fetchone()
                        if mem:
                            st.session_state.family_id = fam["id"]
                            st.session_state.member_id = mem["id"]
                            conn.close()
                            st.success(f"{mem['name']}님, 반갑습니다!")
                            st.rerun()
                        else:
                            c.execute("SELECT COUNT(*) as cnt FROM members WHERE family_id = ?", (fam["id"],))
                            if c.fetchone()["cnt"] >= 4:
                                st.error("최대 4명까지만 참여 가능합니다.")
                            else:
                                c.execute("INSERT INTO members (family_id, name, role, title, birthdate, blood_type) VALUES (?, ?, ?, ?, CURRENT_DATE, 'A형')", (fam["id"], j_name.strip(), '자녀', j_name.strip()))
                                new_mem_id = c.lastrowid
                                conn.commit()
                                st.session_state.family_id = fam["id"]
                                st.session_state.member_id = new_mem_id
                                conn.close()
                                st.rerun()
                    else:
                        st.error("초대 코드 또는 비밀번호가 틀렸습니다.")
                        conn.close()
                else:
                    st.warning("정보를 모두 입력해주세요.")

    with tab2:
        with st.form("create_family_form"):
            fam_name = st.text_input("가족 공간 이름", key="new_fam_name")
            fam_pwd = st.text_input("비밀번호 설정", type="password", key="new_fam_pwd")
            m_name = st.text_input("내 이름/별명", key="c_m_name")
            m_role = st.selectbox("가족 역할", ["아빠", "엄마", "첫째 자녀", "둘째 자녀", "셋째 자녀", "기타"], key="c_m_role")
            m_title = st.text_input("호칭 (예: 딸래미)", value="딸래미", key="c_m_title")
            m_blood = st.selectbox("혈액형", ["A형", "B형", "O형", "AB형"], key="c_m_blood")
            create_btn = st.form_submit_button("가족 만들기", use_container_width=True)
            
            if create_btn:
                if fam_name and fam_pwd and m_name:
                    conn = get_db()
                    c = conn.cursor()
                    invite_code = f"HD{random.randint(1000, 9999)}"
                    char_id = get_character_from_blood_types([m_blood])
                    c.execute("INSERT INTO family (family_name, invite_code, password, character_id, growth_points, growth_stage) VALUES (?, ?, ?, ?, 0, 1)", (fam_name.strip(), invite_code, fam_pwd.strip(), char_id))
                    new_fam_id = c.lastrowid
                    c.execute("INSERT INTO members (family_id, name, role, title, birthdate, blood_type) VALUES (?, ?, ?, ?, CURRENT_DATE, ?)", (new_fam_id, m_name.strip(), m_role, m_title.strip(), m_blood))
                    new_mem_id = c.lastrowid
                    conn.commit()
                    conn.close()
                    st.session_state.family_id = new_fam_id
                    st.session_state.member_id = new_mem_id
                    st.rerun()
                else:
                    st.warning("필수 입력 항목을 확인해 주세요.")
    st.stop()

family = get_family_info(st.session_state.family_id)
members = get_family_members(st.session_state.family_id)

if not family or not members:
    st.session_state.family_id = None
    st.session_state.member_id = None
    st.rerun()

current_member = next((m for m in members if m["id"] == st.session_state.member_id), members[0])

all_blood_types = [m["blood_type"] for m in members]
calculated_char_id = get_character_from_blood_types(all_blood_types)
if calculated_char_id != family["character_id"]:
    conn = get_db()
    conn.execute("UPDATE family SET character_id = ? WHERE id = ?", (calculated_char_id, family["id"]))
    conn.commit()
    conn.close()
    family = get_family_info(st.session_state.family_id)

char_idx = min(max(0, (family["character_id"] or 1) - 1), len(CHARACTERS) - 1)
active_char = CHARACTERS[char_idx]

st.markdown(f"""
<div class="app-header">
    <div>
        <div class="app-header-title">🏡 {family['family_name']}</div>
        <div class="app-header-sub">반가워요, {current_member['title']}님!</div>
    </div>
    <div style="background: #EFE6DC; padding: 4px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; color: #6B5B4D;">
        🔑 {family['invite_code']}
    </div>
</div>
""", unsafe_allow_html=True)

curr_tab = st.session_state.current_nav

# --- 1. 홈 화면 ---
if curr_tab == "홈":
    try:
        created_date = datetime.datetime.strptime(family["created_at"], "%Y-%m-%d").date()
    except Exception:
        created_date = datetime.date.today()
    days_together = (datetime.date.today() - created_date).days + 1
    
    stage = family["growth_stage"] or 1
    points = family["growth_points"] or 0
    pct = min(int((points / 120) * 100), 100)
    
    stage_names = {1: "1단계 알 🥚", 2: "2단계 부화 🐣", 3: "3단계 아기 🧸", 4: "4단계 성장 ✨"}
    display_icon = "🥚" if stage == 1 else ("🐣" if stage == 2 else active_char["icon"])

    st.markdown(f"""
    <div class="char-box">
        <div style="font-family: 'Gamja Flower', cursive; font-size: 20px; color: #5C4C3E; margin-bottom: 4px;">
            {active_char['name']} <span style="font-size:11px; background:{active_char['accent']}; color:#FFF; padding:2px 6px; border-radius:8px;">{stage_names.get(stage, "1단계 알 🥚")}</span>
        </div>
        <div class="char-avatar-3d" style="background: {active_char['bg_color']};">{display_icon}</div>
        <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: {pct}%;"></div></div>
        <div style="font-size: 11px; color: #8A7A6C; display: flex; justify-content: space-between;">
            <span>포인트: <b>{points} PT</b></span>
            <span>달성률: {pct}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="hd-card"><div class="hd-card-title">🌱 가족 안부 신호</div>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    m_cols = st.columns(max(1, len(members)))
    for idx, mem in enumerate(members):
        c.execute("SELECT mood FROM mood_signals WHERE member_id = ? ORDER BY updated_at DESC LIMIT 1", (mem["id"],))
        ms = c.fetchone()
        mood_txt = ms["mood"] if ms else "등록전"
        with m_cols[idx]:
            st.markdown(f"""
            <div style="background: #FBF8F3; padding: 6px; border-radius: 10px; text-align: center; border: 1px solid #EFE8DF;">
                <div style="font-size: 11px; font-weight: bold; color: #7A6855;">{mem['title']}</div>
                <div style="font-size: 16px; margin: 2px 0;">{mood_txt.split()[0] if ms else '💬'}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    today_q = get_today_question()
    st.markdown(f"""
    <div class="hd-card" style="background: linear-gradient(135deg, #FFFDF7 0%, #F8F1E9 100%);">
        <div class="hd-card-title">❓ 오늘의 질문</div>
        <div style="font-size: 13px; font-weight: bold; color: #605043;">"{today_q}"</div>
    </div>
    """, unsafe_allow_html=True)
    conn.close()

# --- 2. 질문 화면 (안정적인 등록 및 감정 선택 저장) ---
elif curr_tab == "질문":
    st.markdown('<div class="hd-card"><div class="hd-card-title">❓ 오늘의 가족 질문</div>', unsafe_allow_html=True)
    today_q = get_today_question()
    st.markdown(f'<div style="color: #5C4C3E; font-size: 14px; font-weight: bold; margin-bottom: 8px;">"{today_q}"</div>', unsafe_allow_html=True)
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM answers WHERE family_id = ? AND member_id = ? AND question_date = CURRENT_DATE", (family["id"], current_member["id"]))
    my_ans = c.fetchone()
    
    with st.form("ans_form", clear_on_submit=False):
        ans_input = st.text_area("답변 쓰기", value=my_ans["answer_text"] if my_ans else "", height=70, placeholder="가족에게 남길 이야기를 자유롭게 작성해 보세요.")
        emotion_sel = st.selectbox("오늘의 나의 감정 선택", EMOTION_OPTIONS, index=0)
        submit_ans = st.form_submit_button("등록 (+10 PT)", use_container_width=True)
        
        if submit_ans:
            if ans_input and ans_input.strip():
                emo_icon = emotion_sel.split()[0]
                if my_ans:
                    c.execute("UPDATE answers SET answer_text = ?, emotion = ? WHERE id = ?", (ans_input.strip(), emo_icon, my_ans["id"]))
                else:
                    c.execute("INSERT INTO answers (family_id, member_id, question_date, question_text, answer_text, emotion) VALUES (?, ?, CURRENT_DATE, ?, ?, ?)", (family["id"], current_member["id"], today_q, ans_input.strip(), emo_icon))
                    add_growth_points(family["id"], 10)
                conn.commit()
                st.success("답변이 성공적으로 등록되었습니다! 🎉 (+10 PT)")
                st.rerun()
            else:
                st.warning("답변 내용을 입력해 주세요!")
            
    st.markdown("---")
    st.markdown("**우리 가족의 오늘 답변 현황**")
    c.execute("SELECT a.*, m.title, m.name FROM answers a JOIN members m ON a.member_id = m.id WHERE a.family_id = ? AND a.question_date = CURRENT_DATE", (family["id"],))
    all_ans = c.fetchall()
    if all_ans:
        for row in all_ans:
            st.markdown(f"""
            <div style="background: #FFFDF9; border: 1px solid #EFE6DC; padding: 8px 12px; border-radius: 12px; margin-bottom: 6px;">
                <div style="font-size: 12px; font-weight: bold; color: #7A6855;">{row['title']} ({row['name']}) {row['emotion']}</div>
                <div style="font-size: 13px; color: #4A3E3D; margin-top: 2px;">{row['answer_text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("아직 오늘 답변을 남긴 가족이 없습니다.")
    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 3. 달력 화면 ---
elif curr_tab == "달력":
    st.markdown('<div class="hd-card"><div class="hd-card-title">📅 가족 달력 & 일정</div>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    with st.form("cal_form"):
        ev_title = st.text_input("일정 제목")
        ev_date = st.date_input("날짜", value=datetime.date.today())
        ev_sub = st.form_submit_button("일정 추가 (+5 PT)", use_container_width=True)
        if ev_sub:
            if ev_title and ev_title.strip():
                c.execute("INSERT INTO calendar_events (family_id, member_id, title, event_date) VALUES (?, ?, ?, ?)", (family["id"], current_member["id"], ev_title.strip(), ev_date))
                add_growth_points(family["id"], 5)
                conn.commit()
                st.success("일정이 등록되었습니다!")
                st.rerun()
            else:
                st.warning("일정 제목을 입력해주세요.")
            
    c.execute("SELECT * FROM calendar_events WHERE family_id = ? ORDER BY event_date ASC LIMIT 5", (family["id"],))
    events = c.fetchall()
    if events:
        for ev in events:
            st.markdown(f"<div style='font-size:12px; color:#5C4C3E; margin-bottom:4px;'>📌 <b>{ev['event_date']}</b>: {ev['title']}</div>", unsafe_allow_html=True)
    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 4. 편지 화면 ---
elif curr_tab == "편지":
    st.markdown('<div class="hd-card"><div class="hd-card-title">💌 미래의 비밀 편지</div>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    with st.form("letter_form"):
        l_rec = st.text_input("받는 사람")
        l_title = st.text_input("제목")
        l_open_date = st.date_input("열람 날짜", value=datetime.date.today() + datetime.timedelta(days=7))
        l_content = st.text_area("내용", height=70)
        l_sub = st.form_submit_button("편지 봉인하기", use_container_width=True)
        if l_sub:
            if l_title and l_content and l_title.strip() and l_content.strip():
                c.execute("INSERT INTO future_letters (family_id, sender_id, recipient_name, title, content, open_date) VALUES (?, ?, ?, ?, ?, ?)", (family["id"], current_member["id"], l_rec.strip(), l_title.strip(), l_content.strip(), l_open_date))
                conn.commit()
                st.success("비밀 편지가 성공적으로 봉인되었습니다!")
                st.rerun()
            else:
                st.warning("제목과 내용을 모두 입력해 주세요.")
    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 더보기 & 설정 탭 ---
elif curr_tab == "더보기":
    st.markdown('<div class="hd-card"><div class="hd-card-title">⚙️ 설정 및 관리</div>', unsafe_allow_html=True)
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📖 도감", "👤 내 설정", "🏡 가족 관리"])
    conn = get_db()
    c = conn.cursor()
    
    with sub_tab1:
        st.markdown(f"**현재 대표 펫:** {active_char['name']} ({active_char['type']})")
        st.caption(active_char['desc'])
        
    with sub_tab2:
        st.markdown("**내 프로필 설정**")
        with st.form("edit_my_profile"):
            new_title = st.text_input("내 호칭 변경", value=current_member["title"])
            bt_options = ["A형", "B형", "O형", "AB형"]
            curr_bt_idx = bt_options.index(current_member["blood_type"]) if current_member["blood_type"] in bt_options else 0
            new_blood = st.selectbox("혈액형 변경", bt_options, index=curr_bt_idx)
            save_prof = st.form_submit_button("변경 사항 저장", use_container_width=True)
            if save_prof:
                c.execute("UPDATE members SET title = ?, blood_type = ? WHERE id = ?", (new_title.strip(), new_blood, current_member["id"]))
                c.execute("SELECT blood_type FROM members WHERE family_id = ?", (family["id"],))
                all_bloods = [r["blood_type"] for r in c.fetchall()]
                new_char_id = get_character_from_blood_types(all_bloods)
                c.execute("UPDATE family SET character_id = ? WHERE id = ?", (new_char_id, family["id"]))
                conn.commit()
                st.success("정보가 성공적으로 변경되었습니다!")
                st.rerun()
                
    with sub_tab3:
        st.markdown(f"**가족 공간명:** {family['family_name']}")
        st.markdown(f"**초대 코드:** `{family['invite_code']}`")
        st.markdown("**가족 구성원 목록**")
        for mem in members:
            st.markdown(f"- **{mem['title']}** ({mem['name']}) | {mem['blood_type']}")
            
        if st.button("🚪 로그아웃 (가족 공간 나가기)", use_container_width=True):
            st.session_state.family_id = None
            st.session_state.member_id = None
            st.rerun()
            
    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# 하단 고정 모바일 탭 메뉴
st.markdown('<div class="nav-anchor"></div>', unsafe_allow_html=True)
nav_cols = st.columns(5)
nav_items = [("홈", "🏠"), ("질문", "❓"), ("달력", "📅"), ("편지", "💌"), ("더보기", "⚙️")]
for idx, (item, icon) in enumerate(nav_items):
    with nav_cols[idx]:
        if st.button(f"{icon} {item}", key=f"nav_btn_{item}", use_container_width=True):
            st.session_state.current_nav = item
            st.rerun()
