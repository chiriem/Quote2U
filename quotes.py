import requests
import streamlit as st  # Streamlit

# API Ninjas (Quotes API v2)
QUOTE_BASE = "https://api.api-ninjas.com"
QUOTES_ENDPOINT = "/v2/quotes"

# API Ninjas 문서 기준 카테고리(고정값)
AVAILABLE_CATEGORIES = {
    "wisdom",
    "philosophy",
    "life",
    "truth",
    "inspirational",
    "relationships",
    "love",
    "faith",
    "humor",
    "success",
    "courage",
    "happiness",
    "art",
    "writing",
    "fear",
    "nature",
    "time",
    "freedom",
    "death",
    "leadership",
}

# 한국어 키워드 → API Ninjas categories 매핑
# 부분 문자열 포함 기준으로 점수화
KO_TO_CATEGORY_RULES = [
    (["불안", "걱정", "초조", "긴장"], ["fear", "wisdom"]),
    (["스트레스", "압박", "부담", "번아웃", "지침", "탈진"], ["life", "wisdom"]),
    (["우울", "슬픔", "눈물", "상실"], ["life", "happiness"]),
    (["무기력", "의욕", "미루", "포기"], ["inspirational", "success"]),
    (["실패", "좌절", "자책"], ["courage", "success"]),
    (["분노", "짜증", "화남"], ["wisdom", "courage"]),
    (["관계", "갈등", "이별"], ["relationships", "love"]),
    (["외로"], ["relationships", "life"]),
    (["자존감", "자기비난"], ["inspirational", "wisdom"]),
    (["마감", "일", "회사", "업무"], ["success", "leadership"]),
]


def build_query_english(user_text: str) -> str:
    """
    기존 app.py 인터페이스를 유지하기 위해 함수명은 그대로 둔다.
    반환값은 '영문 단어'가 아니라 API Ninjas의 categories 문자열.
    예) "fear" 또는 "success,leadership"
    """
    if not user_text:
        return "life"

    t = user_text.strip()
    scored: list[tuple[int, list[str]]] = []

    for ko_keys, cats in KO_TO_CATEGORY_RULES:
        score = 0
        for k in ko_keys:
            if k in t:
                score += 1
        if score > 0:
            scored.append((score, cats))

    if not scored:
        return "life"

    scored.sort(key=lambda x: x[0], reverse=True)

    # 상위 1~2개 규칙만 사용
    picked = []
    for _, cats in scored[:2]:
        if cats:
            picked.append(cats[0])

    # 중복 제거 + 유효 카테고리만 유지
    out = []
    for c in picked:
        c = (c or "").strip()
        if c and c in AVAILABLE_CATEGORIES and c not in out:
            out.append(c)

    return ",".join(out) if out else "life"


def _get_api_key() -> str:
    return (st.secrets.get("API_NINJAS_KEY") or "").strip()


def fetch_quotes(query: str, timeout_seconds: float = 6.0, retry_once: bool = True) -> list[dict]:
    """
    API Ninjas에서 명언 후보를 가져옴
    반환은 프로젝트 내부 인터페이스에 맞춰 {"content","author"}로 정규화
    """
    api_key = _get_api_key()
    if not api_key:
        st.error("api 키 설정 오류")
        st.stop()

    url = f"{QUOTE_BASE}{QUOTES_ENDPOINT}"
    headers = {"X-Api-Key": api_key}

    categories = [c.strip() for c in (query or "").split(",") if c.strip()]
    if not categories:
        categories = ["life"]
    categories = categories[:2]

    def _call_one(cat: str) -> dict | None:
        params = {"categories": cat}
        r = requests.get(url, params=params, headers=headers, timeout=timeout_seconds)
        r.raise_for_status()
        data = r.json()

        # 응답은 배열이며, 첫 원소에 quote/author/categories 등이 포함
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            return None

        content = (data[0].get("quote") or "").strip()
        author = (data[0].get("author") or "").strip()

        if not content:
            return None

        return {"content": content, "author": author or "Unknown"}

    out: list[dict] = []

    for cat in categories:
        try:
            item = _call_one(cat)
            if item:
                out.append(item)
        except Exception:
            if not retry_once:
                continue
            try:
                item = _call_one(cat)
                if item:
                    out.append(item)
            except Exception:
                continue

    return out


def pick_two_quotes(candidates: list[dict]) -> list[dict]:
    """후보에서 문장 중복만 제거하고 앞에서부터 2개 선택"""
    picked = []
    seen = set()

    for q in candidates:
        content = (q.get("content") or "").strip()
        author = (q.get("author") or "").strip()
        if not content:
            continue

        key = " ".join(content.lower().split())
        if key in seen:
            continue

        seen.add(key)
        picked.append({"content": content, "author": author or "Unknown"})

        if len(picked) >= 2:
            break

    return picked
