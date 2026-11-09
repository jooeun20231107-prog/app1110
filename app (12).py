# -*- coding: utf-8 -*-
"""SUMONE · 우리들의 하루 | Streamlit edition
Run: streamlit run app.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

import streamlit as st

APP_TITLE = "SUMONE · 우리들의 하루"
DB_PATH = os.environ.get("SUMONE_DB_PATH", "sumone_family.db")
TODAY = date.today().isoformat()

st.set_page_config(page_title=APP_TITLE, page_icon="🌱", layout="centered", initial_sidebar_state="collapsed")

# ------------------------------ Styling ------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Nanum+Myeongjo:wght@400;700&display=swap');
:root { --ink:#493f36; --muted:#8b8075; --cream:#faf8f3; --card:#fffefa; --sage:#9baa8b; --sage2:#e9eee3; --peach:#f2d9c8; }
html, body, [class*="css"] { font-family:'Gowun Dodum',sans-serif; color:var(--ink); }
.stApp { background:var(--cream); }
.block-container { max-width:720px; padding-top:1.1rem; padding-bottom:6rem; }
h1,h2,h3 { color:var(--ink); letter-spacing:-.04em; }
h1 { font-family:'Nanum Myeongjo',serif; font-size:2rem!important; }
h2 { font-size:1.35rem!important; }
h3 { font-size:1.08rem!important; }
div[data-testid="stMetric"] { background:#fffefa; border:1px solid #eee8df; border-radius:18px; padding:12px; }
.stButton>button, .stFormSubmitButton>button { border-radius:14px; border:1px solid #d9dfd1; background:#e9eee3; color:#45523f; font-weight:700; min-height:2.65rem; }
.stButton>button:hover, .stFormSubmitButton>button:hover { background:#dce5d4; border-color:#b9c7ad; color:#35422f; }
.stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] { border-radius:12px; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:var(--card); border:1px solid #eee8df; border-radius:20px; padding:14px 16px; }
div[data-testid="stAlert"] { border-radius:14px; }
div[data-testid="stRadio"] > div { gap:.35rem; }
div[data-testid="stRadio"] label { background:#fffefa; border:1px solid #eee8df; border-radius:13px; padding:8px 12px; }
.small-muted { color:var(--muted); font-size:.86rem; }
.hero { background:linear-gradient(135deg,#eef1e8,#fff3e9); border:1px solid #e7e8dd; padding:22px; border-radius:24px; margin:8px 0 18px; }
.hero-title { font-family:'Nanum Myeongjo',serif; font-size:1.65rem; line-height:1.5; }
.pill { display:inline-block; padding:5px 10px; background:#edf1e8; color:#66745d; border-radius:99px; font-size:.8rem; margin:2px; }
.answer-card { background:#fffefa; border:1px solid #eee8df; border-radius:16px; padding:13px; margin:8px 0; }
div[data-testid="stTabs"] button { font-size:.9rem; }
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ------------------------------ Database ------------------------------
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS family(id TEXT PRIMARY KEY, name TEXT, pin TEXT, invite TEXT, established TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS members(id TEXT PRIMARY KEY, family_id TEXT, name TEXT, role TEXT, call_name TEXT, birthday TEXT, blood TEXT, color TEXT, qr_token TEXT);
        CREATE TABLE IF NOT EXISTS answers(id TEXT PRIMARY KEY, family_id TEXT, question_date TEXT, question TEXT, category TEXT, member_id TEXT, member_name TEXT, text TEXT, mood TEXT, created TEXT, UNIQUE(family_id,question_date,member_id));
        CREATE TABLE IF NOT EXISTS letters(id TEXT PRIMARY KEY, family_id TEXT, sender_id TEXT, sender_name TEXT, receiver_id TEXT, receiver_name TEXT, title TEXT, content TEXT, created TEXT, unlock_date TEXT, opened INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS bucket(id TEXT PRIMARY KEY, family_id TEXT, text TEXT, proposer TEXT, target_date TEXT, done INTEGER DEFAULT 0, created TEXT);
        CREATE TABLE IF NOT EXISTS memos(id TEXT PRIMARY KEY, family_id TEXT, author TEXT, text TEXT, color TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS signals(id TEXT PRIMARY KEY, family_id TEXT, member_id TEXT, status TEXT, emoji TEXT, note TEXT, updated TEXT, UNIQUE(family_id,member_id));
        CREATE TABLE IF NOT EXISTS bookmarks(family_id TEXT, question_date TEXT, PRIMARY KEY(family_id,question_date));
        """)

