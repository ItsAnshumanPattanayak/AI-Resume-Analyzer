import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

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
from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
)
from app.config import settings
from app.database import get_database_session
from app.error_handlers import (
    register_exception_handlers,
)
from app.extractor import (
    extract_resume_information,
)
from app.history import (
    create_analysis_record,
    delete_analysis_record,
    get_analysis_record,
    list_analysis_records,
)
from app.logging_config import configure_logging
from app.models import User
from app.parser import (
    SUPPORTED_EXTENSIONS,
    extract_resume_text,
)
from app.recommender import recommend_job_roles
from app.schemas import (
    AccessTokenResponse,
    AnalysisHistoryDetail,
    AnalysisHistoryItem,
    DeleteHistoryResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.semantic import (
    calculate_chunk_matches,
    calculate_semantic_similarity,
)
from app.similarity import (
    calculate_combined_similarity,
    calculate_tfidf_similarity,
)
from app.skills import (
    compare_resume_and_job_skills,
)
from app.users import create_user


configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    application: FastAPI,
):
    """
    Initialize application resources.

    Database schema creation and schema changes
    are managed through Alembic migrations.
    """

    logger.info(
        (
            "%s version %s started in %s mode."
        ),
        settings.app_name,
        settings.app_version,
        settings.app_environment,
    )

    yield

    logger.info(
        "%s shutting down.",
        settings.app_name,
    )


app = FastAPI(
    title=settings.app_name,
    description=(
        "Authenticated backend API for parsing resumes, "
        "calculating ATS scores, matching job descriptions, "
        "recommending job roles, generating resume improvement "
        "suggestions, and storing private user analysis history."
    ),
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)


register_exception_handlers(app)


cors_origin_regex = None

