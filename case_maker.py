import streamlit as st
import json
from openai import OpenAI
from datetime import datetime
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

client = OpenAI(api_key="")  # <-- 본인 키 입력

st.title("테스트케이스 생성 대시보드 ")

if "tc_history" not in st.session_state:
	st.session_state.tc_history = []

feature = st.text_input("기능명")
description = st.text_area("설명/요구사항")


def make_prompt_qase_json(feature, description, n=10):
	return f"""
당신은 이제 전문적인 QA 엔지니어입니다. 아래 요구사항에 맞는 테스트케이스를 생성해주세요.

[요청 사항]
- QASE Testcase 관리툴용 JSON 포맷 테스트케이스 {n}개 생성
- 각 테스트케이스는 반드시 고유해야 하며, 중복된 시나리오는 허용되지 않음
- JSON 배열 형식으로만 출력 (설명, 코드블록, 마크다운 제외)

[테스트 케이스 작성 원칙]
1. 중복 방지 원칙
- 각 테스트케이스는 고유한 테스트 목적을 가져야 함
- 유사한 시나리오더라도 테스트하는 관점이 다르다면 분리하여 작성
- 이전에 작성한 케이스와 중복되지 않도록 항상 비교 검토
- title, description, steps가 80% 이상 유사한 케이스 생성 금지
- 동일한 테스트 목적을 가진 케이스 생성 금지
- 단순히 데이터만 다른 케이스 생성 금지

2. 테스트 커버리지 분배
- 기능 테스트: 40%
- 예외/비기능 테스트: 40%
- 보안 테스트: 20%

3. 케이스 우선순위 분배
- Critical/High: 30%
- Medium: 40%
- Low: 30%

[테스트케이스 필수 필드]
1. 기본 정보
- title: 고유한 식별이 가능하도록 구체적으로 작성
- description: 해당 케이스만의 특별한 테스트 조건과 목적을 명시
- preconditions: 구체적인 선행 조건
- postconditions: 명확한 완료 조건

2. 메타데이터
- priority: "Critical", "High", "Medium", "Low" 중 선택
- severity: "Critical", "Major", "Minor", "Low" 중 선택
- type: "Functional", "Security", "Performance", "Usability", "Compatibility" 중 선택
- behavior: "Positive", "Negative", "Destructive" 중 선택
- automation: "Manual", "Automated", "Semi-automated" 중 선택
- status: "Actual" 고정
- is_flaky: false 고정
- layer: "E2E", "API", "Unit" 중 선택
- milestone: ""
- custom_fields: ""
- steps_type: "classic" 고정
- tags: 관련 키워드 배열
- params: ""
- is_muted: false 고정

3. 테스트 단계(steps)
- 각 단계는 구체적이고 검증 가능해야 함
- 최소 3단계, 최대 7단계로 구성
- position은 1부터 순차 증가

- data 필드는 실제 테스트에 필요한 값만 포함

테스트 대상 기능 정보:
- 기능명: {feature}
- 설명/요구사항: {description}
"""


def extract_json(text):
	# 마크다운 블록 등 제거, JSON 배열만 추출
	md_block = re.search(r"```json(.*?)```", text, re.DOTALL)
	if md_block:
		return md_block.group(1).strip()
	first = min([i for i in [text.find("["), text.find("{")] if i >= 0], default=0)
	last = max([text.rfind("]"), text.rfind("}")])
	return text[first:last + 1].strip()


def try_fix_and_load_json(json_str):
	# 마지막 콤마 제거
	json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
	# 대괄호, 중괄호 개수 맞추기
	open_sq, close_sq = json_str.count('['), json_str.count(']')
	open_cu, close_cu = json_str.count('{'), json_str.count('}')
	if open_sq > close_sq:
		json_str += ']' * (open_sq - close_sq)
	if open_sq < close_sq:
		json_str = json_str.rstrip(']')
	if open_cu > close_cu:
		json_str += '}' * (open_cu - close_cu)
	if open_cu < close_cu:
		json_str = json_str.rstrip('}')
	# 큰따옴표 특수문자 보정
	json_str = json_str.replace("‘", "\"").replace("’", "\"").replace('“', '"').replace('”', '"')
	try:
		obj = json.loads(json_str)
		return obj, None
	except Exception as e:
		return None, str(e)


