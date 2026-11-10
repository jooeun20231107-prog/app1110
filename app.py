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
            st.download_button("백업 파일 다운로드",json.dumps(data,ensure_ascii=False,indent=2).encode("utf-8"),file_name="harudam_family_backup.json",mime="application/json")
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
        st.markdown("<div style='text-align:center;color:#9b9186;font-size:.8rem'>하루담<br>가족의 오늘을 기록하는 작은 습관 🍃</div>",unsafe_allow_html=True)
