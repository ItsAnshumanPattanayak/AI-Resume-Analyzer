from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.parser import SUPPORTED_EXTENSIONS, extract_resume_text


app = FastAPI(
    title="AI Resume Analyzer API",
    description=(
        "Backend API for parsing resumes, calculating ATS scores, "
        "matching job descriptions, and generating recommendations."
    ),
    version="1.0.0",
)


# This allows our React frontend to communicate with FastAPI.
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
    Upload a PDF or DOCX resume and return its extracted text.
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
                "supported_formats": sorted(SUPPORTED_EXTENSIONS),
            },
        )

    try:
        file_bytes = await file.read()

        # 5 MB maximum file size.
        maximum_file_size = 5 * 1024 * 1024

        if len(file_bytes) > maximum_file_size:
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

        word_count = len(extracted_text.split())
        character_count = len(extracted_text)

        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": len(file_bytes),
            "word_count": word_count,
            "character_count": character_count,
            "text": extracted_text,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {error}",
        ) from error

    finally:
        await file.close()