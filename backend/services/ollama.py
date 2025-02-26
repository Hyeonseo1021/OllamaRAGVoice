import ollama
from services.rag import should_apply_rag, search_web

async def query_olama(prompt: str, use_rag: bool = False, threshold: float = 0.7) -> str:
    """📚 RAG 버튼 적용 시 문서 검색 후 유사도 판단하여 ChromaDB or 웹 검색 사용"""

    if use_rag:
        # 🔍 ChromaDB 문서 검색 수행
        use_rag, context = should_apply_rag(prompt, top_k_final=20, threshold=threshold)

        if use_rag:
            print("✅ RAG 적용: ChromaDB 검색 결과 활용")
            print(f"🔍 사용된 컨텍스트 내용: {context[:500]}...")  # ✅ 컨텍스트 확인용 출력

            # ✅ ChromaDB 문서를 활용한 답변 프롬프트
            query_text = f"""
            당신은 **일관되고 정중한 한국어 답변을 제공하는 전문가 AI 어시스턴트**입니다.
            항상 공식적인 한국어(존댓말)로 응답하십시오.
            기술적 또는 과학적 용어에 일반적으로 사용되는 한국어 번역이 있다면 해당 한국어 용어를 사용하십시오.
            적절한 한국어 번역이 없을 경우 영어 용어를 그대로 사용하십시오.
            한국어와 영어가 모두 일반적으로 사용되는 경우, 둘 다 제공하십시오.

            **제공된 문맥을 기반으로 한국어로만 응답을 생성하십시오.** 번역된 응답을 추가로 제공하지 마십시오.
            문맥에 관련 정보가 포함되지 않았다면, 다음과 같이 응답하십시오: "충분한 정보가 없습니다."

            ### Context:
            {context}

            ### User Question:
            {prompt}

            ### Assistant Response (in Korean):
            """

        else:
            print("❌ 문서 유사도 낮음 → 웹 검색 수행")
            context = search_web(prompt) or "No relevant documents found."

            # ✅ 웹 검색을 활용한 답변 프롬프트 (더 보수적인 답변)
            query_text = f"""
            You are an AI assistant that provides **formal and polite responses in Korean**.
            Your answers should always be in **Korean (존댓말)**.
            If a technical or scientific term has a commonly used Korean translation, use the Korean term.
            If there is no suitable Korean translation, use the English term.
            If both Korean and English are commonly used, provide both (e.g., "Brain-Derived Neurotrophic Factor (BDNF), 뇌유래 신경영양인자").

            The following information is from a web search. Based on this, provide a reliable response.

            ### Web Search Results:
            {context}

            ### User Question:
            {prompt}

            ### Assistant Response (in Korean):
            """

    else:
        print("💡 RAG 버튼 OFF → 일반 모델 응답")
        query_text = prompt  # 그냥 Olama 모델 사용

    # 🧠 Olama 모델 호출
    response = ollama.chat(model="mistral", messages=[
        {"role": "system", "content": "You are a professional AI assistant providing polite and consistent answers in Korean."},
        {"role": "user", "content": query_text}
    ])

    # ✅ 응답이 `Message` 객체이므로 `.message.content` 사용
    if hasattr(response, "message") and hasattr(response.message, "content"):
        return response.message.content

    return "Error: Could not retrieve response from Olama"
