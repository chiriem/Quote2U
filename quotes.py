import requests

# Quotable API
QUOTABLE_BASE = "https://api.quotable.io"

# 한국어 입력 → 영문 query 매핑
# 키워드는 부분 포함 기준으로 카운트
KO_TO_EN_RULES = [
    (["불안", "걱정", "초조"], ["anxiety", "worry"]),
    (["스트레스", "압박", "부담"], ["stress", "pressure"]),
    (["우울", "슬픔", "눈물"], ["sadness", "grief"]),
    (["무기력", "의욕", "미루"], ["motivation", "discipline"]),
    (["분노", "짜증", "화남"], ["anger", "patience"]),
    (["번아웃", "지침", "탈진"], ["burnout", "rest"]),
    (["실패", "좌절"], ["failure", "resilience"]),
    (["관계", "갈등", "이별"], ["relationships", "love"]),
    (["외로"], ["loneliness", "connection"]),
    (["자존감", "자기비난"], ["self-esteem", "self-compassion"]),
    (["마감", "일", "회사", "업무"], ["work", "focus"]),
]


def build_query_english(user_text: str) -> str:
    """한국어 입력을 규칙 기반으로 영문 검색 query로 변환"""
    if not user_text:
        return "life"

    t = user_text.strip()
    scored = []

    for ko_keys, en_terms in KO_TO_EN_RULES:
        score = 0
        for k in ko_keys:
            if k in t:
                score += 1
        if score > 0:
            scored.append((score, en_terms))

    if not scored:
        return "life"

    scored.sort(key=lambda x: x[0], reverse=True)

    # 상위 1~2개 카테고리만 사용
    top_terms = []
    for _, en_terms in scored[:2]:
        top_terms.append(en_terms[0])

    return " ".join(top_terms).strip() if top_terms else "life"


def fetch_quotes(query: str, timeout_seconds: float = 3.0, retry_once: bool = True) -> list[dict]:
    """
    명언 후보 가져오기
    - 기본 타임아웃 3초, 실패 시 1회 재시도
    """
    params = {
        "query": query,
        "limit": 20,
        "page": 1,
    }
    url = f"{QUOTABLE_BASE}/quotes"

    def _call() -> list[dict]:
        r = requests.get(url, params=params, timeout=timeout_seconds)
        r.raise_for_status()
        data = r.json()
        # results에 content/author 등이 담김
        return data.get("results", []) if isinstance(data, dict) else []

    try:
        return _call()
    except Exception:
        if not retry_once:
            return []
        # 1회 재시도
        try:
            return _call()
        except Exception:
            return []


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
