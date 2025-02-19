from googlesearch import search
import requests
from bs4 import BeautifulSoup

# 🔹 RAG가 적용될 키워드 리스트
RAG_KEYWORDS = ["최신", "최근", "업데이트", "뉴스", "논문", "연구", "발표", "새로운", "스마트팜"]

# ✅ 1. 특정 질문에 대해서만 RAG 적용 여부 판단
def should_apply_rag(query: str) -> bool:
    """질문에 특정 키워드가 포함되었는지 확인하여 RAG 적용 여부 결정"""
    return any(keyword in query.lower() for keyword in RAG_KEYWORDS)

# ✅ 2. Google 검색 수행
def search_web(query: str, num_results=2):
    """Google Search를 사용하여 검색 결과 가져오기"""
    try:
        # `googlesearch.search`를 사용해 Google에서 검색
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

# ✅ 4. 검색 & 크롤링 통합
def retrieve_relevant_text(query: str):
    """검색 및 크롤링을 수행하여 LLM에 제공할 문맥을 구성"""
    print("🔍 RAG 적용: Google 검색 수행 중...")
    urls = search_web(query)
    if not urls:
        print("🔍 No URLs found for query.")
        return "현재 Google 검색에서 관련 정보를 찾을 수 없습니다. 질문을 조금 더 구체적으로 작성해 주세요."

    # 각 URL별로 크롤링된 결과 출력
    extracted_texts = []
    for url in urls:
        print(f"🔗 URL Found: {url}")
        text = extract_text_from_url(url)
        if text:
            print(f"✅ Extracted Text from {url}:\n{text[:200]}...\n")  # 앞부분 200자만 출력
            extracted_texts.append(text)
        else:
            print(f"❌ Failed to extract text from {url}.\n")
    
    # None 값 제거 후 하나의 문맥으로 결합
    context = "\n".join(extracted_texts)
    return context if context else "No relevant information found."
