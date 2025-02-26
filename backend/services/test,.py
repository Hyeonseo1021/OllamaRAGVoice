from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 현재 사용 중인 임베딩 모델 로드
embedding_model = SentenceTransformer("jhgan/ko-sbert-nli")

# 테스트 문장
text1 = "오늘 날씨 어때?"
text2 = "기차 시간표 알려줘"

embedding1 = embedding_model.encode(text1)
embedding2 = embedding_model.encode(text2)

# 코사인 유사도 계산
similarity = cosine_similarity([embedding1], [embedding2])[0][0]
print(f"유사도: {similarity:.4f}")
