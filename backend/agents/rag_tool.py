import chromadb
import numpy as np
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langchain.tools import Tool

# ✅ 1️⃣ ChromaDB 클라이언트 설정
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="documents")

# ✅ 2️⃣ 임베딩 모델 (문서 검색용)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ 3️⃣ ChromaDB에서 유사 문서 검색
def search_rag_data(query: str, top_k_final: int = 20, threshold: float = 0.75):
    """ ChromaDB에서 유사 문서 검색 후, cosine similarity 기반 필터링 """
    
    # ✅ 임베딩 생성 (정규화하여 cosine similarity에 적합하게)
    query_embedding = embedding_model.encode([query], normalize_embeddings=True)

    # ✅ 문서 검색 및 임베딩 포함 요청
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=50,
        include=["documents", "embeddings", "metadatas"]
    )

    retrieved_docs = results.get("documents", [[]])[0]
    retrieved_embeddings = results.get("embeddings", [[]])[0]
    retrieved_metadata = results.get("metadatas", [[]])[0]

    if not retrieved_docs:
        return "❌ 관련 문서를 찾을 수 없습니다."

    # ✅ cosine similarity 계산
    similarities = cosine_similarity([query_embedding[0]], retrieved_embeddings)[0]

    # ✅ 유사도 기준으로 정렬
    all_docs = list(zip(retrieved_docs, similarities, retrieved_metadata))
    all_docs = sorted(all_docs, key=lambda x: x[1], reverse=True)[:top_k_final]

    # ✅ 유사도 기준 필터링
    filtered_docs = [(doc, sim, meta["filename"]) for doc, sim, meta in all_docs if sim >= threshold]

    # ✅ 디버깅용 로그 출력 (옵션)
    for doc, sim, meta in filtered_docs:
        print(f"[유사도: {sim:.3f}] 문서: {meta}\n미리보기: {doc[:200]}\n")

    if not filtered_docs:
        return search_web(query)

    # ✅ 결과 구성
    formatted_docs = "\n\n".join([f"📄 문서: {meta}\n{doc}" for doc, _, meta in filtered_docs])
    context = f"📚 검색된 문서 데이터:\n{formatted_docs}"
    return context

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
        return f"🌍 [출처: {url}]\n" + extracted_text[:1000]  # 최대 길이 제한
    except Exception as e:
        return f"❌ {url} 크롤링 중 오류 발생: {e}"

# ✅ 6️⃣ LangChain 기반 RAG Agent 정의
rag_agent = Tool(
    name="SmartFarmRAGAgent",
    func=search_rag_data,
    description="작물 품종, 병해충, 재배 방법 등 농업 지식에 대한 문서를 검색합니다."
)