# over68.csv의 68개 카테고리에 대해 설명문/키워드를 LLM 1회 호출로 생성을 위한 파일

from __future__ import annotations

from pathlib import Path
import csv

import pandas as pd
from openai import OpenAI
import os

def _read_api_key() -> str:

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    return api_key

def main():
    in_path = Path("data/over68.csv")
    out_path = Path("data/over68_enriched.csv")

    df = pd.read_csv(in_path)

    categories = [str(x).strip() for x in df["category"].tolist()]

    api_key = _read_api_key()

    client = OpenAI(api_key=api_key)

    # LLM 1회 호출로 68개 생성
    # 출력은 CSV 형태로 강제
    instructions = (
        "너는 카테고리 라벨에 대한 한국어 설명문 생성기다.\n"
        "입력으로 카테고리 목록이 주어지면, 각 카테고리에 대해:\n"
        "1) desc_ko: 1문장 설명(한국어, 너무 추상적이지 않게)\n"
        "2) keywords_ko: 6~10개 키워드(한국어, 쉼표로 구분)\n"
        "를 생성하라.\n\n"
        "출력은 반드시 CSV 형식의 텍스트로만 작성하라.\n"
        "헤더는 다음과 같다:\n"
        "category,desc_ko,keywords_ko\n"
        "각 행의 category는 입력과 정확히 동일한 문자열을 사용하라.\n"
        "불필요한 추가 설명/문장/코드는 출력하지 마라.\n"
    )

    # 카테고리 목록은 그대로 전달
    user_input = "카테고리 목록:\n" + "\n".join(f"- {c}" for c in categories)

    resp = client.responses.create(
        model="gpt-4o-mini",
        instructions=instructions,
        input=user_input,
    )

    text = (getattr(resp, "output_text", "") or "").strip()
    if not text:
        raise RuntimeError("LLM 출력이 비어 있습니다.")

    # CSV 파싱 (LLM 출력이 틀어질 수 있으니 최소 방어)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines or "category,desc_ko,keywords_ko" not in lines[0].replace(" ", ""):
        # 헤더가 조금 틀려도 대충 통과시키지 않고 실패로 처리(포트폴리오 품질)
        raise RuntimeError("LLM 출력이 기대한 CSV 헤더 형식이 아닙니다. 출력 내용을 확인하세요.")

    # CSV 로드
    rows: list[dict] = []
    reader = csv.DictReader(lines)
    for r in reader:
        cat = (r.get("category") or "").strip()
        desc = (r.get("desc_ko") or "").strip()
        kws = (r.get("keywords_ko") or "").strip()
        if not cat or not desc:
            continue
        rows.append({"category": cat, "desc_ko": desc, "keywords_ko": kws})

    if not rows:
        raise RuntimeError("CSV 파싱 결과가 비어 있습니다. LLM 출력 형식을 확인하세요.")

    # 원본 df와 병합(순서 유지)
    enrich_map = {r["category"]: r for r in rows}
    df["desc_ko"] = df["category"].map(lambda c: enrich_map.get(str(c).strip(), {}).get("desc_ko", ""))
    df["keywords_ko"] = df["category"].map(lambda c: enrich_map.get(str(c).strip(), {}).get("keywords_ko", ""))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("완료:", out_path)

if __name__ == "__main__":
    main()