init_db()

def q(sql, params=(), one=False):
    with db() as c:
        cur = c.execute(sql, params)
        rows = cur.fetchall()
    return (dict(rows[0]) if rows else None) if one else [dict(x) for x in rows]

def run(sql, params=()):
    with db() as c:
        c.execute(sql, params)
        c.commit()

def uid():
    return uuid.uuid4().hex[:12]

def family_members(fid):
    return q("SELECT * FROM members WHERE family_id=? ORDER BY rowid", (fid,))

def family_data(fid):
    return q("SELECT * FROM family WHERE id=?", (fid,), one=True)

def dday(start):
    try:
        n = (date.today() - date.fromisoformat(start)).days + 1
        return max(n, 1)
    except Exception:
        return 1

# ------------------------------ Session ------------------------------
for key, default in {
    "family_id": None, "member_id": None, "page": "홈", "font_large": False,
    "show_setup": False, "notice": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def notify(msg):
    st.session_state.notice = msg

def show_notice():
    if st.session_state.notice:
        st.success(st.session_state.notice)
        st.session_state.notice = None

def current_member():
    if not st.session_state.family_id or not st.session_state.member_id:
        return None
    return q("SELECT * FROM members WHERE id=? AND family_id=?", (st.session_state.member_id, st.session_state.family_id), one=True)

def get_family():
    return family_data(st.session_state.family_id) if st.session_state.family_id else None

def header():
    fam, me = get_family(), current_member()
    with st.container():
        c1,c2 = st.columns([3,1])
        with c1:
            st.markdown(f"### 🌱 {fam['name'] if fam else 'SUMONE'}")
            st.caption("우리의 오늘이 모여, 오래도록 꺼내 볼 추억이 되도록")
        with c2:
            if me and st.button("멤버 변경", use_container_width=True):
                st.session_state.member_id = None
                st.rerun()
    if fam and me:
        members = family_members(fam["id"])
        options = {f"{m['name']} · {m['role']}":m["id"] for m in members}
        selected = st.selectbox("지금 사용 중인 가족", list(options), index=list(options.values()).index(me["id"]), label_visibility="collapsed")
        if options[selected] != me["id"]:
            st.session_state.member_id = options[selected]
            st.rerun()
    st.divider()

# ------------------------------ Onboarding / Login ------------------------------
def onboarding():
    st.markdown('<div class="hero"><div class="hero-title">가족의 하루를 모으는<br>작은 공간, <b>SUMONE</b></div><p>서로의 마음을 묻고, 함께한 순간을 기록해요.</p><span class="pill">오늘의 질문</span><span class="pill">가족 달력</span><span class="pill">비밀 편지</span></div>', unsafe_allow_html=True)
    setup, join = st.tabs(["우리 가족 시작하기", "초대 코드로 참여하기"])
    with setup:
        with st.form("create_family"):
            fname = st.text_input("가족 이름", placeholder="예: 우리 가족")
            pin = st.text_input("가족 비밀번호 4자리", type="password", max_chars=4)
            established = st.date_input("함께한 날", value=date.today())
            st.markdown("**첫 번째 가족 구성원**")
            mname = st.text_input("이름")
            role = st.selectbox("가족 내 역할", ["엄마","아빠","딸","아들","할머니","할아버지","나"])
            call = st.text_input("서로 부르는 호칭", value="")
            birthday = st.date_input("생일", value=date(2010,1,1), min_value=date(1900,1,1), max_value=date.today())
            blood = st.selectbox("혈액형", ["A","B","O","AB"])
            if st.form_submit_button("우리 가족 만들기", use_container_width=True):
                if not fname.strip() or not mname.strip() or len(pin) != 4 or not pin.isdigit():
                    st.error("가족 이름과 구성원 이름을 입력하고, 비밀번호는 숫자 4자리로 설정해 주세요.")
                else:
                    fid, invite, mid = uid(), "SUM-" + uuid.uuid4().hex[:6].upper(), uid()
                    run("INSERT INTO family VALUES(?,?,?,?,?,?)", (fid,fname.strip(),pin,invite,established.isoformat(),datetime.now().isoformat()))
                    run("INSERT INTO members VALUES(?,?,?,?,?,?,?,?,?)", (mid,fid,mname.strip(),role,call.strip() or role,birthday.isoformat(),blood,"#DDE8D5",uid()))
                    st.session_state.family_id, st.session_state.member_id = fid, mid
                    notify("가족 공간이 만들어졌어요. 다른 가족도 초대해 보세요!")
                    st.rerun()
    with join:
        with st.form("join_family"):
            invite = st.text_input("초대 코드", placeholder="SUM-XXXXXX").strip().upper()
            pin = st.text_input("가족 비밀번호", type="password", max_chars=4)
            mname = st.text_input("내 이름")
            role = st.selectbox("나의 역할", ["엄마","아빠","딸","아들","할머니","할아버지","나"], key="join_role")
            call = st.text_input("가족이 부를 호칭", key="join_call")
            birthday = st.date_input("생일", value=date(2010,1,1), min_value=date(1900,1,1), max_value=date.today(), key="join_bday")
            blood = st.selectbox("혈액형", ["A","B","O","AB"], key="join_blood")
            if st.form_submit_button("가족 공간 참여하기", use_container_width=True):
                fam = q("SELECT * FROM family WHERE invite=?", (invite,), one=True)
                if not fam or fam["pin"] != pin:
                    st.error("초대 코드 또는 가족 비밀번호를 확인해 주세요.")
                elif not mname.strip():
                    st.error("이름을 입력해 주세요.")
                else:
                    mid=uid()
                    run("INSERT INTO members VALUES(?,?,?,?,?,?,?,?,?)", (mid,fam["id"],mname.strip(),role,call.strip() or role,birthday.isoformat(),blood,"#DDE8D5",uid()))
                    st.session_state.family_id, st.session_state.member_id = fam["id"], mid
                    notify(f"{fam['name']}에 참여했어요!")
                    st.rerun()

def login_member():
    st.markdown("## 가족 구성원 선택")
    fam = get_family()
    if not fam:
        return
    members = family_members(fam["id"])
    if not members:
        st.error("등록된 구성원이 없습니다.")
        return
    for m in members:
        if st.button(f"👤  {m['name']}  ·  {m['role']}", key=f"login_{m['id']}", use_container_width=True):
            st.session_state.member_id=m["id"]
            st.rerun()
    if st.button("다른 가족 공간으로 이동 / 로그아웃"):
        st.session_state.family_id=None
        st.session_state.member_id=None
        st.rerun()

# ------------------------------ Shared content ------------------------------
QUESTION_BANK = [
    ("식사","오늘 가족과 둘러앉아 가장 맛있게 먹었던 음식이나, 생각났던 집밥은 무엇인가요?"),
    ("추억","어릴 적 가장 선명하게 기억나는 가족과의 하루는 언제인가요?"),
    ("일상","오늘 하루 중 작지만 기분 좋았던 순간을 하나 들려주세요."),
    ("마음","요즘 누군가에게 꼭 전하고 싶은 고마운 마음이 있나요?"),
    ("지혜","살면서 알게 된, 우리 가족에게 꼭 알려주고 싶은 삶의 지혜는 무엇인가요?"),
    ("사랑","가족에게 들었던 말 중 오래도록 기억에 남는 말은 무엇인가요?"),
    ("추억","우리 가족이 함께 꼭 다시 가보고 싶은 장소는 어디인가요?"),
    ("일상","최근 새롭게 관심이 생긴 것이나 요즘 빠져 있는 것은 무엇인가요?"),
    ("마음","오늘 나의 마음을 날씨로 표현한다면 어떤 날씨인가요?"),
    ("사랑","가족과 함께여서 다행이라고 느꼈던 순간은 언제인가요?"),
]

def today_question():
    idx = date.today().toordinal() % len(QUESTION_BANK)
    return QUESTION_BANK[idx]

def home_page():
    fam, me = get_family(), current_member()
    days=dday(fam["established"])
    st.markdown(f'<div class="hero"><div class="hero-title">오늘도, 우리답게<br>함께한 지 <b>{days:,}일</b></div><p>작은 대화가 모여 우리 가족만의 이야기가 됩니다.</p><span class="pill">🌿 사랑의 클로버</span><span class="pill">{len(family_members(fam["id"]))}명의 가족</span></div>', unsafe_allow_html=True)
    question, category = today_question()
    st.markdown("## 🌼 오늘의 질문")
    st.markdown(f'<div class="answer-card"><span class="pill">{category}</span><h3>{question}</h3><p class="small-muted">오늘의 질문에 답하고 가족의 이야기를 모아 보세요.</p></div>', unsafe_allow_html=True)
    my_answer=q("SELECT * FROM answers WHERE family_id=? AND question_date=? AND member_id=?", (fam["id"],TODAY,me["id"]), one=True)
    if my_answer:
        st.success("오늘의 이야기를 남겼어요. 다른 가족의 답변도 확인해 보세요.")
        st.markdown(f'<div class="answer-card">{my_answer["text"]}<p class="small-muted">{my_answer["mood"]} · {my_answer["created"][:16]}</p></div>', unsafe_allow_html=True)
    else:
        with st.form("home_answer"):
            answer=st.text_area("나의 답변", placeholder="오늘의 이야기를 편하게 적어 주세요.", height=110)
            mood=st.selectbox("오늘의 기분", ["😊 좋아요","😌 평온해요","🥰 행복해요","😴 피곤해요","🤔 생각이 많아요","🌧 조금 우울해요"])
            if st.form_submit_button("답변 남기기", use_container_width=True):
                if answer.strip():
                    run("INSERT OR REPLACE INTO answers VALUES(?,?,?,?,?,?,?,?,?,?)", (uid(),fam["id"],TODAY,question,category,me["id"],me["name"],answer.strip(),mood,datetime.now().isoformat()))
                    notify("오늘의 답변을 저장했어요.")
                    st.rerun()
                else: st.warning("답변을 한 줄이라도 적어 주세요.")
    st.markdown("### 💌 오늘 우리 가족의 이야기")
    answers=q("SELECT * FROM answers WHERE family_id=? AND question_date=? ORDER BY created", (fam["id"],TODAY))
    if answers:
        for a in answers:
            st.markdown(f'<div class="answer-card"><b>{a["member_name"]}</b> <span class="small-muted">· {a["mood"]}</span><p>{a["text"]}</p></div>', unsafe_allow_html=True)
    else: st.info("아직 답변이 없어요. 첫 번째 이야기를 남겨 보세요.")
    st.markdown("### 🌱 우리 가족 마음 날씨")
    with st.form("mind_signal"):
        status=st.selectbox("지금 나의 마음", ["아주 좋아요","괜찮아요","조금 지쳐요","위로가 필요해요","이야기하고 싶어요"])
        note=st.text_input("가족에게 전하고 싶은 한마디 (선택)")
        if st.form_submit_button("마음 날씨 공유하기"):
            run("INSERT OR REPLACE INTO signals VALUES(?,?,?,?,?,?,?)", (uid(),fam["id"],me["id"],status,{"아주 좋아요":"☀️","괜찮아요":"🌤️","조금 지쳐요":"☁️","위로가 필요해요":"🌧️","이야기하고 싶어요":"💬"}[status],note,datetime.now().isoformat()))
            notify("마음 날씨를 공유했어요.")
            st.rerun()
    signals=q("SELECT s.*,m.name FROM signals s JOIN members m ON s.member_id=m.id WHERE s.family_id=? ORDER BY s.updated DESC", (fam["id"],))
    for s in signals:
        st.markdown(f'<div class="answer-card">{s["emoji"]} **{s["name"]}** · {s["status"]}<br><span class="small-muted">{s["note"]}</span></div>', unsafe_allow_html=True)

def question_page():
    fam, me=get_family(),current_member()
    st.title("오늘의 질문")
    st.caption("하루에 하나, 서로의 마음을 알아가는 질문")
    question,cat=today_question()
    st.markdown(f'<div class="hero"><span class="pill">{cat}</span><h2>{question}</h2></div>', unsafe_allow_html=True)
    if q("SELECT * FROM bookmarks WHERE family_id=? AND question_date=?", (fam["id"],TODAY), one=True):
        if st.button("⭐ 북마크 해제"):
            run("DELETE FROM bookmarks WHERE family_id=? AND question_date=?", (fam["id"],TODAY)); st.rerun()
    else:
        if st.button("☆ 오늘의 질문 북마크"):
            run("INSERT OR IGNORE INTO bookmarks VALUES(?,?)",(fam["id"],TODAY)); st.rerun()
    prev=q("SELECT * FROM answers WHERE family_id=? AND question_date=? AND member_id=?", (fam["id"],TODAY,me["id"]), one=True)
    with st.form("question_answer"):
        text=st.text_area("나의 이야기", value=prev["text"] if prev else "", height=150)
        mood=st.selectbox("기분", ["😊 좋아요","😌 평온해요","🥰 행복해요","😴 피곤해요","🤔 생각이 많아요","🌧 조금 우울해요"], index=0)
        if st.form_submit_button("저장하기", use_container_width=True):
            if text.strip():
                run("INSERT OR REPLACE INTO answers VALUES(?,?,?,?,?,?,?,?,?,?)",(uid(),fam["id"],TODAY,question,cat,me["id"],me["name"],text.strip(),mood,datetime.now().isoformat()))
                notify("답변을 저장했어요."); st.rerun()
            else: st.error("내용을 입력해 주세요.")
    st.markdown("## 가족들의 답변")
    answers=q("SELECT * FROM answers WHERE family_id=? AND question_date=? ORDER BY created",(fam["id"],TODAY))
    for a in answers:
        st.markdown(f'<div class="answer-card"><b>{a["member_name"]}</b> · {a["mood"]}<p>{a["text"]}</p><span class="small-muted">{a["created"][:16]}</span></div>',unsafe_allow_html=True)
    st.markdown("## ⭐ 저장한 질문")
    saved=q("SELECT * FROM bookmarks WHERE family_id=? ORDER BY question_date DESC",(fam["id"],))
    for b in saved:
        st.write(f"• {b['question_date']} — {today_question()[0] if b['question_date']==TODAY else '저장한 질문'}")

def calendar_page():
    fam=get_family()
    st.title("우리 가족 달력")
    st.caption("함께한 날과 가족의 기념일을 기억해요.")
    month=st.date_input("기준 날짜", value=date.today(), key="calendar_month")
    first=month.replace(day=1)
    next_month=(first.replace(day=28)+timedelta(days=4)).replace(day=1)
    last=next_month-timedelta(days=1)
    st.markdown(f"### {month.year}년 {month.month}월")
    import calendar
    weeks=calendar.monthcalendar(month.year,month.month)
    cols=st.columns(7)
    for col,wd in zip(cols,["월","화","수","목","금","토","일"]): col.markdown(f"**{wd}**")
    for week in weeks:
        cols=st.columns(7)
        for col,day in zip(cols,week):
            if day:
                d=date(month.year,month.month,day)
                marker="🌱" if d==date.fromisoformat(fam["established"]) else ("•" if d==date.today() else "")
                col.markdown(f"**{day}**<br><span class='small-muted'>{marker}</span>",unsafe_allow_html=True)
            else: col.write(" ")
    st.divider()
    st.markdown("### 🎂 가족 생일")
    for m in family_members(fam["id"]):
        try: bd=date.fromisoformat(m["birthday"])
        except: continue
        st.write(f"🎂 {m['name']} · {bd.month}월 {bd.day}일")
    st.markdown("### 🌿 가족이 함께한 날")
    st.metric("함께한 지",f"{dday(fam['established']):,}일")
    st.caption(f"처음 함께한 날: {fam['established']}")

def letters_page():
    fam,me=get_family(),current_member()
    st.title("비밀 편지")
    st.caption("미래의 어느 날, 소중한 마음을 열어보세요.")
    members=family_members(fam["id"])
    with st.expander("✉️ 새로운 비밀 편지 쓰기",expanded=True):
        with st.form("new_letter"):
            receiver_opts={f"{m['name']} ({m['role']})":m for m in members if m["id"]!=me["id"]}
            recipient=st.selectbox("받는 사람",list(receiver_opts) or ["나에게 쓰기"])
            title=st.text_input("편지 제목",placeholder="그날의 너에게")
            content=st.text_area("편지 내용",height=150,placeholder="전하고 싶은 마음을 적어 주세요.")
            unlock=st.date_input("편지를 열어볼 날짜",value=date.today()+timedelta(days=30),min_value=date.today())
            if st.form_submit_button("편지 봉인하기",use_container_width=True):
                target=receiver_opts.get(recipient)
                if not title.strip() or not content.strip(): st.error("제목과 내용을 모두 입력해 주세요.")
                else:
                    rid=uid()
                    run("INSERT INTO letters(id,family_id,sender_id,sender_name,receiver_id,receiver_name,title,content,created,unlock_date,opened) VALUES(?,?,?,?,?,?,?,?,?,?,0)",
                        (rid,fam["id"],me["id"],me["name"],target["id"] if target else me["id"],target["name"] if target else me["name"],title.strip(),content.strip(),datetime.now().isoformat(),unlock.isoformat()))
                    notify("편지를 안전하게 봉인했어요."); st.rerun()
    st.markdown("## 📬 나에게 온 편지")
    letters=q("SELECT * FROM letters WHERE family_id=? AND (receiver_id=? OR sender_id=?) ORDER BY unlock_date",(fam["id"],me["id"],me["id"]))
    if not letters: st.info("아직 편지가 없어요.")
    for letter in letters:
        available=date.today()>=date.fromisoformat(letter["unlock_date"])
        with st.container(border=True):
            st.markdown(f"**💌 {letter['title']}**")
            st.caption(f"{letter['sender_name']} → {letter['receiver_name']} · 열리는 날 {letter['unlock_date']}")
            if available:
                st.write(letter["content"])
                if not letter["opened"]:
                    run("UPDATE letters SET opened=1 WHERE id=?",(letter["id"],))
                    st.caption("✨ 오늘 편지가 열렸어요.")
            else:
                remain=(date.fromisoformat(letter["unlock_date"])-date.today()).days
                st.info(f"아직 봉인되어 있어요. {remain}일 후에 열 수 있어요.")

def more_page():
    fam,me=get_family()
    st.title("더보기")
    st.caption("가족 공간과 추억을 관리해요.")
    tabs=st.tabs(["가족 관리","우리의 버킷리스트","가족 메모","설정"])
    with tabs[0]:
        st.markdown("### 👨‍👩‍👧‍👦 가족 구성원")
        for m in family_members(fam["id"]):
            with st.container(border=True):
                st.write(f"**{m['name']}** · {m['role']} · {m['blood']}형")
                st.caption(f"생일 {m['birthday']} · 호칭 {m['call_name']}")
        st.markdown("### 새로운 가족 구성원 추가")
        with st.form("add_member"):
            name=st.text_input("이름",key="add_name")
            role=st.selectbox("역할",["엄마","아빠","딸","아들","할머니","할아버지","나"],key="add_role")
            call=st.text_input("부르는 호칭",key="add_call")
            birthday=st.date_input("생일",value=date(2010,1,1),min_value=date(1900,1,1),max_value=date.today(),key="add_birthday")
            blood=st.selectbox("혈액형",["A","B","O","AB"],key="add_blood")
            if st.form_submit_button("구성원 추가"):
                if name.strip():
                    run("INSERT INTO members VALUES(?,?,?,?,?,?,?,?,?)",(uid(),fam["id"],name.strip(),role,call.strip() or role,birthday.isoformat(),blood,"#DDE8D5",uid()))
                    notify("가족 구성원을 추가했어요."); st.rerun()
                else: st.error("이름을 입력해 주세요.")
        st.markdown("### 🔑 우리 가족 초대 코드")
        st.code(fam["invite"])
        st.caption("가족에게 초대 코드와 가족 비밀번호를 알려주세요.")
    with tabs[1]:
        st.markdown("### 함께 이루고 싶은 일")
        with st.form("bucket_add"):
            item=st.text_input("우리 가족의 버킷리스트",placeholder="예: 다 같이 바다 보러 가기")
            who=st.text_input("제안한 사람",value=me["name"])
            target=st.date_input("목표 날짜 (선택)",value=date.today()+timedelta(days=30))
            if st.form_submit_button("버킷리스트 추가"):
                if item.strip():
                    run("INSERT INTO bucket VALUES(?,?,?,?,?,?,?)",(uid(),fam["id"],item.strip(),who.strip(),target.isoformat(),0,datetime.now().isoformat()))
                    st.rerun()
        items=q("SELECT * FROM bucket WHERE family_id=? ORDER BY done,created DESC",(fam["id"],))
        for item in items:
            c1,c2=st.columns([5,1])
            with c1: st.write(("✅ " if item["done"] else "🌱 ")+item["text"]); st.caption(f"{item['proposer']} 제안 · 목표 {item['target_date']}")
            with c2:
                if st.button("취소" if item["done"] else "완료",key=f"bucket_{item['id']}"):
                    run("UPDATE bucket SET done=? WHERE id=?",(0 if item["done"] else 1,item["id"])); st.rerun()
    with tabs[2]:
        st.markdown("### 📌 가족 메모")
        with st.form("memo_add"):
            text=st.text_area("함께 기억할 내용을 적어 주세요.")
            color=st.selectbox("메모 색상",["크림","세이지","살구","하늘"])
            if st.form_submit_button("메모 붙이기"):
                if text.strip():
                    run("INSERT INTO memos VALUES(?,?,?,?,?,?)",(uid(),fam["id"],me["name"],text.strip(),color,datetime.now().isoformat())); st.rerun()
        for m in q("SELECT * FROM memos WHERE family_id=? ORDER BY created DESC",(fam["id"],)):
            with st.container(border=True):
                st.write(m["text"]); st.caption(f"{m['author']} · {m['created'][:16]} · {m['color']}")
                if st.button("삭제",key=f"memo_del_{m['id']}"):
                    run("DELETE FROM memos WHERE id=? AND family_id=?",(m["id"],fam["id"])); st.rerun()
    with tabs[3]:
        st.markdown("### ⚙️ 설정")
        st.toggle("큰 글씨 모드",key="font_large")
        st.markdown("### 가족 이름 변경")
        newname=st.text_input("가족 이름",value=fam["name"],key="rename_family")
        if st.button("가족 이름 저장"):
            if newname.strip():
                run("UPDATE family SET name=? WHERE id=?",(newname.strip(),fam["id"])); notify("가족 이름을 변경했어요."); st.rerun()
        st.markdown("### 가족 비밀번호 변경")
        newpin=st.text_input("새 비밀번호 (숫자 4자리)",type="password",max_chars=4,key="new_pin")
        if st.button("비밀번호 변경"):
            if len(newpin)==4 and newpin.isdigit():
                run("UPDATE family SET pin=? WHERE id=?",(newpin,fam["id"])); st.success("비밀번호를 변경했어요.")
            else: st.error("숫자 4자리로 입력해 주세요.")
        st.markdown("### 데이터 백업")
        if st.button("가족 데이터 JSON 내보내기"):
            data={"family":fam,"members":family_members(fam["id"])}
            for table in ["answers","letters","bucket","memos","signals"]:
                data[table]=q(f"SELECT * FROM {table} WHERE family_id=?",(fam["id"],))
            st.download_button("백업 파일 다운로드",json.dumps(data,ensure_ascii=False,indent=2).encode("utf-8"),file_name="sumone_family_backup.json",mime="application/json")
        st.caption("데이터는 이 Streamlit 앱의 SQLite 데이터베이스에 저장됩니다.")

# ------------------------------ App flow ------------------------------
fam=get_family()
if not fam:
    onboarding()
else:
    if not st.session_state.member_id or not current_member():
        login_member()
    else:
        header()
        show_notice()
        if st.session_state.font_large:
            st.markdown("<style>html,body,[class*='css']{font-size:1.08rem!important}</style>",unsafe_allow_html=True)
        nav=st.radio("메뉴",["홈","질문","달력","비밀 편지","더보기"],horizontal=True,label_visibility="collapsed",key="main_nav")
        st.session_state.page=nav
        if nav=="홈": home_page()
        elif nav=="질문": question_page()
        elif nav=="달력": calendar_page()
        elif nav=="비밀 편지": letters_page()
        elif nav=="더보기": more_page()
        st.divider()
        st.markdown("<div style='text-align:center;color:#9b9186;font-size:.8rem'>SUMONE · 우리들의 하루<br>가족의 오늘을 기록하는 작은 습관 🌱</div>",unsafe_allow_html=True)
