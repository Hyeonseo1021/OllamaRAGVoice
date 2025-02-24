import chromadb
import math
import numpy as np
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from numpy import clip
from sentence_transformers import SentenceTransformer

# ✅ 모델을 벡터 저장할 때와 동일하게 설정
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


# 🔹 ChromaDB 클라이언트 설정
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="documents")

# ✅ 1. 특정 질문에 대해서만 RAG 적용 여부 판단 
def should_apply_rag(query: str, top_k_final: int = 20, threshold: float = 0.7, scale: float = 30.0):
    # 쿼리 임베딩 생성
    query_embedding = embedding_model.encode(query).tolist()

    # 컬렉션에서 쿼리 실행
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10
    )

    retrieved_docs = results.get("documents", [[]])[0]
    retrieved_scores = results.get("distances", [[]])[0]  # 기본적으로 L2 distance 제공됨
    retrieved_metadata = results.get("metadatas", [[]])[0]

    all_docs = []
    print("\n🔍 검색된 문서 및 유사도 점수:")

    for doc, score, meta in zip(retrieved_docs, retrieved_scores, retrieved_metadata):
        # scaling factor 적용 후 L2 distance를 지수 감쇠 함수로 similarity로 변환
        similarity = math.exp(-score / scale)
        similarity = clip(similarity, 0, 1)  # 값이 0~1 범위를 벗어나지 않도록 보정

        print(f"📄 문서: {doc[:50]}... | 🔢 L2 distance: {score:.4f} | 🔥 변환된 유사도: {similarity:.4f}")

        if similarity < threshold:
            print(f"⚠️ 유사도가 {similarity:.4f}로 threshold({threshold})보다 낮아 필터링됨.")
            continue

        all_docs.append((doc, similarity, meta["filename"]))

    # 상위 유사도 문서만 선택
    all_docs = sorted(all_docs, key=lambda x: x[1], reverse=True)[:top_k_final]

    if not all_docs:
        print("❌ 유사한 문서 없음 → RAG 미적용")
        return False, ""

    combined_context = "\n\n".join(doc for doc, _, _ in all_docs)
    print(f"\n✅ RAG 적용됨! (사용된 문서 개수: {len(all_docs)})")
    return True, combined_context 
 

# ✅ 2. Google 검색 수행
def search_web(query: str, num_results=2):
    """Google Search를 사용하여 검색 결과 가져오기"""
    try:
        search_results = list(search(query, num_results=num_results, lang="ko"))
        return search_results
    except Exception as e:
        print(f"❌ Error during Google Search: {e}")
        return []

# ✅ 3. 웹페이지에서 주요 텍스트 크롤링
def extract_text_from_url(url: str):
    """웹페이지의 주요 내용을 크롤링하여 텍스트로 변환"""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")  # 주요 문서 내용 추출
        extracted_text = " ".join([p.get_text() for p in paragraphs])

        return extracted_text[:1000]  # LLM 입력을 고려하여 최대 길이 제한
    except Exception as e:
        print(f"❌ Error extracting text from {url}: {e}")
        return None
