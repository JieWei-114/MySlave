import io
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Centralized file upload limit
FILE_UPLOAD_MAX_CHARS = settings.FILE_UPLOAD_MAX_CHARS


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extract text content from various file types.
    """
    filename_lower = filename.lower()

    logger.info(f'Extracting content from {filename} ({len(file_content)} bytes)')

    try:
        if filename_lower.endswith('.pdf'):
            content = extract_from_pdf(file_content)
        elif filename_lower.endswith('.docx'):
            content = extract_from_docx(file_content)
        elif filename_lower.endswith('.doc'):
            raise ValueError(
                'Legacy .doc format not supported. '
                'Please convert the file to .docx format using Microsoft Word or LibreOffice'
            )
        else:
            content = extract_as_text(file_content)

        # Truncate using centralized limit
        content = truncate_content(content)

        logger.info(f'Successfully extracted {len(content)} chars from {filename}')
        return content

    except Exception as e:
        logger.error(f'Failed to extract content from {filename}: {e}')
        raise ValueError(f'Failed to extract content from {filename}: {str(e)}')


def extract_from_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file.
    """
    try:
        import PyPDF2

        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text_parts = []
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f'--- Page {page_num + 1} ---\n{text}')
            except Exception as e:
                logger.warning(f'Failed to extract page {page_num + 1}: {e}')
                continue

        if not text_parts:
            raise ValueError('No text content found in PDF')

        return '\n\n'.join(text_parts)

    except ImportError:
        raise ValueError('PDF extraction not available. Install PyPDF2: pip install PyPDF2')


def extract_from_docx(file_content: bytes) -> str:
    """
    Extract text from .docx file.
    """
    try:
        from docx import Document

        docx_file = io.BytesIO(file_content)
        doc = Document(docx_file)

        text_parts = []

        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                text_parts.append(text)

        # Extract tables
        for table in doc.tables:
            for row in table.rows:
                row_text = ' | '.join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    text_parts.append(row_text)

        if not text_parts:
            raise ValueError('No text content found in Word document')

        return '\n\n'.join(text_parts)

    except ImportError:
        raise ValueError(
            'Word extraction not available. Install python-docx: pip install python-docx'
        )


def extract_as_text(file_content: bytes) -> str:
    """
    Extract content as plain text with encoding detection.
    """
    # Try common encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    for encoding in encodings:
        try:
            text = file_content.decode(encoding)
            if text.strip():
                return text.strip()
        except (UnicodeDecodeError, AttributeError):
            continue

    raise ValueError('Unable to decode file content as text')


def truncate_content(content: str, max_chars: int = None) -> str:
    """
    Truncate content to maximum length.
    """
    if max_chars is None:
        max_chars = FILE_UPLOAD_MAX_CHARS

    if len(content) <= max_chars:
        return content

    truncated = content[:max_chars]
    return f'{truncated}\n\n[Content truncated to {max_chars} chars - original length: {len(content)} chars]'
