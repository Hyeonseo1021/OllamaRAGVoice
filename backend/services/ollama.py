import ollama
from services.rag import retrieve_relevant_text, should_apply_rag  # 🔥 변경된 동적 RAG 함수

# ✅ 특정 질문에서만 RAG를 적용하는 로직
async def query_olama(prompt: str) -> str:
    """사용자 입력을 기반으로 필요한 경우에만 RAG를 적용하여 Olama 모델 호출"""

    # 🔹 특정 키워드가 포함된 경우에만 RAG 적용
    if should_apply_rag(prompt):
        print("🔍 RAG 적용: 실시간 웹 검색 수행 중...")
        context = retrieve_relevant_text(prompt)  # 🔥 검색 수행
        context = context[:500]
        query_text = f"Context: {context}\nUser: {prompt}"
    else:
        print("💡 RAG 미적용: 일반 Olama 모델 실행")
        query_text = prompt  # 일반 질문은 검색 없이 Olama 실행

    # 🧠 Olama 모델 호출
    response = ollama.chat(model="mistral", messages=[
        {"role": "system", "content": "You are a knowledgeable assistant."},
        {"role": "user", "content": query_text}
    ])

    # ✅ 응답이 `Message` 객체이므로 `.message.content` 사용
    if hasattr(response, "message") and hasattr(response.message, "content"):
        return response.message.content

    return "Error: Could not retrieve response from Olama"
