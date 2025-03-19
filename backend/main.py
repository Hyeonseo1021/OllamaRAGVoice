from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import chromadb
from pydantic import BaseModel
from services.llm import query_olama
from services.file import process_uploaded_file
from services.today_data import get_today_data

app = FastAPI()

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ ChromaDB 설정
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection_documents = chroma_client.get_or_create_collection(name="documents")
collection_data_files = chroma_client.get_or_create_collection(name="data_files")

class ChatRequest(BaseModel):
    message: str
    
@app.post("/chat")
async def chat(request: ChatRequest):
    """📚 자동으로 질문 유형을 판단하여 응답"""
    
    print("💬 사용자 입력:", request.message)
    
    # ✅ 비동기 함수이므로 `await` 사용하여 호출
    response = await query_olama(request.message)
    
    print("✅ query_olama 실행 완료", flush=True)
    
    return {"response": response}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """📂 모든 파일 업로드 가능 + CSV/JSON은 별도 컬렉션에 저장"""
    
    file_ext = file.filename.split(".")[-1].lower()
    
    if file_ext in ["csv", "json"]:
        return await process_uploaded_file(file, collection_documents, collection_data_files)  # ✅ CSV/JSON → data_files 컬렉션
    else:
        return await process_uploaded_file(file, collection_documents, collection_data_files)  # ✅ 기타 파일 → documents 컬렉션


@app.get("/files")
async def get_uploaded_files():
    """📂 ChromaDB에서 일반 문서와 CSV/JSON 파일 목록을 조회"""
    try:
        # ✅ 일반 문서 컬렉션에서 파일 조회
        doc_results = collection_documents.get()
        data_results = collection_data_files.get()

        # ✅ 파일 목록 추출 함수
        def extract_filenames(results):
            if not results or "metadatas" not in results or not results["metadatas"]:
                return []
            return list(set(
                meta["filename"] for meta in results["metadatas"] if isinstance(meta, dict) and "filename" in meta
            ))

        doc_files = extract_filenames(doc_results)
        data_files = extract_filenames(data_results)

        print(f"📂 일반 문서 파일 목록: {doc_files}")
        print(f"📊 CSV/JSON 파일 목록: {data_files}")

        return {
            "documents": doc_files,  # ✅ 일반 문서 파일
            "data_files": data_files  # ✅ CSV/JSON 파일
        }
    except Exception as e:
        print(f"❌ 파일 목록 조회 오류: {e}")
        return {"error": "파일 목록을 가져오는 중 오류 발생"}

@app.delete("/delete/document")
async def delete_document(filename: str):
    """📂 ChromaDB에서 특정 문서 삭제"""
    try:
        # ✅ documents 컬렉션에서 삭제
        collection_documents.delete(where={"filename": filename})
        print(f"🗑 문서 삭제 완료: {filename}")
        return {"message": f"문서 '{filename}' 삭제 완료"}
    except Exception as e:
        print(f"❌ 문서 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=f"문서 삭제 오류: {e}")

@app.delete("/delete/file")
async def delete_file(filename: str):
    """📂 서버에서 파일 삭제"""
    try:
        collection_data_files.delete(where={"filename": filename})
        print(f"🗑 파일 삭제 완료: {filename}")
        return {"message": f"파일 '{filename}' 삭제 완료"}
        
    except Exception as e:
        print(f"❌ 파일 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 삭제 오류: {e}")

# ✅ API 엔드포인트 (오늘 날짜 데이터 반환)
@app.get("/today")
async def today_data_api():
    """ChromaDB에서 오늘 날짜 데이터 반환"""
    return get_today_data()
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)