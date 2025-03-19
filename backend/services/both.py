from services.manage_data import data_agent  # 센서 데이터 Agent
from services.rag import rag_agent  # 문서 검색 Agent
from langchain.tools import Tool

# ✅ 1️⃣ BOTH 유형 분석 함수
def query_both_data(prompt: str) -> str:
    """ 센서 데이터 + 문서 검색을 동시에 수행하여 결과 비교 """
    
    # ✅ 현재 센서 데이터 가져오기
    sensor_data = data_agent.run(prompt)
    
    # ✅ 문서에서 최적 기준 검색
    rag_data = rag_agent.run(prompt)
    
    if not sensor_data and not rag_data:
        return "❌ 관련 데이터를 찾을 수 없습니다."
    
    # ✅ 결과 비교 및 분석
    response = "📊 [BOTH 분석 결과]\n"
    response += f"🌡️ 현재 센서 데이터:\n{sensor_data}\n\n"
    response += f"📄 문서 검색 결과:\n{rag_data}\n\n"
    
    response += "📌 분석: 현재 센서 데이터가 문서에서 제공하는 최적 기준과 비교될 수 있습니다. 필요하면 추가 분석 요청을 해주세요."
    
    return response

# ✅ 2️⃣ LangChain 기반 BOTH Agent 정의
both_agent = Tool(
    name="SmartFarmBOTHAgent",
    func=query_both_data,
    description="스마트팜 센서 데이터와 문서를 동시에 검색하여 최적 상태인지 분석합니다."
)