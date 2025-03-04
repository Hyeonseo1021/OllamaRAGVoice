import ollama
from services.rag import should_apply_rag, search_web
from services.manage_data import search_growth_data_in_chromadb, filter_growth_data

# ✅ GPT 기반 질문 분석 함수
def classify_question_type(prompt: str) -> str:
    """
    📌 GPT-4 (또는 LLaMA) 모델을 이용하여 질문을 분석하고 
    'DATA', 'RAG', 'BOTH' 중 하나를 반환
    """
    system_prompt = """
    당신은 스마트팜 데이터를 관리하는 AI입니다.
    사용자의 질문을 분석하여 다음 카테고리 중 하나로 분류하십시오:
    
    - DATA: 현재 온도, 습도, 센서 데이터 등 **실시간 정보**와 특정 날짜, 농가명, 센서 데이터, 딸기 특성 등 **정확한 값**을 요청하는 경우
    - RAG: 최적 온도, 작물 관리법, 스마트팜 운영 지식 등 **문서에서 찾을 수 있는 정보**를 요청하는 경우
    - BOTH: 실시간 데이터와 문서 정보가 **둘 다 필요한 경우** (예: "지금 온도가 적당해?")
    
    예시:
    1. "현재 온도 몇 도야?" → DATA
    2. "딸기 최적 온도는 얼마야?" → RAG
    3. "지금 온도가 최적 범위야?" → BOTH
    4. "지난주 농가별 평균 습도는?" -> DATA
    5. "딸기 병해충 관리 방법은? -> RAG
    6. "현재 조도와 생육 단계별 최적 조도 비교해줘." -> BOTH

    사용자의 질문을 위 규칙에 따라 분류하세요. **응답은 반드시 'DATA', 'RAG', 'BOTH' 중 하나로만 하십시오.**
    """

    response = ollama.chat(model="llama3", messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ])

    # ✅ "DATA", "RAG", "BOTH" 중 하나를 반환하도록 설정
    if hasattr(response, "message") and hasattr(response.message, "content"):
        response_text = response.message.content.strip().upper()
        if response_text in ["DATA", "RAG", "BOTH"]:
            print(response_text)
            return response_text

    return "UNKNOWN"  # 예외 처리

async def query_olama(prompt: str, use_rag: bool = False, threshold: float = 0.7) -> str:

    data_source = classify_question_type(prompt)
    print(f"🔍 데이터 방식 결정: {data_source}")

    context = ""

        # ✅ DATA 검색 (실시간 데이터 필요)
    if data_source in ["DATA", "BOTH"]:
        raw_data = search_growth_data_in_chromadb(prompt, data_source)  # 🔹 최신 센서 데이터 가져오기
        data_context = filter_growth_data(raw_data, prompt)
        
        if data_context:
            context += f"\n\n### 생육 데이터:\n{data_context}"
        
    # ✅ RAG 문서에서 검색 (지식 기반 정보 필요)
    if data_source in ["RAG", "BOTH"]:
        if use_rag:
            use_rag, rag_context = should_apply_rag(prompt, top_k_final=20, threshold=threshold)

            if use_rag and rag_context:
                print("✅ RAG 적용: ChromaDB 검색 결과 활용")
                print(f"🔍 사용된 컨텍스트 내용: {context[:500]}...")  # ✅ 컨텍스트 확인용 출력
                context += f"\n\n### RAG 문서 데이터:\n{rag_context}"


            else:
                print("❌ 문서 유사도 낮음 → 웹 검색 수행")
                web_context = search_web(prompt) or "No relevant documents found."
                context += f"\n\n### 웹 검색 결과:\n{web_context}"          
    
    if context:
        query_text = f"""
        항상 공식적인 한국어로 응답하십시오.
        제공된 문맥(context) 기반으로만 응답하십시오. 문맥에 포함되지 않은 정보를 추가하거나 일반 지식을 추가하지 마십시오.
        ***문맥에서 직접적으로 제공되지 않은 정보는 포함하지 마십시오.***
        문맥에 관련 정보가 부족하거나 포함되지 않았다면, 다음과 같이 응답하십시오:
        ***제공된 문서에서 해당 정보를 찾을 수 없습니다.***

        {context}
        ### 사용자 질문
        {prompt}
        ### AI 어시스턴트의 응답 (in Korean):
        """

    else:
        print("💡 RAG 버튼 OFF 또는 데이터 없음 → 일반 모델 응답")
        query_text = prompt  # 그냥 Olama 모델 사용

    # 🧠 Olama 모델 호출
    response = ollama.chat(model="gemma:7b", messages=[
        {"role": "system", "content": "당신은 정중한 한국어  AI 어시스턴트입니다. 항상 공식적인 한국어(존댓말)로 응답하십시오"},
        {"role": "user", "content": query_text}
    ])

    # ✅ 응답이 `Message` 객체이므로 `.message.content` 사용
    if hasattr(response, "message") and hasattr(response.message, "content"):
        return response.message.content

    return "Error: Could not retrieve response from Olama"
