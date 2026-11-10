# -*- coding: utf-8 -*-
"""하루담 | 가족의 하루를 담는 공간 · Streamlit edition
Run: streamlit run app.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

import streamlit as st

APP_TITLE = "하루담"
DB_PATH = os.environ.get("HARUDAM_DB_PATH", "harudam_family.db")
TODAY = date.today().isoformat()

st.set_page_config(page_title=APP_TITLE, page_icon="🍃", layout="centered", initial_sidebar_state="collapsed")

# ------------------------------ Styling ------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Nanum+Myeongjo:wght@400;700&display=swap');
:root { --ink:#51463d; --muted:#9a8d80; --cream:#faf7f1; --card:#fffefa; --line:#eee4d8; --sage:#9cab8d; --sage-pale:#eef1e8; --peach:#f3e5d6; }
html, body, [class*="css"] { font-family:'Gowun Dodum',sans-serif; color:var(--ink); }
.stApp { background:var(--cream); }
.block-container { max-width:500px; padding:0.65rem 0.85rem 6.5rem!important; }
h1,h2,h3 { color:var(--ink); letter-spacing:-.035em; }
h1 { font-family:'Nanum Myeongjo',serif; font-size:1.55rem!important; }
h2 { font-size:1.18rem!important; }
h3 { font-size:1rem!important; }
p { line-height:1.55; }
.stButton>button, .stFormSubmitButton>button { border-radius:999px; border:1px solid #e8ddcf; background:#fffefa; color:#766958; font-weight:600; min-height:2.45rem; }
.stButton>button:hover, .stFormSubmitButton>button:hover { background:#eef1e8; border-color:#cbd5c0; color:#53634c; }
.stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] { border-radius:12px; background:#fffefa; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:var(--card); border:1px solid var(--line); border-radius:19px; padding:12px 14px; }
div[data-testid="stAlert"] { border-radius:14px; }
.small-muted { color:var(--muted); font-size:.8rem; }
.hero { background:linear-gradient(135deg,#f1f0e7,#fbf0e7); border:1px solid #eee5d8; padding:17px; border-radius:22px; margin:8px 0 13px; }
.hero-title { font-family:'Nanum Myeongjo',serif; font-size:1.42rem; line-height:1.5; }
.pill { display:inline-block; padding:4px 9px; background:#f0eadf; color:#897b69; border-radius:99px; font-size:.76rem; margin:2px; }
.answer-card { background:#fffefa; border:1px solid var(--line); border-radius:16px; padding:12px; margin:7px 0; }
div[data-testid="stTabs"] button { font-size:.88rem; }
div[data-testid="stRadio"] { position:fixed; z-index:1000; left:0; bottom:0; width:100%; box-sizing:border-box; padding:8px 8px calc(8px + env(safe-area-inset-bottom)); background:rgba(250,247,241,.97); border-top:1px solid #e9dfd3; backdrop-filter:blur(12px); }
div[data-testid="stRadio"] > label { display:none; }
div[data-testid="stRadio"] > div { max-width:500px; margin:0 auto; display:flex; justify-content:space-around; gap:2px; }
div[data-testid="stRadio"] label { flex:1; justify-content:center; text-align:center; padding:7px 2px!important; margin:0!important; border:0!important; border-radius:12px!important; background:transparent!important; color:#9b8c7d!important; font-size:.72rem!important; }
div[data-testid="stRadio"] label:has(input:checked) { background:#eee9df!important; color:#5e5144!important; font-weight:700; }
div[data-testid="stRadio"] label p { font-size:.72rem!important; margin:0!important; white-space:nowrap; }
div[data-testid="stRadio"] input { display:none!important; }
header[data-testid="stHeader"] { background:transparent; }
[data-testid="stToolbar"], footer { visibility:hidden; }
@media (min-width:700px) {
  .block-container { max-width:500px!important; }
}
@media (max-width:380px) {
  .block-container { padding-left:.65rem!important; padding-right:.65rem!important; }
  div[data-testid="stRadio"] label p { font-size:.66rem!important; }
}
</style>
""", unsafe_allow_html=True)


# ------------------------------ App launch splash ------------------------------
# 세션에서 한 번만 표시되는 앱 시작 화면
if "harudam_splash_done" not in st.session_state:
    st.session_state.harudam_splash_done = False

if not st.session_state.harudam_splash_done:
    splash_slot = st.empty()
    with splash_slot:
        st.markdown("""
        <style>
        .stApp:has(.harudam-splash) .block-container { padding-top:0!important; }
        .harudam-splash {
            position:fixed; inset:0; z-index:999999;
            display:flex; flex-direction:column; align-items:center; justify-content:center;
            background:linear-gradient(145deg,#f7f4eb 0%,#f5eee5 55%,#edf0e7 100%);
            animation:harudamFade 2.15s ease forwards;
        }
        .harudam-mark {
            width:88px;height:88px;border-radius:28px;
            display:flex;align-items:center;justify-content:center;
            background:linear-gradient(145deg,#e5ebdc,#f8e9dc);
            box-shadow:0 12px 35px rgba(94,105,79,.12);
            font-size:43px;margin-bottom:18px;
            animation:harudamPop .65s cubic-bezier(.2,.8,.2,1) both;
        }
        .harudam-name {
            font-family:'Nanum Myeongjo',serif;font-size:34px;letter-spacing:.12em;
            color:#493f36;animation:harudamText .8s ease both;
        }
        .harudam-sub { margin-top:10px;color:#8b8075;font-size:13px;letter-spacing:.04em; }
