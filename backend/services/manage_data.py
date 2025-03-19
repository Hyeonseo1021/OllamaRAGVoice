import chromadb
import re
import pandas as pd
from langchain.tools import Tool
from sentence_transformers import SentenceTransformer
from services.today_data import get_today_data  # ✅ 오늘 날짜 데이터 가져오는 함수 불러오기

# ✅ 1️⃣ ChromaDB 설정
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="data_files")  # 센서 데이터 저장 컬렉션

# ✅ 2️⃣ 임베딩 모델 (문서 검색용)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ 3️⃣ 사용자 질문에서 필요한 데이터 필터링
def extract_matching_columns(prompt: str, column_names: list) -> dict:
    matched_columns = {}
    word_number_pattern = re.findall(r"([가-힣A-Za-z]+)\s*([\d]+)", prompt)

    for word, number in word_number_pattern:
        for col in column_names:
            if word in col:
                matched_columns[col] = number

    for col in column_names:
        if col in prompt and col not in matched_columns:
            matched_columns[col] = None

    return matched_columns

# ✅ 4️⃣ 데이터 필터링 기능
def filter_growth_data(raw_data: list, prompt: str) -> list:
    if not raw_data:
        return []

    processed_data = [dict(entry.split(": ") for entry in doc.split(", ")) for doc in raw_data]
    df = pd.DataFrame(processed_data)
    column_names = df.columns.tolist()

    matching_filters = extract_matching_columns(prompt, column_names)
    print(f"🔍 필터링 조건: {matching_filters}")

    for col, value in matching_filters.items():
        if col in df.columns and value is not None:
            df = df[df[col].astype(str) == value]

    for col, value in matching_filters.items():
        if col in df.columns and value is None:
            df = df[df[col].notna()]

    if df.empty:
        return processed_data

    return df.to_dict(orient="records")

# ✅ 5️⃣ ChromaDB에서 데이터 검색
def search_growth_data_in_chromadb(prompt: str) -> list:
    try:
        # ✅ "오늘", "현재", "지금"이 포함된 질문이면 today_data.py 사용
        if any(keyword in prompt for keyword in ["오늘", "현재", "지금"]):
            print("📅 오늘 날짜 데이터 검색 실행")
            return get_today_data()
        
        raw_data = collection.get()["documents"]

        # ✅ 일반적인 데이터 검색
        filtered_data = filter_growth_data(raw_data, prompt)

        if filtered_data and len(filtered_data) < 1000:
            return filtered_data

        query_embedding = embedding_model.encode(prompt).tolist()
        results = collection.query(query_embeddings=[query_embedding], n_results=500)
        retrieved_docs = results.get("documents", [[]])[0]

        return retrieved_docs if retrieved_docs else []
    except Exception as e:
        print(f"❌ ChromaDB 데이터 검색 오류: {e}")
        return []

# ✅ 6️⃣ LangChain 기반 Data Agent 생성
def query_smartfarm_data(prompt: str) -> str:
    results = search_growth_data_in_chromadb(prompt)
    context = f"📊 검색된 데이터:\n{results}" if results else "❌ 관련 데이터를 찾을 수 없습니다."
    return context
data_agent = Tool(
    name="SmartFarmDataAgent",
    func=query_smartfarm_data,
    description="스마트팜 센서 데이터 조회 및 분석"
)
