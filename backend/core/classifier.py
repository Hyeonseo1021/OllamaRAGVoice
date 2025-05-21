from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate

# ✅ 최신 Ollama LLM 사용
llm = OllamaLLM(model="llama3")  # OpenAI 없이 로컬 모델 사용 가능

# ✅ 질문 분류 프롬프트 설정 (LLM이 직접 분류)
prompt_template = PromptTemplate(
    input_variables=["prompt"],
    template="""
    당신은 스마트팜 데이터를 관리하는 AI입니다.
    사용자의 질문을 분석하여 반드시 'DATA', 'RAG', 'BOTH', 'UNKNOWN' 중 하나만 반환하세요.

    ** 분류 기준 **
    - DATA: 현재 온도, 습도, 센서 데이터 등 **실시간 정보**와 특정 날짜, 농가명, 센서 데이터, 딸기 특성 등 **정확한 값**을 요청하는 경우
    - RAG: 최적 온도, 생육 조건, 작물 관리법, 스마트팜 운영 지식 등 **문서에서 찾을 수 있는 정보**를 요청하는 경우
    - BOTH: 현재 데이터를 기준 정보와 비교해야 하는 경우 (예: "지금 온도가 적당해?", "지금 CO2 농도는 기준에 맞아?")
    - UNKNOWN: 스마트팜과 관련 없는 일반적인 질문 또는 의미 없는 질문

    **예제 질문 및 분류 결과**  
    1. "현재 온도 몇 도야?" → DATA  
    2. "딸기 최적 온도는 얼마야?" → RAG  
    3. "지금 온도가 최적 범위야?" → BOTH  
    4. "지난주 농가별 평균 습도는?" → DATA  
    5. "딸기 병해충 관리 방법은?" → RAG  
    6. "현재 조도와 생육 단계별 최적 조도 비교해줘." → BOTH  

    **응답은 반드시 'DATA', 'RAG', 'BOTH', 'UNKNOWN' 중 하나만 반환하세요.  
    다른 단어나 설명 없이 정확한 분류명만 출력하세요.**
    
    사용자의 질문: "{prompt}"
    """
)

# ✅ LangChain 체인 방식 적용
question_classifier = prompt_template | llm

# ✅ 질문 분류 함수
def classify_question_type(prompt: str) -> str:
    response = question_classifier.invoke({"prompt": prompt}).strip().upper()
    
    # ✅ 응답이 유효한 분류인지 검증
    valid_categories = ["DATA", "RAG", "BOTH", "UNKNOWN"]
    return response if response in valid_categories else "UNKNOWN"

 
