import pandas as pd
import json
from fastapi import UploadFile, HTTPException
from .extraction import extract_text, calculate_file_hash
from langchain.text_splitter import CharacterTextSplitter
from sentence_transformers import SentenceTransformer

uploaded_hashes = set()  # 해시 저장소
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")  # ✅ 무료 임베딩 모델 로드

async def process_uploaded_file(file: UploadFile, collection_documents, collection_data_files):
    """📂 파일 업로드 후 임베딩 생성 및 ChromaDB 저장 (CSV/JSON 분리)"""
    original_filename = file.filename
    file_content = await file.read()

    # 🔹 파일 해시값 계산
    file_hash = calculate_file_hash(file_content)

    # 🔹 중복 업로드 방지
    if file_hash in uploaded_hashes:
        raise HTTPException(status_code=400, detail="⚠️ 이미 업로드된 파일입니다.")

    uploaded_hashes.add(file_hash)  # 해시 저장

    # 🔹 파일 확장자 확인
    file_ext = original_filename.split(".")[-1].lower()
    
    if file_ext in ["csv", "json", "xlsx"]:
        docs = process_data_file(file_content, file_ext)
        collection = collection_data_files  # ✅ CSV/JSON은 별도 컬렉션에 저장
    else:
        pages = extract_text(original_filename, file_content)
        if not pages or (isinstance(pages, list) and not any(pages)):
            return {"error": f"❌ {original_filename}에서 텍스트를 추출할 수 없습니다."}

        # 🔹 1000자 단위로 분할
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = [chunk for page in pages for chunk in text_splitter.split_text(page)]
        collection = collection_documents  # ✅ 일반 문서는 기존 컬렉션 사용

    print(f"📂 {original_filename}에서 {len(docs)}개의 문서 조각 생성됨.")

    # ✅ 임베딩 및 ChromaDB 저장
    embedding_dim = embedding_model.get_sentence_embedding_dimension()

    for i, doc in enumerate(docs):
        try:
            vector = embedding_model.encode(doc).tolist()
            if len(vector) != embedding_dim:
                print(f"❌ {original_filename}-{i} 벡터 크기 오류! 예상 {embedding_dim}, 실제 {len(vector)}")
                continue
        except Exception as e:
            print(f"❌ 임베딩 생성 오류: {e}")
            continue

        collection.add(
            ids=[f"{original_filename}-{i}"],
            embeddings=[vector],
            metadatas=[{"filename": original_filename, "hash": file_hash, "text": doc}],
            documents=[doc]
        )

    print(f"✅ {original_filename}이(가) ChromaDB에 저장됨. (총 {len(docs)}개)")

    return {"message": f"✅ {original_filename} 업로드 및 저장 완료!"}



def process_data_file(file_content: bytes, file_ext: str):
    """📊 CSV/JSON 파일을 분석하여 ChromaDB에 저장할 문서 생성"""
    docs = []
    
    if file_ext == "csv":
        df = pd.read_csv(pd.io.common.BytesIO(file_content))
    elif file_ext == "xlsx":
        df = pd.read_excel(pd.io.BytesIO(file_content))
    elif file_ext == "json":
        data = json.loads(file_content.decode("utf-8"))
        df = pd.DataFrame(data)

    # ✅ 데이터 변환 (컬럼명을 포함하여 자연어로 변환)
    for _, row in df.iterrows():
        doc_text = ", ".join([f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])])
        docs.append(doc_text)

    return docs
