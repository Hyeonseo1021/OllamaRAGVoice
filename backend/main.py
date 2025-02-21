from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.ollama import query_olama
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings  # 또는 다른 임베딩 모델 사용
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import shutil

app = FastAPI()

# ✅ CORS 설정 추가 (프론트엔드 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# ✅ 요청 모델
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    """사용자의 메시지를 받아 Olama 모델을 실행"""
    response = await query_olama(request.message)
    return {"response": response}

# ✅ PDF 파일 업로드 및 저장
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """PDF 파일을 업로드하고 내용을 ChromaDB에 저장"""
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # 파일 저장
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # PDF 로드 및 텍스트 추출
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()
    
    # 문서 분할
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    
    # 임베딩 저장
    vector_store.add_documents(texts)
    vector_store.persist()
    
    return {"message": "PDF 업로드 및 저장 완료", "filename": file.filename}


# ✅ 문서 검색 API
class SearchRequest(BaseModel):
    query: str

@app.post("/search")
async def search_documents(request: SearchRequest):
    """사용자의 검색어와 관련된 문서를 ChromaDB에서 검색"""
    results = vector_store.similarity_search(request.query, k=5)
    return {"results": [result.page_content for result in results]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
