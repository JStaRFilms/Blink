"""
File reader module for Blink.

Handles reading text content from various file types including PDF, DOCX, and plain text files.
"""

import os
import base64
from io import BytesIO
from typing import Optional, Tuple


class FileReader:
    """
    Reads text content from various file types.
    """

    def __init__(self) -> None:
        """Initialize the file reader."""
        pass

    def _configure_tesseract(self) -> None:
        """
        Configure pytesseract's tesseract_cmd from environment or common Windows install paths.

        This helps avoid TesseractNotFoundError when the binary isn't on PATH.
        """
        try:
            import pytesseract  # type: ignore
        except ImportError:
            # Handled by callers which re-import and report a helpful error
            return

        # 1) If user provided explicit env var, prefer it
        env_cmd = os.environ.get('TESSERACT_CMD')
        if env_cmd and os.path.exists(env_cmd):
            try:
                pytesseract.pytesseract.tesseract_cmd = env_cmd
                return
            except Exception:
                pass

        # 2) If current cmd is a valid existing path, keep it
        try:
            current_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
        except Exception:
            current_cmd = None

        if current_cmd and os.path.isabs(current_cmd) and os.path.exists(current_cmd):
            return

        # 3) Try common Windows install locations
        for cmd in [
            r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
        ]:
            try:
                if os.path.exists(cmd):
                    pytesseract.pytesseract.tesseract_cmd = cmd
                    return
            except Exception:
                continue

    def is_image_file(self, file_path: str) -> bool:
        """
        Checks if a file is an image based on its extension.
        
        Args:
            file_path (str): Path to the file to check.
            
        Returns:
            bool: True if the file is an image, False otherwise.
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        return ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif']

    def get_image_data(self, image_path: str) -> Tuple[str, str]:
        """
        Gets image data as base64 string and MIME type.
        
        Args:
            image_path (str): Path to the image file.
            
        Returns:
            Tuple[str, str]: Base64 encoded image data and MIME type.
            
        Raises:
            ValueError: If the file is not a valid image.
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"File not found: {image_path}")

        if not os.access(image_path, os.R_OK):
            raise PermissionError(f"Cannot read file: {image_path}")

        if not self.is_image_file(image_path):
            raise ValueError(f"File is not an image: {image_path}")

        # Get MIME type based on file extension
        _, ext = os.path.splitext(image_path)
        ext = ext.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')

        # Read image and convert to base64
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                return base64_data, mime_type
        except Exception as e:
            raise ValueError(f"Could not read image file {image_path}: {e}")

    def get_pil_image_data(self, image) -> Tuple[str, str]:
        """
        Gets PIL Image data as base64 string and MIME type.
        
        Args:
            image: PIL.Image.Image instance.
            
        Returns:
            Tuple[str, str]: Base64 encoded image data and MIME type.
            
        Raises:
            ValueError: If the image cannot be processed.
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("Pillow is required for image processing. Install it with: pip install Pillow")

        if not isinstance(image, Image.Image):
            raise ValueError("Provided object is not a PIL Image")

        # Determine MIME type from image format
        format_to_mime = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'BMP': 'image/bmp',
            'TIFF': 'image/tiff',
            'WEBP': 'image/webp',
            'GIF': 'image/gif'
        }
        mime_type = format_to_mime.get(image.format, 'image/png')

        # Convert image to bytes and then to base64
        try:
            buffer = BytesIO()
            image.save(buffer, format=image.format or 'PNG')
            image_data = buffer.getvalue()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return base64_data, mime_type
        except Exception as e:
            raise ValueError(f"Could not process image: {e}")

    def read_text_from_file(self, file_path: str) -> str:
        """
        Reads text content from a file based on its extension.

        Args:
            file_path (str): Path to the file to read.

        Returns:
            str: The extracted text content.

        Raises:
            ValueError: If the file type is not supported.
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"Cannot read file: {file_path}")

        # Get file extension (case insensitive)
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.log']:
            return self._read_plain_text_file(file_path)
        elif ext == '.pdf':
            return self._read_pdf_file(file_path)
        elif ext in ['.docx', '.doc']:
            return self._read_docx_file(file_path)
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif']:
            return self._read_image_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Supported types: .txt, .md, .py, .js, .html, .css, .json, .xml, .csv, .log, .pdf, .docx, .doc, .png, .jpg, .jpeg, .bmp, .tiff, .tif, .webp, .gif")

    def _read_plain_text_file(self, file_path: str) -> str:
        """
        Reads a plain text file.

        Args:
            file_path (str): Path to the text file.

        Returns:
            str: The file content.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Could not read text file {file_path}: {e}")

    def _read_pdf_file(self, file_path: str) -> str:
        """
        Reads text content from a PDF file.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            str: The extracted text content.
        """
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError("PyPDF2 is required to read PDF files. Install it with: pip install PyPDF2")

        try:
            reader = PdfReader(file_path)
            text_content = []

            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_content.append(text)

            return '\n\n'.join(text_content)

        except Exception as e:
            raise ValueError(f"Could not read PDF file {file_path}: {e}")

    def _read_image_file(self, file_path: str) -> str:
        """
        OCR text content from an image file.

        Args:
            file_path (str): Path to the image file.

        Returns:
            str: The OCR-extracted text content.
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("Pillow is required for image OCR. Install it with: pip install Pillow")
        try:
            import pytesseract
        except ImportError:
            raise ImportError("pytesseract is required for image OCR. Install it with: pip install pytesseract")

        # Attempt to auto-configure tesseract path
        self._configure_tesseract()

        try:
            with Image.open(file_path) as img:
                text = pytesseract.image_to_string(img)
                return text or ""
        except pytesseract.TesseractNotFoundError as e:
            raise ValueError("Tesseract OCR engine not found. Please install Tesseract and ensure it's on PATH or set TESSERACT_CMD to the tesseract.exe path.")
        except Exception as e:
            raise ValueError(f"Could not OCR image file {file_path}: {e}")

    def read_text_from_image(self, image) -> str:
        """
        OCR text from a PIL Image object.

        Args:
            image: PIL.Image.Image instance.

        Returns:
            str: OCR-extracted text content.
        """
        try:
            import pytesseract
        except ImportError:
            raise ImportError("pytesseract is required for image OCR. Install it with: pip install pytesseract")

        # Attempt to auto-configure tesseract path
        self._configure_tesseract()

        try:
            text = pytesseract.image_to_string(image)
            return text or ""
        except pytesseract.TesseractNotFoundError:
            raise ValueError("Tesseract OCR engine not found. Please install Tesseract and ensure it's on PATH or set TESSERACT_CMD to the tesseract.exe path.")
        except Exception as e:
            raise ValueError(f"Could not OCR clipboard image: {e}")

    def _read_docx_file(self, file_path: str) -> str:
        """
        Reads text content from a DOCX file.

        Args:
            file_path (str): Path to the DOCX file.

        Returns:
            str: The extracted text content.
        """
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is required to read DOCX files. Install it with: pip install python-docx")

        try:
            doc = Document(file_path)
            text_content = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)

            return '\n'.join(text_content)

        except Exception as e:
            raise ValueError(f"Could not read DOCX file {file_path}: {e}")