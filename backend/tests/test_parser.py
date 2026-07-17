import pytest

from app.parser import (
    clean_text,
    extract_resume_text,
    extract_text_from_docx,
    validate_resume_content,
)


def test_clean_text_removes_extra_spaces() -> None:
    raw_text = "Python     Developer\n\n\nFastAPI\tSQL"

    result = clean_text(raw_text)

    assert "Python Developer" in result
    assert "FastAPI SQL" in result
    assert "\n\n\n" not in result


def test_extract_docx_text(
    simple_docx_bytes: bytes,
) -> None:
    result = extract_text_from_docx(
        simple_docx_bytes
    )

    assert "ANSHUMAN PATTANAYAK" in result
    assert "Python" in result
    assert "FastAPI" in result


def test_extract_resume_text_from_docx(
    simple_docx_bytes: bytes,
) -> None:
    result = extract_resume_text(
        filename="resume.docx",
        file_bytes=simple_docx_bytes,
    )

    assert result
    assert "Machine Learning" in result


def test_reject_unsupported_file_type() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported file type",
    ):
        extract_resume_text(
            filename="resume.txt",
            file_bytes=b"sample resume",
        )


def test_reject_empty_file() -> None:
    with pytest.raises(
        ValueError,
        match="uploaded file is empty",
    ):
        extract_resume_text(
            filename="resume.pdf",
            file_bytes=b"",
        )


def test_rejects_invalid_pdf_signature() -> None:
    with pytest.raises(ValueError, match="valid PDF"):
        validate_resume_content(".pdf", b"not-a-pdf")


def test_rejects_invalid_docx_container() -> None:
    with pytest.raises(ValueError, match="valid DOCX"):
        validate_resume_content(".docx", b"not-a-zip-file")


def test_accepts_valid_docx_container(
    simple_docx_bytes: bytes,
) -> None:
    validate_resume_content(".docx", simple_docx_bytes)
