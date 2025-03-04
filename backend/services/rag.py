import chromadb
import math
import numpy as np
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from numpy import clip
from sentence_transformers import SentenceTransformer

# ✅ 모델을 벡터 저장할 때와 동일하게 설정
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 🔹 ChromaDB 클라이언트 설정
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="documents")

# ✅ 1. 특정 질문에 대해서만 RAG 적용 여부 판단 
def should_apply_rag(query: str, top_k_final: int = 20, threshold: float = 0.7):
    """ 특정 질문에 대해 RAG 적용 여부 판단 (L2 Distance 정규화 + 유사도 변환 개선) """

    # ✅ L2 Distance 기반으로 정규화 없이 임베딩 생성
    query_embedding = np.array(embedding_model.encode(query, normalize_embeddings=False))

    # ✅ ChromaDB에서 L2 Distance 기반 검색 수행
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=50  # ✅ 검색된 문서 개수 증가
    )

    retrieved_docs = results.get("documents", [[]])[0]
    retrieved_scores = results.get("distances", [[]])[0]  # ✅ L2 Distance 값 가져오기
    retrieved_metadata = results.get("metadatas", [[]])[0]

    if not retrieved_docs:
        print("❌ 검색된 문서가 없음 → RAG 미적용")
        return False, ""

    all_docs = []
    print("\n🔍 검색된 문서 및 L2 Distance 점수:")

    # ✅ L2 Distance 값 정규화: 최소/최대 거리 구해서 스케일링
    min_dist = min(retrieved_scores) if retrieved_scores else 0
    max_dist = max(retrieved_scores) if retrieved_scores else 1

    for doc, score, meta in zip(retrieved_docs, retrieved_scores, retrieved_metadata):
        # ✅ 유사도 변환 방법 개선
        similarity = 1 / (1 + score)  # ✅ L2 Distance 값이 낮을수록 높은 유사도 반환
        similarity = (max_dist - score) / (max_dist - min_dist + 1e-9)  # ✅ Min-Max 정규화 추가

        print(f"📄 문서: {doc[:50]}... | 🔢 L2 Distance: {score:.4f} | 🔥 변환된 유사도: {similarity:.4f}")

        all_docs.append((doc, similarity, meta["filename"]))

    # ✅ 유사도 높은 순서대로 정렬 후 top_k 개만 선택
    all_docs = sorted(all_docs, key=lambda x: x[1], reverse=True)[:top_k_final]

    # ✅ 상위 문서 중 threshold 이하인 문서만 필터링
    filtered_docs = [(doc, sim, meta) for doc, sim, meta in all_docs if sim >= threshold]

    if not filtered_docs:
        print("❌ 유사한 문서 없음 → RAG 미적용")
        return False, ""

    combined_context = "\n\n".join(doc for doc, _, _ in filtered_docs)
    print(f"\n✅ RAG 적용됨! (사용된 문서 개수: {len(filtered_docs)})")
    return True, combined_context
 

# ✅ 2. Google 검색 수행
def search_web(query: str, num_results=2):
    """Google Search를 사용하여 검색 결과 가져오기"""
    try:
        search_results = list(search(query, num_results=num_results, lang="ko"))
        return search_results
    
    except Exception as e:
        print(f"❌ Error during Google Search: {e}")
        return ["Error fetching search results."]

# ✅ 3. 웹페이지에서 주요 텍스트 크롤링
def extract_text_from_url(url: str):
    """웹페이지의 주요 내용을 크롤링하여 텍스트로 변환"""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")  # 주요 문서 내용 추출
        extracted_text = " ".join([p.get_text() for p in paragraphs])

        return extracted_text[:1000]  # LLM 입력을 고려하여 최대 길이 제한\
    
    except Exception as e:
        print(f"❌ Error extracting text from {url}: {e}")
        return None
