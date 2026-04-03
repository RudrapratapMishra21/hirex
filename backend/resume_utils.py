from PyPDF2 import PdfReader
import docx

def extract_text(path):

    text = ""

    if path.endswith(".pdf"):

        reader = PdfReader(path)

        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()

    elif path.endswith(".docx"):

        doc = docx.Document(path)

        for p in doc.paragraphs:
            text += p.text

    return text