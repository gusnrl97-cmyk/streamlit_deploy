import streamlit as st
from openai import OpenAI


st.set_page_config(page_title="OpenAI Chatbot", page_icon="🤖", layout="centered")

st.title("🤖 OpenAI Chatbot")
st.caption("Streamlit Share 배포용 챗봇 예시")


def get_api_key() -> str | None:
    # Streamlit Share에서는 Secrets에 저장된 값을 우선 사용
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]
    # 로컬 테스트용 입력
    return st.session_state.get("local_openai_api_key")


with st.sidebar:
    st.header("설정")
    model = st.selectbox(
        "모델",
        ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"],
        index=0,
    )
    if "OPENAI_API_KEY" not in st.secrets:
        st.text_input(
            "OPENAI API Key",
            type="password",
            key="local_openai_api_key",
            help="배포 시에는 Streamlit Secrets에 OPENAI_API_KEY를 넣으세요.",
        )
    temperature = st.slider("창의성(temperature)", 0.0, 1.5, 0.7, 0.1)
    max_tokens = st.slider("최대 토큰", 128, 2048, 512, 64)
    if st.button("대화 초기화"):
        st.session_state["messages"] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        st.rerun()


if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

# 화면에는 system 메시지는 숨기고 표시
for m in st.session_state["messages"]:
    if m["role"] == "system":
        continue
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


user_prompt = st.chat_input("메시지를 입력하세요...")
if user_prompt:
    api_key = get_api_key()
    if not api_key:
        st.error("API 키가 없습니다. Streamlit Secrets 또는 사이드바 입력을 확인하세요.")
        st.stop()

    st.session_state["messages"].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=st.session_state["messages"],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        answer = response.choices[0].message.content or ""
    except Exception as e:
        st.error(f"API 호출 오류: {e}")
        st.stop()

    st.session_state["messages"].append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
