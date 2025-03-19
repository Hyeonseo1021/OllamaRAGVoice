import chromadb
import pandas as pd
import datetime
from sentence_transformers import SentenceTransformer
from typing import List, Dict

# ✅ ChromaDB 클라이언트 설정
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="data_files")  # ChromaDB 컬렉션

# ✅ 날짜 컬럼 후보 리스트 (자동 감지)
POSSIBLE_DATE_COLUMNS = ["date", "날짜", "조사일자", "측정일", "기록일", "등록일", "실험일"]

# ✅ 오늘 날짜 가져오기
def get_today_date() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")

# ✅ 날짜 컬럼 자동 감지 함수
def detect_date_column(df: pd.DataFrame) -> str:
    """데이터프레임에서 날짜 형식의 컬럼을 자동으로 감지"""
    for col in df.columns:
        if any(keyword in col.lower() for keyword in POSSIBLE_DATE_COLUMNS):  # ✅ 컬럼명 매칭
            return col

    # ✅ 데이터 유형이 날짜 형식인 컬럼 찾기
    for col in df.columns:
        try:
            pd.to_datetime(df[col])
            return col  # 변환 가능하면 날짜 컬럼으로 판단
        except Exception:
            continue

    return None  # 날짜 컬럼 없음

# ✅ ChromaDB에서 오늘 날짜 데이터 검색
def get_today_data() -> List[str]:
    try:
        # ✅ ChromaDB에서 전체 데이터 가져오기
        raw_data = collection.get()["documents"]

        if not raw_data:
            return []  # ✅ 데이터가 없으면 빈 리스트 반환

        # ✅ 데이터를 JSON 형태로 변환
        processed_data = [dict(entry.split(": ") for entry in doc.split(", ")) for doc in raw_data]
        df = pd.DataFrame(processed_data)

        # ✅ 날짜 컬럼 자동 감지
        date_column = detect_date_column(df)

        if not date_column:
            return ["❌ 날짜 컬럼을 찾을 수 없습니다."]

        # ✅ 날짜 형식 변환 및 필터링
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")  # 변환 실패 시 NaT 처리
        df = df.dropna(subset=[date_column])  # NaT 값 제거

        today_date = pd.to_datetime(get_today_date())
        today_data = df[df[date_column].dt.date == today_date.date()]

        # ✅ 데이터를 LLM이 이해할 수 있는 형식으로 변환
        retrieved_docs = [", ".join(f"{k}: {v}" for k, v in row.items()) for row in today_data.to_dict(orient="records")]

        return retrieved_docs if retrieved_docs else []  # ✅ LLM이 이해할 수 있도록 변환

    except Exception as e:
        return [f"❌ 오류 발생: {str(e)}"]
