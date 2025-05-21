import sys
import ollama
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_ollama import OllamaLLM  # ✅ LangChain Ollama 지원 LLM 추가
from langchain.prompts import PromptTemplate
from core.classifier import classify_question_type
from agents.data_tool import data_agent
from agents.rag_tool import rag_agent
from agents.both_tool import both_agent

# ✅ 1️⃣ Ollama LangChain LLM 설정 (stop_sequences 추가)
llm = OllamaLLM(
    model="llama3",
)

# ✅ 2️⃣ LangChain Tool 설정
tools = [data_agent, rag_agent, both_agent]

# ✅ 3️⃣ LangChain에서 사용할 PromptTemplate 생성 (필수 변수 포함)
prompt_template = PromptTemplate(
    input_variables=["prompt", "agent_scratchpad", "intermediate_steps", "context"],
    template="""
    Analyze the user's question and call the appropriate tools.

    ### User Input:
    {prompt}

    ### Provided Data:
    {context}

    ### Internal Scratchpad:
    {agent_scratchpad}

    ### Intermediate Steps:
    {intermediate_steps}

    ### Tool Selection Instructions:
    - Use **SmartFarmDataAgent** ONLY for sensor-related queries such as:
      - temperature, humidity, CO₂ levels, light intensity, nutrient concentration, real-time readings

    - Use **SmartFarmRAGAgent** for knowledge-based queries such as:
      - crop varieties (e.g., 딸기 품종), cultivation methods, pest and disease information, general farming techniques, definitions, terminology

    - Use **SmartFarmBOTHAgent** if the question asks to compare:
      - real-time data with standards or recommendations in documents
      - sensor data vs document data

    ### Execution Instructions:
    - **After "Thought:", you must include "Action:".**
    - **Every Action must include 'Action Input:', even if no action is required.**
    - **If no additional action is needed, use: "Action: Final Answer\nAction Input: [your final response here]".**
    - **If an action is needed, specify the appropriate tool and its input.**
    - **If the question type is 'BOTH', always use 'both_agent' instead of calling 'data_agent' and 'rag_agent' separately.**
    - **After executing the Agent, combine the results and generate the final answer.**

    - **Analyze the retrieved data and generate the most appropriate response.**
    - **Use the data from 'Provided Data' to construct an accurate and well-formed answer.**
    - **Ensure the response is based solely on the given data and does not contain inferred or additional information.**
    - **The final response should be in natural Korean.**

    **📢 AI's Response:**  
    - **If you have the final answer, output it using:**  
      "Final Answer: [your response here]"
    - **If more action is needed, use "Action:" followed by "Action Input:"**
    """
)

# ✅ 4️⃣ LangChain 최신 방식으로 Agent 생성 (최대 3회 반복 제한)
print("🚀 에이전트 초기화 중...")

try:
    agent_executor = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3,  
        allow_ask_for_clarification=False  # ✅ 추가 질문 없이 바로 중단
    )
    print("✅ 에이전트가 정상적으로 생성되었습니다.")
     
except Exception as e:
    print(f"❌ 에이전트 초기화 오류: {e}")
     

# ✅ 5️⃣ Agent를 활용한 질문 응답 함수
async def query_olama(prompt: str) -> str:
    print("🚀 query_olama 함수 실행됨")
    print(f"💬 사용자 질문 수신: {prompt}")
     
    data_source = classify_question_type(prompt)
    print(f"🔍 데이터 방식 결정: {data_source}")

    context = ""
     
    try:
        if data_source == "UNKNOWN":
            context = prompt

        else:
            print("⚡ LangChain Agent 실행 중...")
            result = agent_executor.invoke({"input": prompt}) # ✅ `invoke()` 사용
           
            if isinstance(result, dict) and "output" in result:
                context = result["output"]
            else:
                context = str(result)
            print(f"✅결과: {context[:200]}")  # 로그 출력 시 길이 제한
             

    except Exception as e:
        print(f"❌ Agent 실행 오류: {e}")
         
        return f"Error: {e}"

    if context:
        print(f"🔎 최종 컨텍스트 확인: {context[:200]}")
         

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
        print("💡 데이터 없음 → 일반 모델 응답")
         
        query_text = prompt  # 그냥 Ollama 모델 사용

    # 🧠 Ollama 모델 호출
    print("🧠 Ollama 모델 호출 중...")
     
    try:
        response = ollama.chat(model="gemma:7b", messages=[
            {"role": "system", "content": "당신은 정중한 한국어 AI 어시스턴트입니다. 항상 공식적인 한국어(존댓말)로 응답하십시오"},
            {"role": "user", "content": query_text}
        ])
        print(f"✅ Ollama 응답 완료: {response}")  # 로그 출력
         
    except Exception as e:
        print(f"❌ Ollama 호출 오류: {e}")
         
        return f"Error: {e}"

    if hasattr(response, "message") and hasattr(response.message, "content"):
        return response.message.content

    return "Error: Could not retrieve response from Ollama"
