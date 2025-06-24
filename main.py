import streamlit as st
import pandas as pd
from datetime import datetime
import os

USERS_FILE = ".users.csv"
LAST_USER_FILE = ".last_user"
USER_FIELDS = ["user_id", "password"]

# 회원정보 파일 최초 준비
if not os.path.exists(USERS_FILE):
	pd.DataFrame(columns=USER_FIELDS).to_csv(USERS_FILE, index=False)


# last_user 자동로그인 파일 읽기
def load_last_user():
	if os.path.exists(LAST_USER_FILE):
		with open(LAST_USER_FILE, "r") as f:
			return f.read().strip()
	return ""


def save_last_user(user_id):
	with open(LAST_USER_FILE, "w") as f:
		f.write(user_id)


def remove_last_user():
	if os.path.exists(LAST_USER_FILE):
		os.remove(LAST_USER_FILE)


# 로그인/회원가입
def login_or_register():
	st.title("🔑 캘린더&일지 로그인")
	tab1, tab2 = st.tabs(["로그인", "회원가입"])
	with tab1:
		login_id = st.text_input("ID", key="login_id")
		login_pw = st.text_input("Password", type="password", key="login_pw")
		if st.button("로그인"):
			users = pd.read_csv(USERS_FILE)
			match = users[(users["user_id"] == login_id) & (users["password"] == login_pw)]
			if not match.empty:
				st.session_state.user_id = login_id
				save_last_user(login_id)
				st.success(f"{login_id}님 환영합니다!")
				st.rerun()
			else:
				st.error("ID 또는 비밀번호가 올바르지 않습니다.")
	with tab2:
		reg_id = st.text_input("ID(회원가입)", key="reg_id")
		reg_pw = st.text_input("Password(회원가입)", type="password", key="reg_pw")
		if st.button("회원가입"):
			users = pd.read_csv(USERS_FILE)
			if reg_id in users["user_id"].values:
				st.warning("이미 사용 중인 ID입니다.")
			elif not reg_id or not reg_pw:
				st.warning("ID/비밀번호를 모두 입력하세요.")
			else:
				new_user = pd.DataFrame([[reg_id, reg_pw]], columns=USER_FIELDS)
				users = pd.concat([users, new_user], ignore_index=True)
				users.to_csv(USERS_FILE, index=False)
				st.session_state.user_id = reg_id
				save_last_user(reg_id)
				st.success("회원가입 완료! 바로 시작합니다.")
				st.rerun()


# 로그인 상태 유지
if "user_id" not in st.session_state or not st.session_state.user_id:
	last = load_last_user()
	if last:
		st.session_state.user_id = last
	else:
		st.session_state.user_id = ""
if not st.session_state.user_id:
	login_or_register()
	st.stop()

user_id = st.session_state.user_id
st.sidebar.write(f"👤 {user_id} 님")
if st.sidebar.button("로그아웃"):
	for key in list(st.session_state.keys()):
		del st.session_state[key]
	remove_last_user()
	st.rerun()

st.title(f"📅 {user_id}님의 캘린더 & 일지")
filename = f"{user_id}_calendar_diary.csv"

try:
	df = pd.read_csv(filename)
except FileNotFoundError:
	df = pd.DataFrame(columns=["날짜", "제목", "내용"])

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
			btn_col1, btn_col2 = st.columns([1, 0.1])
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
	df.to_csv(filename, index=False)
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
			df.to_csv(filename, index=False)
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
