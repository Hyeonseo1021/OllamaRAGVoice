import chromadb
import re
import pandas as pd
from sentence_transformers import SentenceTransformer

# ✅ ChromaDB 클라이언트 설정
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="data_files")  # CSV/JSON 데이터 저장 컬렉션

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ 날짜 패턴 (예: "2025-03-04", "2월 15일", "어제", "오늘", "최근")
DATE_PATTERN = r"(\d{4}-\d{2}-\d{2}|\d{1,2}월 \d{1,2}일|어제|오늘|최근)"

# ✅ 업로드된 데이터셋의 컬럼명을 저장할 변수 (초기에는 비어 있음)
DATASET_COLUMNS = set()

def update_dataset_columns(new_columns):
    """📌 새로운 데이터셋이 추가될 때 컬럼명을 자동 업데이트"""
    global DATASET_COLUMNS
    DATASET_COLUMNS.update(new_columns)

def search_growth_data_in_chromadb(prompt: str, question_type: str) -> list:
    """
    📌 ChromaDB에서 사용자의 질문 유형을 기반으로 생육 데이터를 검색하여 반환
    """
    try:
        # ✅ 사용자 질문을 벡터로 변환 후 검색
        query_embedding = embedding_model.encode(prompt).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],  # ✅ 임베딩된 질문을 사용
            n_results=100  # ✅ 최상위 50개 결과 가져오기
        )

        retrieved_docs = results.get("documents", [[]])[0]

        # ✅ 질문 유형이 CSV 관련이라면 숫자가 포함된 데이터만 반환 (정확한 데이터 검색)
        if question_type == "DATA":
            retrieved_docs = [doc for doc in retrieved_docs if any(char.isdigit() for char in doc)]

        return retrieved_docs if retrieved_docs else []

    except Exception as e:
        print(f"❌ ChromaDB 데이터 검색 오류: {e}")
        return []
    
def filter_growth_data(docs: list, prompt: str) -> str:
    """
    📌 검색된 생육 데이터에서 사용자 질문과 관련된 정보만 필터링 (컬럼명 자동 감지)
    """

    # ✅ 날짜 필터링 (날짜 관련 질문이면 적용)
    date_match = re.search(DATE_PATTERN, prompt)
    if date_match:
        date_query = date_match.group(0)
        docs = [doc for doc in docs if date_query in doc]

    # ✅ "농가명 XX"이 포함된 경우 해당 농가 데이터만 필터링
    farm_match = re.search(r"농가명\s*(\d+)", prompt)
    if farm_match:
        farm_id = farm_match.group(1)  # 예: "58"
        docs = [doc for doc in docs if f"농가명: {farm_id}" in doc]

    # ✅ 컬럼명 자동 필터링 (업로드된 데이터셋에서 필드명 추출)
    relevant_docs = []
    for doc in docs:
        for column in DATASET_COLUMNS:  # ✅ 기존 하드코딩된 키워드 대신 데이터셋에서 자동 감지된 컬럼 사용
            if column in prompt and column in doc:
                relevant_docs.append(doc)
                break  # 중복 저장 방지

    # ✅ 최종 데이터 정리 (필터링된 데이터 반환)
    if relevant_docs:
        return "\n".join(relevant_docs)  # 📌 모든 검색된 데이터 반환
    elif docs:
        return "\n".join(docs)  # 📌 농가 필터링된 데이터 반환
    else:
        return "❌ 제공된 데이터에는 해당 농가에 대한 정보가 포함되지 않습니다."
