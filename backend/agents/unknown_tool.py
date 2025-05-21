from langchain.tools import Tool

# ✅ Unknown 질문 처리 함수 (LLM 호출 없이 그대로 context 전달)
def handle_unknown_question(prompt: str) -> str:
    """ 스마트팜 도구와 관련 없는 질문 → 그냥 context로 넘김 """
    return f"💬 [일반 대화용 질문]\n{prompt}"

# ✅ LangChain 기반 Unknown Tool 정의
unknown_tool = Tool(
    name="SmartFarmUnknown",
    func=handle_unknown_question,
    description="스마트팜 질문이 아닌 경우 일반 대화용 컨텍스트로 넘깁니다."
)
