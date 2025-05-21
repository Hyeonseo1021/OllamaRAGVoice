import sys
import ollama
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_ollama import OllamaLLM  # ✅ LangChain Ollama 지원 LLM 추가
from langchain.prompts import PromptTemplate
from langchain.agents.agent import AgentExecutor
from agents.data_tool import data_tool
from agents.rag_tool import rag_tool
from agents.both_tool import both_tool
from agents.unknown_tool import unknown_tool

llm_context = OllamaLLM(model="mistral")  
llm_response = OllamaLLM(model="gemma:7b")

# ✅ 2️⃣ LangChain Tool 설정
tools = [data_tool, rag_tool, both_tool, unknown_tool]

context_agent = initialize_agent(
    tools=tools,
    llm=llm_context,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5,
    allow_ask_for_clarification=False
)

# ✅ 3️⃣ LangChain에서 사용할 PromptTemplate 생성 (필수 변수 포함)
prompt_template = PromptTemplate(
    input_variables=["prompt", "agent_scratchpad", "intermediate_steps", "context"],
    template="""
        You are a structured reasoning agent with access to specific tools.
        Your job is to choose exactly ONE appropriate tool and provide the result in a strict format.

        ---

        ### 🧾 User Query:
        {prompt}

        ### 📚 Retrieved Context:
        {context}

        ### 🧠 Internal Scratchpad:
        {agent_scratchpad}

        ### ⛓️ Intermediate Steps:
        {intermediate_steps}

        ---

        ### 🔧 Available Tools:

        - 🧠 **SmartFarmRAG**  
        → 사용 목적: 작물 품종, 병해충, 재배법, 농업 지식 질문  
        → 예시: “딸기 품종 알려줘”, “고추 병해충은 뭐가 있어?”

        - 🌡 **SmartFarmData**  
        → 사용 목적: 센서 기반 실시간 데이터(온도, 습도, CO₂, 조도, 토양 수분 등)  
        → **질문에 '현재', '오늘', '지금', 센서 이름'이 명시되어 있어야 함**

        - 🧪 **SmartFarmBOTH**  
        → 사용 목적: 센서 데이터와 문서 정보를 비교하거나 통합 질문 시  
        → 예시: “지금 온도가 토마토 생장에 적절해?”

        - ❓ **SmartFarmUnknown**  
        → 사용 목적: 농업/센서와 관련 없는 일반 대화, 또는 분류 불가능한 질문  
        → 예시: “GPT는 뇌가 있나요?”, “내일 뭐 할까?”

        ---

        ### 🛑 Strict Usage Rules:

        - ✅ 반드시 하나의 도구만 선택
        - 🚫 "딸기 품종", "고추 병해충" 같은 일반 농업 질문에는 **절대 SmartFarmData 사용 금지**
        - 🚫 문서 검색 실패 시 SmartFarmData를 fallback으로 사용하지 말 것
        - 🚫 도구 호출 실패 시 다른 도구 시도 금지
        - 🚫 도구 호출 없이 답하지 말 것 (Final Answer는 context 기반일 때만)

        ---

        ### ✅ Output Format:

        반드시 아래 형식으로 응답하십시오. 순서와 태그는 **절대 변경 금지**:

        Thought: [내부 판단 설명]  
        Action: [SmartFarmRAG, SmartFarmData, SmartFarmBOTH, SmartFarmUnknown, or Final Answer]  
        Action Input: [도구 입력 or 최종 한국어 응답]

        ---

        ### ✅ Valid Example:

        Thought: The user is asking for strawberry varieties, which is a knowledge query.  
        Action: SmartFarmRAG  
        Action Input: 딸기 품종

        ---

        🚨 **이 형식을 위반할 경우 시스템은 동작하지 않습니다.**
        """
)

# ✅ response_agent Prompt
response_prompt = PromptTemplate(
    input_variables=["context", "prompt"],
    template="""
    항상 정중하고 정확한 한국어로 응답하십시오.
    제공된 문맥(context)을 기반으로만 응답하고, 그 외 정보는 절대 포함하지 마십시오.

    ### 문맥:
    {context}

    ### 사용자 질문:
    {prompt}

    ### 응답:
    """
)

# ✅ 응답 생성 전용 Agent
response_agent = response_prompt | llm_response

# ✅ 두 Agent를 연결하는 함수
async def query_dual_agent(prompt: str) -> str:
    try:
        # Step 1: context 수집
        context_result = context_agent.invoke({
            "input": prompt,
        })
        context = context_result["output"] if isinstance(context_result, dict) and "output" in context_result else str(context_result)
        print(f"📄문맥 (앞부분): {context[:500]}")
    except Exception as e:
        return f"❌ context_agent 오류: {e}"

    try:
        # Step 2: 응답 생성
        response_text = response_agent.invoke({
            "context": context,
            "prompt": prompt
        })
        return response_text
    except Exception as e:
        return f"❌ response_agent 오류: {e}"