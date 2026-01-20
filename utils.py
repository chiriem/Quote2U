import re


def normalize_output(text: str) -> str:
    """
    출력이 4개 항목을 벗어나지 않도록 정리
    - 모델이 공백 줄을 섞어도 4줄만 남김
    - 접두어가 있으면 그 줄을 우선 사용
    """
    if not text:
        return ""

    raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # 접두어 라인 우선 수집
    want = ["명언 1)", "명언 2)", "조언 1)", "조언 2)"]
    picked = []
    for w in want:
        for ln in raw_lines:
            if ln.startswith(w):
                picked.append(ln)
                break

    # 부족하면 앞에서부터 채움
    if len(picked) < 4:
        for ln in raw_lines:
            if ln in picked:
                continue
            picked.append(ln)
            if len(picked) >= 4:
                break

    # 그래도 부족하면 빈 항목 채우기
    while len(picked) < 4:
        idx = len(picked) + 1
        if idx <= 2:
            picked.append(f"명언 {idx}) “오늘의 문장” — 작자 미상")
        else:
            picked.append(f"조언 {idx-2}) 지금 할 수 있는 작은 행동 하나를 10분만 해보세요. 부담을 낮추면 시작이 쉬워집니다.")

    return "\n".join(picked[:4])
