import os
import tempfile
from pathlib import Path
from typing import BinaryIO, List, Optional

import PyPDF2
from docx import Document as DocxDocument


class DocumentService:
    """Service for extracting text from various document formats"""
    
    @staticmethod
    def extract_text_from_pdf(file: BinaryIO) -> str:
        """Extract text content from a PDF file"""
        text = ""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting text from PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file: BinaryIO) -> str:
        """Extract text content from a DOCX file"""
        try:
            # Create a temporary file to save the uploaded content
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                temp_file.write(file.read())
                temp_path = temp_file.name
            
            # Process the document
            doc = DocxDocument(temp_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            
            # Clean up the temp file
            os.unlink(temp_path)
            
            return "\n".join(full_text)
        except Exception as e:
            raise ValueError(f"Error extracting text from DOCX: {str(e)}")
    
    @staticmethod
    def extract_text_from_txt(file: BinaryIO) -> str:
        """Extract text content from a TXT file"""
        try:
            content = file.read()
            if isinstance(content, bytes):
                return content.decode('utf-8')
            return content
        except Exception as e:
            raise ValueError(f"Error extracting text from TXT: {str(e)}")
    
    @classmethod
    def extract_text_from_file(cls, file: BinaryIO, filename: str) -> str:
        """Extract text from a file based on its extension"""
        file_extension = Path(filename).suffix.lower()
        
        if file_extension == '.pdf':
            return cls.extract_text_from_pdf(file)
        elif file_extension == '.docx':
            return cls.extract_text_from_docx(file)
        elif file_extension == '.txt':
            return cls.extract_text_from_txt(file)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}") 