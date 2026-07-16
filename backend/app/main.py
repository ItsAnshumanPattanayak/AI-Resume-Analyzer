import logging
from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware

from app.advisor import analyze_resume_quality
from app.ats import calculate_ats_score
from app.error_handlers import (
    register_exception_handlers,
)
from app.extractor import extract_resume_information
from app.logging_config import configure_logging
from app.parser import (
    SUPPORTED_EXTENSIONS,
    extract_resume_text,
)
from app.recommender import recommend_job_roles
from app.semantic import (
    calculate_chunk_matches,
    calculate_semantic_similarity,
)
from app.similarity import (
    calculate_combined_similarity,
    calculate_tfidf_similarity,
)
from app.skills import compare_resume_and_job_skills


configure_logging()

logger = logging.getLogger(__name__)


app = FastAPI(
    title="AI Resume Analyzer API",
    description=(
        "Backend API for parsing resumes, calculating ATS scores, "
        "matching job descriptions, recommending job roles, "
        "and generating resume improvement suggestions."
    ),
    version="1.2.0",
)


register_exception_handlers(app)


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
        A tuple containing:
        - Original file bytes
        - Extracted resume text
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file does not have "
                "a filename."
            ),
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail={
                "message": (
                    "Unsupported resume format."
                ),
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
            detail=(
                "The resume must be smaller "
                "than 5 MB."
            ),
        )

    extracted_text = extract_resume_text(
        filename=file.filename,
        file_bytes=file_bytes,
    )

    if not extracted_text:
        raise HTTPException(
            status_code=422,
            detail=(
                "No readable text was found. "
                "The resume may be scanned, "
                "image-based, empty or corrupted."
            ),
        )

    return file_bytes, extracted_text


@app.get("/")
def home() -> dict:
    """
    Root API endpoint.
    """

    return {
        "message": (
            "AI Resume Analyzer API is running."
        ),
        "documentation": "/docs",
        "version": "1.2.0",
    }


@app.get("/health")
def health_check() -> dict:
    """
    Check whether the backend is running.
    """

    return {
        "status": "healthy",
        "service": "AI Resume Analyzer API",
        "version": "1.2.0",
    }


@app.post("/api/resume/parse")
async def parse_resume(
    file: UploadFile = File(...),
) -> dict:
    """
    Parse a PDF or DOCX resume and return
    structured candidate information.
    """

    try:
        logger.info(
            "Parsing resume: %s",
            file.filename,
        )

        file_bytes, extracted_text = (
            await read_and_validate_resume(file)
        )

        resume_information = (
            extract_resume_information(
                extracted_text
            )
        )

        logger.info(
            "Resume parsed successfully: %s",
            file.filename,
        )

        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": len(
                file_bytes
            ),
            "word_count": len(
                extracted_text.split()
            ),
            "character_count": len(
                extracted_text
            ),
            "parsed_data": resume_information,
            "text": extracted_text,
        }

    finally:
        await file.close()


