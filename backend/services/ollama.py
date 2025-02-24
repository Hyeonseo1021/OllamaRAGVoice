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
            당신은 전문적인 AI 비서이며, 사용자의 질문에 대해 항상 공손한 존댓말을 사용해야 합니다.
            또한, 응답은 기본적으로 한국어로 작성되지만, 특정 기술 용어나 논문 개념은 영어로 유지할 수 있습니다.
            응답의 전체적인 흐름은 자연스럽고 일관되도록 유지해야 합니다.
            다음 컨텍스트를 기반으로 사용자 질문에 답변하세요.

            ### Context:
            {context}

            ### User Question:
            {prompt}

            ### Assistant Response:
            """

        else:
            print("❌ 문서 유사도 낮음 → 웹 검색 수행")
            context = search_web(prompt) or "No relevant documents found."

            # ✅ 웹 검색을 활용한 답변 프롬프트
            query_text = f"""
            당신은 AI 비서이며, 사용자의 질문에 대해 항상 공손한 존댓말을 사용해야 합니다.
            또한, 응답은 기본적으로 한국어로 작성되어야 하지만, 특정 기술 용어나 논문 개념은 영어로 유지할 수 있습니다.

            다음은 웹 검색을 통해 얻은 정보입니다. 정보를 바탕으로 신뢰할 수 있는 답변을 제공하세요.

            ### Web Search Results:
            {context}

            ### User Question:
            {prompt}

            ### Assistant Response:
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
