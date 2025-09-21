from PyPDF2 import PdfReader
from typing import List
from app.utils.logger import Logger
from app.utils.error_handler import ErrorHandler

class PDFHandler:
    def __init__(self):
        self.logger = Logger()
        self.error_handler = ErrorHandler(self.logger)
        self.logger.info("PDFHandler initialized.")

    def read(self, file_path: str) -> str:
        """
        Reads the text content from a PDF file.
        """
        self.logger.debug(f"Reading PDF file: {file_path}")
        try:
            reader = PdfReader(file_path)
            text = []
            for page in reader.pages:
                text.append(page.extract_text() or "")
            self.logger.info(f"Successfully read PDF: {file_path}")
            return "\n".join(text)
        except Exception as e:
            self.error_handler.handle(e, context=f"PDFHandler.read('{file_path}')")
            return ""

    def chunk(self, text: str, chunk_size: int = 2000) -> List[str]:
        """
        Splits the input text into chunks of specified size.
        """
        self.logger.debug(f"Chunking text into chunks of size {chunk_size}")
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]