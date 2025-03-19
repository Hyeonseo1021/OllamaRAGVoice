import chromadb
import numpy as np
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from langchain.tools import Tool

# ✅ 1️⃣ ChromaDB 클라이언트 설정
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="documents")

# ✅ 2️⃣ 임베딩 모델 (문서 검색용)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ 3️⃣ ChromaDB에서 유사 문서 검색
def search_rag_data(query: str, top_k_final: int = 20, threshold: float = 0.5):
    """ ChromaDB에서 유사 문서 검색 후, 점수 기반 필터링 """
    query_embedding = embedding_model.encode(query, normalize_embeddings=False)
    results = collection.query(query_embeddings=[query_embedding.tolist()], n_results=50)

    retrieved_docs = results.get("documents", [[]])[0]
    retrieved_scores = results.get("distances", [[]])[0]  # L2 Distance 값
    retrieved_metadata = results.get("metadatas", [[]])[0]

    if not retrieved_docs:
        return "❌ 관련 문서를 찾을 수 없습니다."

    all_docs = []
    for doc, score, meta in zip(retrieved_docs, retrieved_scores, retrieved_metadata):
        similarity = 1 / (1 + score)  # 유사도로 변환
        all_docs.append((doc, similarity, meta["filename"]))

    # ✅ 유사도 높은 순 정렬 후 상위 문서만 반환
    all_docs = sorted(all_docs, key=lambda x: x[1], reverse=True)[:top_k_final]
    filtered_docs = [(doc, sim, meta) for doc, sim, meta in all_docs if sim >= threshold]

    if not filtered_docs:
        # ✅ 유사도가 낮으면 웹 검색 실행
        return search_web(query)

    # ✅ 최종 문서 검색 결과를 `context`로 변환
    formatted_docs = "\n\n".join([f"📄 문서: {meta}\n{doc}" for doc, _, meta in filtered_docs])
    context =  f"📚 검색된 문서 데이터:\n{formatted_docs}"
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
    description="스마트팜 운영 관련 문서를 검색하고, 필요하면 웹에서 정보를 가져옵니다."
)