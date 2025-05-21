import chromadb
import numpy as np
import re
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from langchain.embeddings import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
from langchain.tools import Tool

# ✅ 1️⃣ ChromaDB 클라이언트 설정
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="documents")

# ✅ 2️⃣ 임베딩 모델 (문서 검색용)
embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True}
)

# ✅ 3️⃣ ChromaDB에서 유사 문서 검색
def search_rag_data(query: str, top_k_final: int = 20, threshold: float = 0.5, min_docs: int = 3):
    """ 🔍 개선된 RAG 문서 검색: cosine 유사도 기반 + 보조 필터 + 최소 확보 """

    # ✅ 1. cosine similarity 기반 임베딩 생성
    query_embedding = embedding_model.embed_query(query)  # 이미 정규화됨
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k_final * 2,  # 후보 넉넉히 확보
        include=["documents", "metadatas", "distances"]
    )

    retrieved_docs = results.get("documents", [[]])[0]
    retrieved_scores = results.get("distances", [[]])[0]
    retrieved_metadata = results.get("metadatas", [[]])[0]

    if not retrieved_docs:
        print("❌ No documents retrieved.")
        return "❌ 관련 문서를 찾을 수 없습니다."

    # ✅ 2. cosine 유사도 계산 (score는 distance가 아니라 similarity)
    all_docs = []
    for doc, dist, meta in zip(retrieved_docs, retrieved_scores, retrieved_metadata):
        similarity = 1 - dist  # cosine distance → similarity
        all_docs.append((doc, similarity, meta["filename"]))

    # ✅ 3. threshold 필터 및 유사도 정렬
    sorted_docs = sorted(all_docs, key=lambda x: x[1], reverse=True)
    filtered_docs = [(doc, sim, meta) for doc, sim, meta in sorted_docs if sim >= threshold]

    # ✅ 4. 키워드 보조 필터 (보완용)
    keywords = [kw for kw in re.findall(r"\b\w{2,}\b", query)]
    seen_meta = set(meta for _, _, meta in filtered_docs)

    for doc, sim, meta in sorted_docs:
        if len(filtered_docs) >= top_k_final:
            break
        if meta not in seen_meta and any(kw.lower() in doc.lower() for kw in keywords):
            print(f"📌 키워드 기반 보조 포함: {meta}")
            filtered_docs.append((doc, sim, meta))
            seen_meta.add(meta)

    # ✅ 5. 최소 확보 보장
    for doc, sim, meta in sorted_docs:
        if len(filtered_docs) >= min_docs:
            break
        if meta not in seen_meta:
            filtered_docs.append((doc, sim, meta))
            seen_meta.add(meta)

    if not filtered_docs:
        return search_web(query)

    # ✅ 6. 출력 정리
    formatted_docs = "\n\n".join([f"📄 문서: {meta}\n{doc}" for doc, _, meta in filtered_docs])
    return f"📚 검색된 문서 데이터:\n{formatted_docs}"

# ✅ 4️⃣ Google 검색 실행
def search_web(query: str, num_results=2):
    """ Google 검색을 수행하여 관련 웹 페이지 링크 가져오기 """
    try:
        search_results = list(search(query, num_results=num_results, lang="ko"))
        if search_results:
            return extract_text_from_url(search_results[0])  # ✅ 첫 번째 웹페이지 크롤링 후 반환
        return "❌ 웹 검색 결과가 없습니다."
    except Exception as e:
        return f"❌ Google 검색 중 오류 발생: {e}"

# ✅ 5️⃣ 웹페이지 크롤링 기능
def extract_text_from_url(url: str):
    """ 웹페이지 주요 텍스트 크롤링 """
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        extracted_text = " ".join([p.get_text() for p in paragraphs])
        return f"🌍 [출처: {url}]\n" + extracted_text[:5000]  
    except Exception as e:
        return f"❌ {url} 크롤링 중 오류 발생: {e}"

# ✅ 6️⃣ LangChain 기반 RAG Agent 정의
rag_tool = Tool(
    name="SmartFarmRAG",
    func=search_rag_data,
    description="작물 품종, 병해충, 재배 방법 등 농업 지식에 대한 문서를 검색합니다."
)