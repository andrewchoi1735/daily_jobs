import streamlit as st
import pandas as pd
from datetime import datetime

# 데이터 불러오기/생성
try:
    df = pd.read_csv("calendar_diary.csv")
except FileNotFoundError:
    df = pd.DataFrame(columns=["날짜", "제목", "내용"])

st.title("캘린더 & 일지")

date = st.date_input("날짜를 선택하세요", datetime.now())
date_str = date.strftime("%Y-%m-%d")

# 세션 상태
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None
if "title_input" not in st.session_state:
    st.session_state.title_input = ""
if "content_input" not in st.session_state:
    st.session_state.content_input = ""
if "delete_index" not in st.session_state:
    st.session_state.delete_index = None

st.subheader(f"'{date_str}'의 모든 기록")

filtered = df[df["날짜"] == date_str]
if filtered.empty:
    st.info("아직 작성된 기록이 없습니다.")
else:
    # 각 기록을 카드 형태로!
    for idx, row in filtered.iterrows():
        with st.container():
            st.markdown(
                f"""
                <div style='
                    border-radius:16px;
                    border:1px solid #444;
                    background: #222;
                    padding:24px 24px 10px 24px;
                    margin-bottom:18px;
                    box-shadow: 2px 2px 8px #1111;
                '>
                  <div style='font-size:20px; font-weight:bold; color:#ddd; margin-bottom:6px;'>📝 {row['제목']}</div>
                  <div style='color:#ccc; margin-bottom:18px; white-space:pre-line;'>{row['내용']}</div>
                """,
                unsafe_allow_html=True
            )
            # 버튼을 카드 아래에 중앙정렬
            btn_col1, btn_col2 = st.columns([1,0.1])
            with btn_col1:
                if st.button("수정", key=f"edit_{idx}"):
                    st.session_state.show_form = True
                    st.session_state.edit_index = row.name
                    st.session_state.title_input = row['제목']
                    st.session_state.content_input = row['내용']
            with btn_col2:
                if st.button("삭제", key=f"del_{idx}"):
                    st.session_state.delete_index = row.name
            st.markdown("</div>", unsafe_allow_html=True)

# 삭제 처리
if st.session_state.delete_index is not None:
    df = df.drop(st.session_state.delete_index)
    df = df.reset_index(drop=True)
    df.to_csv("calendar_diary.csv", index=False)
    st.session_state.delete_index = None
    st.session_state.show_form = False
    st.session_state.edit_index = None
    st.session_state.title_input = ""
    st.session_state.content_input = ""
    st.rerun()

if st.button("기록 추가"):
    st.session_state.show_form = True
    st.session_state.edit_index = None
    st.session_state.title_input = ""
    st.session_state.content_input = ""

if st.session_state.show_form:
    if st.session_state.edit_index is not None:
        st.subheader("기록 수정")
    else:
        st.subheader("새 기록 추가")
    with st.form("add_edit_form"):
        title = st.text_input("제목", st.session_state.title_input)
        content = st.text_area("내용", st.session_state.content_input)
        submitted = st.form_submit_button("저장")
        cancel = st.form_submit_button("취소")
        if submitted and title:
            if st.session_state.edit_index is not None:
                df.loc[st.session_state.edit_index, "제목"] = title
                df.loc[st.session_state.edit_index, "내용"] = content
                st.success("수정 완료!")
            else:
                new_row = pd.DataFrame([[date_str, title, content]], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True)
                st.success("저장 완료!")
            df.to_csv("calendar_diary.csv", index=False)
            st.session_state.show_form = False
            st.session_state.edit_index = None
            st.session_state.title_input = ""
            st.session_state.content_input = ""
            st.rerun()
        if cancel:
            st.session_state.show_form = False
            st.session_state.edit_index = None
            st.session_state.title_input = ""
            st.session_state.content_input = ""
            st.rerun()

st.markdown("---")
with st.expander("📅 전체 기록(최근순 보기)"):
    st.dataframe(df[::-1])
