import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.advisor import analyze_resume_quality
from app.ats import calculate_ats_score
from app.database import (
    create_database_tables,
    get_database_session,
)
from app.error_handlers import register_exception_handlers
from app.extractor import extract_resume_information
from app.history import (
    create_analysis_record,
    delete_analysis_record,
    get_analysis_record,
    list_analysis_records,
)
from app.logging_config import configure_logging
from app.parser import (
    SUPPORTED_EXTENSIONS,
    extract_resume_text,
)
from app.recommender import recommend_job_roles
from app.schemas import (
    AnalysisHistoryDetail,
    AnalysisHistoryItem,
    DeleteHistoryResponse,
)
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


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    Initialize application resources during startup.
    """

    create_database_tables()

    logger.info(
        "Database tables initialized successfully."
    )

    yield

    logger.info(
        "AI Resume Analyzer API shutting down."
    )


app = FastAPI(
    title="AI Resume Analyzer API",
    description=(
        "Backend API for parsing resumes, calculating ATS scores, "
        "matching job descriptions, recommending job roles, "
        "generating resume improvement suggestions, and storing "
        "analysis history."
    ),
    version="1.3.0",
    lifespan=lifespan,
)


register_exception_handlers(app)


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"^https?://"
        r"(localhost|127\.0\.0\.1)"
        r"(:\d+)?$"
    ),
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


def save_analysis_result(
    database_session: Session,
    *,
    analysis_type: str,
    filename: str | None,
    result: dict,
) -> int:
    """
    Save an analysis response and return its history ID.
    """

    record = create_analysis_record(
        database_session,
        analysis_type=analysis_type,
        filename=filename or "resume",
        result_data=result,
    )

    logger.info(
        "Analysis saved to history: ID=%s type=%s file=%s",
        record.id,
        analysis_type,
        filename,
    )

    return record.id


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
        "version": "1.3.0",
    }


@app.get("/health")
def health_check() -> dict:
    """
    Check whether the backend is running.
    """

    return {
        "status": "healthy",
        "service": "AI Resume Analyzer API",
        "version": "1.3.0",
        "database": "connected",
    }


@app.post("/api/resume/parse")
async def parse_resume(
    file: UploadFile = File(...),
    database_session: Session = Depends(
        get_database_session
    ),
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

        result = {
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

        history_id = save_analysis_result(
            database_session,
            analysis_type="parse",
            filename=file.filename,
            result=result,
        )

        result["history_id"] = history_id

        logger.info(
            "Resume parsed successfully: %s",
            file.filename,
        )

        return result

    finally:
        await file.close()


@app.post("/api/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    database_session: Session = Depends(
        get_database_session
    ),
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

        result = {
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

        history_id = save_analysis_result(
            database_session,
            analysis_type="analyze",
            filename=file.filename,
            result=result,
        )

        result["history_id"] = history_id

        logger.info(
            "Full analysis completed: %s | ATS: %s",
            file.filename,
            ats_result["overall_score"],
        )

        return result

    finally:
        await file.close()


@app.post("/api/resume/recommend-roles")
async def recommend_roles(
    file: UploadFile = File(...),
    top_n: int = Form(5),
    database_session: Session = Depends(
        get_database_session
    ),
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

        result = {
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

        history_id = save_analysis_result(
            database_session,
            analysis_type="roles",
            filename=file.filename,
            result=result,
        )

        result["history_id"] = history_id

        logger.info(
            "Role recommendations completed: %s",
            file.filename,
        )

        return result

    finally:
        await file.close()


@app.post("/api/resume/improve")
async def improve_resume(
    file: UploadFile = File(...),
    database_session: Session = Depends(
        get_database_session
    ),
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

        result = {
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

        history_id = save_analysis_result(
            database_session,
            analysis_type="improve",
            filename=file.filename,
            result=result,
        )

        result["history_id"] = history_id

        logger.info(
            "Resume improvement analysis completed: %s",
            file.filename,
        )

        return result

    finally:
        await file.close()


@app.get(
    "/api/history",
    response_model=list[AnalysisHistoryItem],
)
def get_history(
    limit: int = 20,
    offset: int = 0,
    database_session: Session = Depends(
        get_database_session
    ),
) -> list[AnalysisHistoryItem]:
    """
    Return saved analysis summaries,
    ordered newest first.
    """

    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=400,
            detail=(
                "limit must be between 1 and 100."
            ),
        )

    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "offset cannot be negative."
            ),
        )

    return list_analysis_records(
        database_session,
        limit=limit,
        offset=offset,
    )


@app.get(
    "/api/history/{record_id}",
    response_model=AnalysisHistoryDetail,
)
def get_history_detail(
    record_id: int,
    database_session: Session = Depends(
        get_database_session
    ),
) -> AnalysisHistoryDetail:
    """
    Return one complete saved analysis report.
    """

    record = get_analysis_record(
        database_session,
        record_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Analysis record not found."
            ),
        )

    return record


@app.delete(
    "/api/history/{record_id}",
    response_model=DeleteHistoryResponse,
)
def delete_history(
    record_id: int,
    database_session: Session = Depends(
        get_database_session
    ),
) -> DeleteHistoryResponse:
    """
    Delete one saved analysis report.
    """

    record = get_analysis_record(
        database_session,
        record_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Analysis record not found."
            ),
        )

    delete_analysis_record(
        database_session,
        record,
    )

    logger.info(
        "Analysis history deleted: ID=%s",
        record_id,
    )

    return DeleteHistoryResponse(
        success=True,
        deleted_id=record_id,
    )