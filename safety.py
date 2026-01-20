# 위기 감지 탐지

CRISIS_SUBSTRINGS = [
    "자살",
    "자해",
    "유서",
    "손목",
    "목숨",
    "죽고 싶",
    "죽이고 싶",
]


def is_crisis(text: str) -> bool:
    """텍스트에 위기 감지 키워드가 포함되는지 확인"""
    if not text:
        return False
    t = text.strip()
    return any(s in t for s in CRISIS_SUBSTRINGS)