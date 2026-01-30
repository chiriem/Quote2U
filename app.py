import streamlit as st
from openai import OpenAI

from safety import is_crisis
from quotes import build_query_english, fetch_quotes, pick_two_quotes
from prompts import SYSTEM_INSTRUCTIONS, build_user_input
from utils import normalize_output


def get_client() -> OpenAI:
    # Streamlit secrets에서 키를 읽음
    api_key = st.secrets.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        st.error("OPENAI_API_KEY가 설정되지 않았습니다. .streamlit/secrets.toml을 확인하세요.")
        st.stop()
    return OpenAI(api_key=api_key)


def call_llm(client: OpenAI, model: str, system_instructions: str, user_input: str) -> str:
    # Responses API로 1회 호출
    resp = client.responses.create(
        model=model,
        instructions=system_instructions,
        input=user_input,
    )
    # SDK는 output_text 편의 필드를 제공
    return getattr(resp, "output_text", "") or ""


def main():
    st.set_page_config(page_title="Quote2U", page_icon="💬")
    st.title("Quote2U.")

    placeholder = (
        "예시)\n"
        "요즘 일이 너무 많아서 지치고, 뭘 해도 의욕이 안 나요.\n"
        "실수할까 봐 걱정도 커서 시작이 잘 안 됩니다."
    )

    user_text = st.text_area("지금 기분과 상황을 적어주세요", height=160, placeholder=placeholder)

    if st.button("응답 받기"):
        with st.spinner("생각 중..."):
            crisis = is_crisis(user_text)

            # 검색 query 생성(규칙 기반)
            query = build_query_english(user_text)

            # 명언 후보 가져오기(타임아웃 5초, 실패 시 1회 재시도)
            candidates = fetch_quotes(query=query, timeout_seconds=5.0, retry_once=True)
            picked = pick_two_quotes(candidates)

            client = get_client()
            model = (st.secrets.get("MODEL_NAME") or "gpt-4.1-mini").strip()

            user_input = build_user_input(user_text=user_text, quotes=picked, crisis=crisis)
            out = call_llm(client=client, model=model, system_instructions=SYSTEM_INSTRUCTIONS, user_input=user_input)
            out_norm = normalize_output(out)

        st.text(out_norm)

if __name__ == "__main__":
    main()