def tc_to_qase_xml(feature, description, cases):
	root = ET.Element("nodes")
	suites = ET.SubElement(root, "suites")
	suite = ET.SubElement(suites, "node")
	ET.SubElement(suite, "id").text = "1"
	ET.SubElement(suite, "title").text = feature
	ET.SubElement(suite, "description").text = ""
	ET.SubElement(suite, "preconditions").text = ""
	ET.SubElement(suite, "suites")  # empty
	cases_node = ET.SubElement(suite, "cases")

	for i, case in enumerate(cases, 1):
		c = ET.SubElement(cases_node, "node")
		ET.SubElement(c, "id").text = str(i)
		ET.SubElement(c, "title").text = case.get("title", "")
		ET.SubElement(c, "description").text = case.get("description", "")
		ET.SubElement(c, "preconditions").text = case.get("preconditions", "")
		ET.SubElement(c, "postconditions").text = case.get("postconditions", "")
		ET.SubElement(c, "priority").text = case.get("priority", "")
		ET.SubElement(c, "severity").text = case.get("severity", "")
		ET.SubElement(c, "type").text = case.get("type", "")
		ET.SubElement(c, "behavior").text = case.get("behavior", "")
		ET.SubElement(c, "automation").text = case.get("automation", "")
		ET.SubElement(c, "status").text = case.get("status", "")
		ET.SubElement(c, "is_flaky").text = str(case.get("is_flaky", ""))
		ET.SubElement(c, "layer").text = case.get("layer", "")
		ET.SubElement(c, "milestone").text = case.get("milestone", "")
		ET.SubElement(c, "custom_fields").text = str(case.get("custom_fields", ""))
		ET.SubElement(c, "steps_type").text = case.get("steps_type", "classic")
		steps_node = ET.SubElement(c, "steps")
		for step_idx, step in enumerate(case.get('steps', []), 1):
			s = ET.SubElement(steps_node, "node")
			ET.SubElement(s, "position").text = str(step.get("position", step_idx))
			ET.SubElement(s, "action").text = step.get("action", "")
			ET.SubElement(s, "expected_result").text = step.get("expected_result", "")
			ET.SubElement(s, "data").text = step.get("data", "")
			ET.SubElement(s, "steps")  # empty
		ET.SubElement(c, "tags").text = str(case.get("tags", ""))
		ET.SubElement(c, "params").text = str(case.get("params", ""))
		ET.SubElement(c, "is_muted").text = str(case.get("is_muted", "no"))

	xml_str = ET.tostring(root, encoding="utf-8")
	return minidom.parseString(xml_str).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


if st.button("테스트케이스 생성") and feature:
	with st.spinner("생성 중..."):
		all_cases = []
		error_flag = False
		for n in [10]:
			prompt = make_prompt_qase_json(feature, description, n=n)
			response = client.chat.completions.create(
				model="gpt-4o",
				messages=[{"role": "user", "content": prompt}],
				max_tokens=3500,
				temperature=0.1,
			)
			raw_result = response.choices[0].message.content
			json_str = extract_json(raw_result)
			obj, err = try_fix_and_load_json(json_str)
			if obj:
				all_cases.extend(obj)
			else:
				st.warning(f"JSON 파싱 실패, 원본 출력:\n{err}")
				st.code(raw_result, language="json")
				st.download_button(
					label="깨진 원본 결과 다운로드",
					data=raw_result,
					file_name=f"broken_testcases_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
				)
				error_flag = True
				break

		if not error_flag and all_cases:
			st.session_state.tc_history.insert(0, {
				"feature": feature,
				"description": description,
				"cases": all_cases,
				"created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			})
			st.success("생성 성공! 아래에서 확인 및 다운로드 하세요.")

st.markdown("---")
st.subheader("최근 생성된 테스트케이스 목록")

if st.session_state.tc_history:
	for i, record in enumerate(st.session_state.tc_history):
		with st.expander(f"[{record['created_at']}] {record['feature']}"):
			st.markdown(f"**설명:** {record['description']}")
			for j, case in enumerate(record["cases"]):
				with st.expander(f"#{j + 1} {case.get('title', '')}", expanded=False):
					st.markdown(f"**Description:** {case.get('description', '')}")
					st.markdown(f"**Precondition:** {case.get('preconditions', '')}")
					st.markdown("**Steps:**")
					for step in case.get('steps', []):
						st.markdown(f"- {step.get('action', '')}")
						st.markdown(f"  - Input data: {step.get('data', '')}")
						st.markdown(f"  - Expected result: {step.get('expected_result', '')}")
			# 개별 기록 xml 다운로드
			xml_content = tc_to_qase_xml(record["feature"], record["description"], record["cases"])
			st.download_button(
				label="XML 확장자로 다운로드",
				data=xml_content,
				file_name=f"{record['feature']}_cases.xml",
				mime="application/xml"
			)
			# JSON도 같이 다운 가능
			st.download_button(
				label="JSON 확장자로 다운로드",
				data=json.dumps(record["cases"], ensure_ascii=False, indent=2),
				file_name=f"{record['feature']}_cases.json",
				mime="application/json"
			)

	# 전체 기록을 한번에 다운로드 (예시: 전체 XML)
	all_cases_flat = []
	for rec in st.session_state.tc_history:
		for case in rec["cases"]:
			all_cases_flat.append(case)
	xml_content = tc_to_qase_xml(
		"All_Features",
		"모든 기록 합본",
		all_cases_flat
	)
	st.download_button(
		label="생성된 모든 항목 XML 확장자로 다운로드",
		data=xml_content,
		file_name="all_testcase_history.xml",
		mime="application/xml"
	)
else:
	st.info("아직 생성된 테스트케이스가 없습니다.")
