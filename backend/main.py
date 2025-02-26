from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import chromadb
import hashlib
import fitz  # ✅ PDF 텍스트 추출 라이브러리 (PyMuPDF)
import re
from pydantic import BaseModel
from services.ollama import query_olama
from langchain.text_splitter import CharacterTextSplitter
from sentence_transformers import SentenceTransformer
from langchain.vectorstores import Chroma

# ✅ 무료 임베딩 모델 로드
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

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
collection = chroma_client.get_or_create_collection(name="documents")

class ChatRequest(BaseModel):
    message: str
    use_rag: bool  # ✅ RAG 버튼 여부 추가

@app.post("/chat")
async def chat(request: ChatRequest):
    """📚 사용자가 RAG 버튼을 눌렀을 때만 RAG를 적용, 그렇지 않으면 일반 모델 응답"""

    print("💬 사용자 입력:", request.message)
    print(f"🟢 RAG 사용 여부: {request.use_rag}")

    if request.use_rag:
        # ✅ RAG 버튼을 눌렀을 경우 → 문서 검색(RAG) 또는 웹 검색 수행
        response = await query_olama(request.message, use_rag=True)
    else:
        # ✅ RAG 버튼을 누르지 않았을 경우 → 일반 LLM 모델 응답
        print("💡 일반 모드: RAG 없이 기본 모델 응답 반환")
        response = await query_olama(request.message, use_rag=False)

    return {"response": response}

# 해시값 저장소 (ChromaDB를 사용해도 되고, 별도 DB를 활용 가능)
uploaded_hashes = set()

def calculate_file_hash(file_content: bytes) -> str:
    """SHA256 해시값 생성"""
    return hashlib.sha256(file_content).hexdigest()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """📂 PDF 파일만 업로드 가능 + 중복 업로드 방지"""
    file_ext = file.filename.split(".")[-1].lower()

    if file_ext != "pdf":
        raise HTTPException(status_code=400, detail="❌ 지원되지 않는 파일 형식입니다. PDF 파일만 업로드 가능합니다.")

    original_filename = file.filename  
    file_content = await file.read()

    # 🔹 파일 해시값 계산
    file_hash = calculate_file_hash(file_content)

    # 🔹 중복 업로드 체크
    if file_hash in uploaded_hashes:
        raise HTTPException(status_code=400, detail="⚠️ 이미 업로드된 파일입니다.")

    # 🔹 중복이 아니라면 해시값 저장
    uploaded_hashes.add(file_hash)

    # 🔹 PDF에서 텍스트 추출
    text = extract_text_from_pdf(file_content)

    if not text.strip():
        print(f"❌ {original_filename}에서 텍스트를 추출할 수 없습니다.")
        return {"error": f"❌ {original_filename}에서 텍스트를 추출할 수 없습니다."}

    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_text(text)

    print(f"📂 {original_filename}에서 {len(docs)}개의 문서 조각 생성됨.")

    # ✅ 모델에서 올바른 벡터 차원 확인
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
            metadatas=[{"filename": original_filename, "hash": file_hash, "text": doc}],  # 🔹 해시값도 저장!
            documents=[doc]
        )

    print(f"✅ {original_filename}이(가) ChromaDB에 저장됨. (총 {len(docs)}개)")

    return {"message": f"✅ {original_filename} 업로드 완료!"}

@app.get("/files")
async def get_uploaded_files():
    """📂 업로드한 PDF 목록 조회 (파일명만 반환)"""
    try:
        results = collection.get()

        if not results or "metadatas" not in results or not results["metadatas"]:
            print("❌ ChromaDB에서 파일 목록을 찾을 수 없습니다.")
            return {"files": []}

        # ✅ 파일명만 추출 (중복 제거)
        file_names = list(set(
            meta["filename"] for meta in results["metadatas"] if isinstance(meta, dict) and "filename" in meta
        ))

        print(f"📂 업로드된 파일 목록: {file_names}")

        return {"files": file_names}
    except Exception as e:
        print(f"❌ 파일 목록 조회 오류: {e}")
        return {"error": "파일 목록을 가져오는 중 오류 발생"}

def extract_text_from_pdf(file_content):
    """📄 PDF에서 텍스트 추출 후 정제"""
    doc = fitz.open(stream=file_content, filetype="pdf")
    text = ""

    for page_num, page in enumerate(doc):
        page_text = page.get_text("text").strip()

        # ✅ 참고문헌 필터링 (다양한 표현 포함)
        ignore_keywords = ["참고 문헌", "참고문헌", "References", "REFERENCES", "참 고 문 헌"]
        if any(keyword in page_text for keyword in ignore_keywords):
            print(f"🔍 참고문헌 섹션 제외됨 (페이지 {page_num + 1})")
            continue

        print(f"📄 [페이지 {page_num + 1}] 길이: {len(page_text)}")  # ✅ 페이지별 길이 출력
        print(f"📄 내용 미리보기: {page_text[:300]}")  # ✅ 첫 300자 미리보기
        text += page_text + "\n"

    if not text.strip():
        print("❌ PDF에서 텍스트를 추출할 수 없음 (OCR 필요할 수도 있음)")
        return ""

    print(f"✅ 최종 추출된 텍스트 길이: {len(text)}")  # ✅ 전체 텍스트 길이 확인
    return text


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
