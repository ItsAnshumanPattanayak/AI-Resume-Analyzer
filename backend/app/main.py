from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware

from app.ats import calculate_ats_score
from app.extractor import extract_resume_information
from app.parser import SUPPORTED_EXTENSIONS, extract_resume_text
from app.semantic import (
    calculate_chunk_matches,
    calculate_semantic_similarity,
)
from app.similarity import (
    calculate_combined_similarity,
    calculate_tfidf_similarity,
)
from app.skills import compare_resume_and_job_skills


app = FastAPI(
    title="AI Resume Analyzer API",
    description=(
        "Backend API for parsing resumes, calculating ATS scores, "
        "matching job descriptions, and generating recommendations."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MAXIMUM_FILE_SIZE = 5 * 1024 * 1024


async def read_and_validate_resume(
    file: UploadFile,
) -> tuple[bytes, str]:
    """
    Validate an uploaded resume and extract its text.

    Returns:
        A tuple containing the original file bytes
        and extracted resume text.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not have a filename.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail={
                "message": "Unsupported resume format.",
                "supported_formats": sorted(
                    SUPPORTED_EXTENSIONS
                ),
            },
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(file_bytes) > MAXIMUM_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The resume must be smaller than 5 MB.",
        )

    extracted_text = extract_resume_text(
        filename=file.filename,
        file_bytes=file_bytes,
    )

    if not extracted_text:
        raise HTTPException(
            status_code=422,
            detail=(
                "No readable text was found. The resume may be "
                "scanned, image-based, empty, or corrupted."
            ),
        )

    return file_bytes, extracted_text


@app.get("/")
def home() -> dict:
    return {
        "message": "AI Resume Analyzer API is running.",
        "documentation": "/docs",
    }


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "AI Resume Analyzer API",
    }


@app.post("/api/resume/parse")
async def parse_resume(
    file: UploadFile = File(...),
) -> dict:
    """
    Upload a PDF or DOCX resume, extract its text,
    and return structured resume information.
    """

    try:
        file_bytes, extracted_text = (
            await read_and_validate_resume(file)
        )

        resume_information = extract_resume_information(
            extracted_text
        )

        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": len(file_bytes),
            "word_count": len(extracted_text.split()),
            "character_count": len(extracted_text),
            "parsed_data": resume_information,
            "text": extracted_text,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected error occurred: "
                f"{error}"
            ),
        ) from error

    finally:
        await file.close()


@app.post("/api/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
) -> dict:
    """
    Compare a resume against a job description using:

    - Skill matching
    - TF-IDF similarity
    - Transformer semantic similarity
    - Combined similarity
    - Rule-based ATS scoring
    """

    try:
        cleaned_job_description = job_description.strip()

        if len(cleaned_job_description) < 50:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The job description is too short. "
                    "Please provide at least 50 characters."
                ),
            )

        file_bytes, extracted_text = (
            await read_and_validate_resume(file)
        )

        parsed_data = extract_resume_information(
            extracted_text
        )

        skill_comparison = compare_resume_and_job_skills(
            resume_text=extracted_text,
            job_description=cleaned_job_description,
        )

        tfidf_similarity = calculate_tfidf_similarity(
            resume_text=extracted_text,
            job_description=cleaned_job_description,
        )

        semantic_similarity = calculate_semantic_similarity(
            resume_text=extracted_text,
            job_description=cleaned_job_description,
        )

        similarity_result = calculate_combined_similarity(
            tfidf_similarity=tfidf_similarity,
            semantic_similarity=semantic_similarity,
        )

        top_semantic_matches = calculate_chunk_matches(
            resume_text=extracted_text,
            job_description=cleaned_job_description,
            top_k=5,
        )

        ats_result = calculate_ats_score(
            resume_text=extracted_text,
            parsed_data=parsed_data,
            skill_comparison=skill_comparison,
            content_similarity=similarity_result[
                "combined_percentage"
            ],
        )

        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": len(file_bytes),
            "resume_statistics": {
                "word_count": len(
                    extracted_text.split()
                ),
                "character_count": len(
                    extracted_text
                ),
            },
            "candidate": parsed_data,
            "job_match": {
                "similarity": similarity_result,
                "skills": skill_comparison,
                "top_semantic_matches": (
                    top_semantic_matches
                ),
            },
            "ats": ats_result,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected error occurred: "
                f"{error}"
            ),
        ) from error

    finally:
        await file.close()