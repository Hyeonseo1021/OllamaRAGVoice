import chromadb
import re
import pandas as pd
from sentence_transformers import SentenceTransformer

# ✅ ChromaDB 클라이언트 설정
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="data_files")  # CSV/JSON 데이터 저장 컬렉션

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_matching_columns(prompt: str, column_names: list) -> dict:
    """
    📌 사용자 질문에서 데이터의 열(column)과 값(value)을 추출하여 매칭
    🔥 "농가 2" 같은 표현이 있으면, "농가"는 열, "2"는 값으로 설정
    🔥 값이 없는 경우(None)는 해당 열이 존재하는지만 확인
    """
    matched_columns = {}

    # ✅ 정규식을 이용하여 "농가 2" 같은 형태에서 숫자와 텍스트를 분리
    word_number_pattern = re.findall(r"([가-힣A-Za-z]+)\s*([\d]+)", prompt)  # (단어, 숫자) 매칭

    for word, number in word_number_pattern:
        for col in column_names:
            if word in col:  # 🔥 질문 속 키워드가 데이터 열과 매칭되면 추가
                matched_columns[col] = number  # 🔥 숫자를 값(value)으로 설정

    # ✅ 숫자가 없는 일반 키워드 처리
    for col in column_names:
        for word in prompt.split():
            if word in col and col not in matched_columns:  # 🔥 기존에 매칭되지 않은 경우만 추가
                matched_columns[col] = None

    return matched_columns

def convert_to_dict(raw_data):
    """
    📌 문자열 데이터를 JSON(dict) 형태로 변환
    """
    processed_data = []
    for entry in raw_data:
        data_dict = {}
        for field in entry.split(", "):  # 각 필드 분리
            key_value = field.split(": ")
            if len(key_value) == 2:
                key, value = key_value
                data_dict[key.strip()] = value.strip()
        processed_data.append(data_dict)
    return processed_data

def filter_growth_data(raw_data: list, prompt: str) -> list:
    """
    📌 사용자 질문에서 매칭된 열과 값으로 데이터 필터링
    🔥 특정 열(예: "농가 2")이 있다면, 해당 열을 먼저 필터링하여 검색 범위 축소
    🔥 값이 없는 경우(None)는 해당 열이 존재하는지만 확인
    """
    try:
        if not raw_data:
            return []

        # ✅ 문자열 데이터를 JSON(dict) 형태로 변환
        processed_data = convert_to_dict(raw_data)
        df = pd.DataFrame(processed_data)  # DataFrame 변환
        column_names = df.columns.tolist()

        # ✅ 사용자 질문에서 데이터와 매칭되는 열과 값 찾기
        matching_filters = extract_matching_columns(prompt, column_names)
        print(f"🔍 필터링 조건: {matching_filters}")

        # ✅ 1️⃣ 특정한 값(예: "농가 2")이 있는 경우, 먼저 필터링하여 데이터 축소
        for col, value in matching_filters.items():
            if col in df.columns and value is not None:
                df = df[df[col].astype(str) == value]  # 🔥 값이 있는 경우 정확한 매칭

        # ✅ 2️⃣ 값이 None인 경우, 해당 열이 존재하는지만 확인
        for col, value in matching_filters.items():
            if col in df.columns and value is None:
                df = df[df[col].notna()]

        # ✅ 필터링 결과가 없는 경우 유사한 데이터 추천
        if df.empty:
            print("⚠ 정확한 데이터가 없음 → 유사한 데이터 추천")
            return processed_data  # 원본 데이터를 반환하여 다른 조건으로 재검색 가능

        return df.to_dict(orient="records")

    except Exception as e:
        print(f"❌ 데이터 필터링 오류: {e}")
        return []

def search_growth_data_in_chromadb(prompt: str) -> list:
    """
    📌 ChromaDB에서 데이터를 검색하기 전에 filter_growth_data를 먼저 실행하여,
       필터링된 데이터가 충분하면 그대로 반환, 부족하면 추가 검색 수행
    """
    try:
        # ✅ ChromaDB에서 전체 데이터 가져오기
        raw_data = collection.get()["documents"]  # 전체 문서 리스트 가져오기
        
        # ✅ 먼저 필터링 실행 (질문과 연관된 데이터만 추출)
        filtered_data = filter_growth_data(raw_data, prompt)

        # ✅ 필터링된 데이터가 충분하면 바로 반환
        if filtered_data and len(filtered_data) < 1000:  
            print(f"✅ 필터링된 데이터 개수: {len(filtered_data)} → 직접 반환")
            return filtered_data
        
        print("⚠ 필터링된 데이터가 부족하여 ChromaDB 검색 수행")

        # ✅ ChromaDB에서 검색 수행 (필터링된 데이터가 너무 적을 때)
        query_embedding = embedding_model.encode(prompt).tolist()
        
        max_results = 500  # 초기 검색 개수
        MAX_LIMIT = 10_000  # 최대 검색 개수
        retrieved_docs = []

        while max_results <= MAX_LIMIT:
            print(f"🔍 {max_results}개 검색 시도 중...")

            results = collection.query(
                query_embeddings=[query_embedding],  
                n_results=max_results
            )

            retrieved_docs = results.get("documents", [[]])[0]
            print(f"📌 현재 검색된 데이터 개수: {len(retrieved_docs)}")

            if retrieved_docs:
                return retrieved_docs  # 🔥 필터링 후 검색된 데이터 반환

            print("❌ 검색된 데이터가 없음 → 검색 개수 증가 시도")
            max_results *= 2  # ✅ 검색 개수 증가

        print("⚠ 최대 검색 개수에 도달했지만 원하는 데이터를 찾지 못했습니다.")
        return []

    except Exception as e:
        print(f"❌ ChromaDB 데이터 검색 오류: {e}")
        return []
