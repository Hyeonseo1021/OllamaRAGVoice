import hashlib
import fitz  # PyMuPDF for PDF
import docx
import chardet  # 문자 인코딩 감지

def calculate_file_hash(file_content: bytes) -> str:
    """SHA256 해시값 생성"""
    return hashlib.sha256(file_content).hexdigest()

def extract_text_from_pdf(file_content: bytes) -> list:
    """📄 PDF에서 텍스트 추출 (참고문헌 이후 제외) → 페이지별 리스트 반환"""
    doc = fitz.open(stream=file_content, filetype="pdf")
    all_pages = []  # 페이지별 텍스트 저장
    ignore_keywords = ["참고 문헌", "참고문헌", "References", "REFERENCES", "참 고 문 헌"]

    exclude_text = False  # 참고문헌 감지 후 이후 페이지 무시

    for page_num, page in enumerate(doc):
        page_text = page.get_text("text").strip()

        # 🔹 참고문헌 감지 시 이후 텍스트 제외
        if any(keyword in page_text for keyword in ignore_keywords):
            print(f"🔍 참고문헌 감지됨! (페이지 {page_num + 1}) 이후 텍스트 제외")
            exclude_text = True
            break  # 이후 페이지 제외

        if not exclude_text and page_text:
            all_pages.append(page_text)  # ✅ 페이지별 리스트로 저장

    if not all_pages:
        return ["⚠️ PDF에서 텍스트를 제대로 추출하지 못했습니다. (OCR 필요 가능성 있음)"]

    return all_pages  # ✅ 이제 리스트 반환


def extract_text_from_docx(file_content: bytes) -> str:
    """📄 DOCX 파일에서 텍스트 추출 (목차 제외, 본문 유지)"""
    from io import BytesIO
    doc = docx.Document(BytesIO(file_content))
    text = []
    is_main_content = False  # 본문 시작 여부

    ignore_keywords = ["목차", "Table of Contents", "INDEX"]

    for para in doc.paragraphs:
        para_text = para.text.strip()

        # 🔹 목차 감지 → 본문 시작 지점 설정
        if any(keyword in para_text for keyword in ignore_keywords):
            print(f"🔍 목차 감지됨! 이후 본문만 유지")
            is_main_content = True
            continue  # 목차 자체는 저장 안 함

        # 🔹 본문 시작 이후 내용만 저장
        if is_main_content and para_text:
            text.append(para_text)

    extracted_text = "\n".join(text).strip()

    return extracted_text if extracted_text else "⚠️ DOCX 파일에서 본문을 찾을 수 없습니다."


def extract_text_from_txt(file_content: bytes) -> str:
    """📄 TXT 파일에서 텍스트 추출 (인코딩 자동 감지)"""
    encoding = chardet.detect(file_content)["encoding"] or "utf-8"
    try:
        text = file_content.decode(encoding)
        return text[:300] + "\n..." if len(text) > 300 else text  # 300자 미리보기
    except UnicodeDecodeError:
        return "❌ TXT 파일의 인코딩을 감지할 수 없습니다."

def extract_text_from_unknown(file_content: bytes) -> str:
    """📄 알 수 없는 파일에서 텍스트 일부만 추출"""
    return file_content[:1000].decode(errors="ignore")  # 최대 1000자 미리보기

def extract_text(file_name: str, file_content: bytes) -> str:
    """📂 파일 유형에 따라 적절한 방식으로 텍스트 추출"""
    file_ext = file_name.split(".")[-1].lower()

    if file_ext == "pdf":
        return extract_text_from_pdf(file_content)
    elif file_ext == "docx":
        return extract_text_from_docx(file_content)
    elif file_ext == "txt":
        return extract_text_from_txt(file_content)
    else:
        return extract_text_from_unknown(file_content)