@app.post("/api/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
) -> dict:
    """
    Run complete resume-versus-job analysis.
    """

    try:
        cleaned_job_description = (
            job_description.strip()
        )

        if len(cleaned_job_description) < 50:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The job description is too short. "
                    "Please provide at least 50 characters."
                ),
            )

        logger.info(
            "Starting full resume analysis: %s",
            file.filename,
        )

        file_bytes, extracted_text = (
            await read_and_validate_resume(file)
        )

        parsed_data = (
            extract_resume_information(
                extracted_text
            )
        )

        skill_comparison = (
            compare_resume_and_job_skills(
                resume_text=extracted_text,
                job_description=(
                    cleaned_job_description
                ),
            )
        )

        tfidf_similarity = (
            calculate_tfidf_similarity(
                resume_text=extracted_text,
                job_description=(
                    cleaned_job_description
                ),
            )
        )

        semantic_similarity = (
            calculate_semantic_similarity(
                resume_text=extracted_text,
                job_description=(
                    cleaned_job_description
                ),
            )
        )

        similarity_result = (
            calculate_combined_similarity(
                tfidf_similarity=(
                    tfidf_similarity
                ),
                semantic_similarity=(
                    semantic_similarity
                ),
            )
        )

        top_semantic_matches = (
            calculate_chunk_matches(
                resume_text=extracted_text,
                job_description=(
                    cleaned_job_description
                ),
                top_k=5,
            )
        )

        role_recommendations = (
            recommend_job_roles(
                resume_text=extracted_text,
                top_n=5,
            )
        )

        resume_quality = (
            analyze_resume_quality(
                resume_text=extracted_text,
                parsed_data=parsed_data,
                skill_comparison=(
                    skill_comparison
                ),
            )
        )

        ats_result = calculate_ats_score(
            resume_text=extracted_text,
            parsed_data=parsed_data,
            skill_comparison=(
                skill_comparison
            ),
            content_similarity=(
                similarity_result[
                    "combined_percentage"
                ]
            ),
        )

        logger.info(
            "Full analysis completed: %s | ATS: %s",
            file.filename,
            ats_result["overall_score"],
        )

        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": len(
                file_bytes
            ),
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
                "similarity": (
                    similarity_result
                ),
                "skills": skill_comparison,
                "top_semantic_matches": (
                    top_semantic_matches
                ),
            },
            "job_role_recommendations": (
                role_recommendations
            ),
            "resume_improvement": (
                resume_quality
            ),
            "ats": ats_result,
        }

    finally:
        await file.close()


@app.post("/api/resume/recommend-roles")
async def recommend_roles(
    file: UploadFile = File(...),
    top_n: int = Form(5),
) -> dict:
    """
    Recommend job roles using only the resume.
    """

    try:
        if not 1 <= top_n <= 10:
            raise HTTPException(
                status_code=400,
                detail=(
                    "top_n must be between "
                    "1 and 10."
                ),
            )

        logger.info(
            "Generating role recommendations: %s",
            file.filename,
        )

        file_bytes, extracted_text = (
            await read_and_validate_resume(file)
        )

        parsed_data = (
            extract_resume_information(
                extracted_text
            )
        )

        recommendations = (
            recommend_job_roles(
                resume_text=extracted_text,
                top_n=top_n,
            )
        )

        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": len(
                file_bytes
            ),
            "resume_statistics": {
                "word_count": len(
                    extracted_text.split()
                ),
                "character_count": len(
                    extracted_text
                ),
            },
            "candidate": {
                "name": parsed_data.get(
                    "name"
                ),
                "email": parsed_data.get(
                    "email"
                ),
                "phone": parsed_data.get(
                    "phone"
                ),
                "links": parsed_data.get(
                    "links"
                ),
                "skills": parsed_data.get(
                    "skills"
                ),
            },
            "recommendations": (
                recommendations
            ),
        }

    finally:
        await file.close()


@app.post("/api/resume/improve")
async def improve_resume(
    file: UploadFile = File(...),
) -> dict:
    """
    Analyze resume-writing quality without
    requiring a job description.
    """

    try:
        logger.info(
            "Running resume improvement analysis: %s",
            file.filename,
        )

        file_bytes, extracted_text = (
            await read_and_validate_resume(file)
        )

        parsed_data = (
            extract_resume_information(
                extracted_text
            )
        )

        improvement_result = (
            analyze_resume_quality(
                resume_text=extracted_text,
                parsed_data=parsed_data,
            )
        )

        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": len(
                file_bytes
            ),
            "resume_statistics": {
                "word_count": len(
                    extracted_text.split()
                ),
                "character_count": len(
                    extracted_text
                ),
            },
            "candidate": {
                "name": parsed_data.get(
                    "name"
                ),
                "email": parsed_data.get(
                    "email"
                ),
                "phone": parsed_data.get(
                    "phone"
                ),
                "links": parsed_data.get(
                    "links"
                ),
                "skills": parsed_data.get(
                    "skills"
                ),
                "sections": parsed_data.get(
                    "sections"
                ),
            },
            "resume_improvement": (
                improvement_result
            ),
        }

    finally:
        await file.close()