if settings.allow_localhost_origin_regex:
    cors_origin_regex = (
        r"^https?://"
        r"(localhost|127\.0\.0\.1)"
        r"(:\d+)?$"
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=(
        cors_origin_regex
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]

AuthenticatedUser = Annotated[
    User,
    Depends(get_current_user),
]


async def read_and_validate_resume(
    file: UploadFile,
) -> tuple[bytes, str]:
    """
    Validate an uploaded resume and extract its text.

    Returns:
        The original file bytes and extracted text.
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
            detail=(
                "The uploaded file is empty."
            ),
        )

    if (
        len(file_bytes)
        > settings.maximum_file_size_bytes
    ):
        raise HTTPException(
            status_code=413,
            detail=(
                "The resume must be smaller than "
                f"{settings.maximum_file_size_mb} MB."
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
    current_user: User,
    analysis_type: str,
    filename: str | None,
    result: dict,
) -> int:
    """
    Save an analysis under the authenticated user.
    """

    record = create_analysis_record(
        database_session,
        user_id=current_user.id,
        analysis_type=analysis_type,
        filename=filename or "resume",
        result_data=result,
    )

    logger.info(
        (
            "Analysis saved: ID=%s user_id=%s "
            "type=%s file=%s"
        ),
        record.id,
        current_user.id,
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
            f"{settings.app_name} is running."
        ),
        "documentation": "/docs",
        "version": settings.app_version,
        "environment": (
            settings.app_environment
        ),
    }


@app.get("/health")
def health_check() -> dict:
    """
    Check whether the backend is running.
    """

    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": (
            settings.app_environment
        ),
        "database": "connected",
        "authentication": "enabled",
    }


@app.post(
    "/api/auth/register",
    response_model=UserResponse,
    status_code=201,
)
def register_user(
    request: UserRegisterRequest,
    database_session: DatabaseSession,
) -> User:
    """
    Register a new application user.
    """

    cleaned_name = request.name.strip()

    if len(cleaned_name) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                "Name must contain at least "
                "2 non-space characters."
            ),
        )

    try:
        user = create_user(
            database_session,
            name=cleaned_name,
            email=str(request.email),
            password=request.password,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    logger.info(
        "New user registered: ID=%s",
        user.id,
    )

    return user


@app.post(
    "/api/auth/login",
    response_model=AccessTokenResponse,
)
def login_user(
    request: UserLoginRequest,
    database_session: DatabaseSession,
) -> AccessTokenResponse:
    """
    Authenticate a user and issue a JWT.
    """

    user = authenticate_user(
        database_session,
        email=str(request.email),
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Incorrect email or password."
            ),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    access_token = create_access_token(
        user.id
    )

    logger.info(
        "User logged in: ID=%s",
        user.id,
    )

    return AccessTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=(
            settings
            .access_token_expire_minutes
            * 60
        ),
        user=UserResponse.model_validate(
            user
        ),
    )


@app.get(
    "/api/auth/me",
    response_model=UserResponse,
)
def get_authenticated_user(
    current_user: AuthenticatedUser,
) -> User:
    """
    Return the authenticated user's profile.
    """

    return current_user


@app.post("/api/resume/parse")
async def parse_resume(
    current_user: AuthenticatedUser,
    database_session: DatabaseSession,
    file: UploadFile = File(...),
) -> dict:
    """
    Parse a resume and save the result privately.
    """

    try:
        logger.info(
            "Parsing resume for user %s: %s",
            current_user.id,
            file.filename,
        )

        file_bytes, extracted_text = (
            await read_and_validate_resume(
                file
            )
        )

        resume_information = (
            extract_resume_information(
                extracted_text
            )
        )

        result = {
            "success": True,
            "filename": file.filename,
            "content_type": (
                file.content_type
            ),
            "file_size_bytes": len(
                file_bytes
            ),
            "word_count": len(
                extracted_text.split()
            ),
            "character_count": len(
                extracted_text
            ),
            "parsed_data": (
                resume_information
            ),
            "text": extracted_text,
        }

        history_id = save_analysis_result(
            database_session,
            current_user=current_user,
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
    current_user: AuthenticatedUser,
    database_session: DatabaseSession,
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

        if (
            len(cleaned_job_description)
            < 50
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "The job description is too short. "
                    "Please provide at least 50 characters."
                ),
            )

        logger.info(
            (
                "Starting full resume analysis "
                "for user %s: %s"
            ),
            current_user.id,
            file.filename,
        )

        file_bytes, extracted_text = (
            await read_and_validate_resume(
                file
            )
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
            "content_type": (
                file.content_type
            ),
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
                "skills": (
                    skill_comparison
                ),
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
            current_user=current_user,
            analysis_type="analyze",
            filename=file.filename,
            result=result,
        )

        result["history_id"] = history_id

        logger.info(
            (
                "Full analysis completed: %s "
                "| user=%s | ATS=%s"
            ),
            file.filename,
            current_user.id,
            ats_result["overall_score"],
        )

        return result

    finally:
        await file.close()


@app.post(
    "/api/resume/recommend-roles"
)
async def recommend_roles(
    current_user: AuthenticatedUser,
    database_session: DatabaseSession,
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
            (
                "Generating role recommendations "
                "for user %s: %s"
            ),
            current_user.id,
            file.filename,
        )

        file_bytes, extracted_text = (
            await read_and_validate_resume(
                file
            )
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
            "content_type": (
                file.content_type
            ),
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
            current_user=current_user,
            analysis_type="roles",
            filename=file.filename,
            result=result,
        )

        result["history_id"] = history_id

        logger.info(
            (
                "Role recommendations completed: "
                "%s | user=%s"
            ),
            file.filename,
            current_user.id,
        )

        return result

    finally:
        await file.close()


@app.post("/api/resume/improve")
async def improve_resume(
    current_user: AuthenticatedUser,
    database_session: DatabaseSession,
    file: UploadFile = File(...),
) -> dict:
    """
    Analyze resume-writing quality.
    """

    try:
        logger.info(
            (
                "Running resume improvement "
                "analysis for user %s: %s"
            ),
            current_user.id,
            file.filename,
        )

        file_bytes, extracted_text = (
            await read_and_validate_resume(
                file
            )
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
            "content_type": (
                file.content_type
            ),
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
            current_user=current_user,
            analysis_type="improve",
            filename=file.filename,
            result=result,
        )

        result["history_id"] = history_id

        logger.info(
            (
                "Resume improvement completed: "
                "%s | user=%s"
            ),
            file.filename,
            current_user.id,
        )

        return result

    finally:
        await file.close()


@app.get(
    "/api/history",
    response_model=list[
        AnalysisHistoryItem
    ],
)
def get_history(
    current_user: AuthenticatedUser,
    database_session: DatabaseSession,
    limit: int = 20,
    offset: int = 0,
) -> list:
    """
    Return the authenticated user's reports.
    """

    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=400,
            detail=(
                "limit must be between "
                "1 and 100."
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
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@app.get(
    "/api/history/{record_id}",
    response_model=(
        AnalysisHistoryDetail
    ),
)
def get_history_detail(
    record_id: int,
    current_user: AuthenticatedUser,
    database_session: DatabaseSession,
):
    """
    Return one report owned by the user.
    """

    record = get_analysis_record(
        database_session,
        record_id=record_id,
        user_id=current_user.id,
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
    response_model=(
        DeleteHistoryResponse
    ),
)
def delete_history(
    record_id: int,
    current_user: AuthenticatedUser,
    database_session: DatabaseSession,
) -> DeleteHistoryResponse:
    """
    Delete one report owned by the user.
    """

    record = get_analysis_record(
        database_session,
        record_id=record_id,
        user_id=current_user.id,
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
        (
            "Analysis history deleted: "
            "ID=%s user=%s"
        ),
        record_id,
        current_user.id,
    )

    return DeleteHistoryResponse(
        success=True,
        deleted_id=record_id,
    )