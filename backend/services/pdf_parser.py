import pdfplumber
import io

def extract_text_from_pdf(file_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages_text = [text for page in pdf.pages if (text := page.extract_text())]

    return "\n".join(pages_text).strip()