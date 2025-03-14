import sys
import os

# 현재 디렉토리를 Python 패스에 추가
sys.path.append(os.getcwd())

# 이제 정상적으로 import 가능
from services.llm import classify_question_type

print(classify_question_type("농가 100의 딸기 엽폭 수"))  # 예상: DATA
print(classify_question_type("딸기 최적 온도는 몇 도야?"))  # 예상: RAG
print(classify_question_type("지금 온도가 적당한지 알려줘"))  # 예상: BOTH
print(classify_question_type("농가 2의 CO2 농도랑 적정 수준 비교해줘"))  # 예상: BOTH
print(classify_question_type("딸기 병해충 방제법은?"))  # 예상: RAG
