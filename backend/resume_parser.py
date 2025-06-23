import PyPDF2

def extract_text_from_pdf(filepath):
    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
    except Exception as e:
        return f"❌ Error reading PDF: {str(e)}"