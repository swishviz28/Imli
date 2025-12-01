import fitz  # PyMuPDF

def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF and returns it as a string.
    """
    doc = fitz.open(file_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text
