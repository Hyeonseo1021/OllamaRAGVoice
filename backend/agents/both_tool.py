from agents.data_tool import data_tool  # 센서 데이터 Agent
from agents.rag_tool import rag_tool  # 문서 검색 Agent
from langchain.tools import Tool

# ✅ 1️⃣ BOTH 유형 분석 함수
def query_both_data(prompt: str) -> str:
    """ 센서 데이터 + 문서 검색을 동시에 수행하여 결과 비교 """
    
    # ✅ 현재 센서 데이터 가져오기
    sensor_data = data_tool.run(prompt)
    
    # ✅ 문서에서 최적 기준 검색
    rag_data = rag_tool.run(prompt)
    
    if not sensor_data and not rag_data:
        return "❌ 관련 데이터를 찾을 수 없습니다."
    
    # ✅ 결과 비교 및 분석
    response = "📊 [BOTH 분석 결과]\n"
    response += f"🌡️ 현재 센서 데이터:\n{sensor_data}\n\n"
    response += f"📄 문서 검색 결과:\n{rag_data}\n\n"
    
    return response

# ✅ 2️⃣ LangChain 기반 BOTH Agent 정의
both_tool = Tool(
    name="SmartFarmBOTH",
    func=query_both_data,
    description="스마트팜 센서 데이터와 문서를 동시에 검색하여 최적 상태인지 분석합니다."
)