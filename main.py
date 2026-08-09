import asyncio
import logging
import os
import smtplib
from collections import deque
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Annotated

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
load_dotenv(BASE_DIR / ".env")

from agents_services import (  # noqa: E402
    RecruitmentAgent,
    analyze_audio_file,
    call_gemini_analyzer,
    load_criteria_from_csv,
    prepare_analysis_prompt,
    search_candidate_info,
)
from models import CandidateInput, CandidateRequest  # noqa: E402
from security import require_analysis_access, require_candidates_admin  # noqa: E402
from validator import OutputValidator  # noqa: E402


logger = logging.getLogger(__name__)

EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
STORE_CANDIDATES = os.getenv("STORE_CANDIDATES", "false").lower() == "true"
MAX_AUDIO_BYTES = 10 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "audio/x-m4a",
    "audio/x-wav",
}
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app = FastAPI(title="Unified HR Recruitment API - Hackathon")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Analysis-Key", "X-Admin-Key"],
)
app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

candidates_store: deque[dict] = deque(maxlen=100)
psychologist_agent = None
output_validator = OutputValidator()


def get_psychologist_agent() -> RecruitmentAgent:
    global psychologist_agent
    if psychologist_agent is None:
        psychologist_agent = RecruitmentAgent()
    return psychologist_agent


def get_criteria() -> list[str]:
    criteria = load_criteria_from_csv(str(BASE_DIR / "requirements.csv"))
    return criteria or ["ניסיון רלוונטי", "יכולת טכנית", "התאמה תרבותית"]


def validate_candidate_form(
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
) -> CandidateRequest:
    try:
        return CandidateRequest(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(include_input=False),
        ) from exc


async def finalize_analysis(
    candidate: CandidateRequest,
    social_profile: dict,
    interaction_profile: dict,
    background_tasks: BackgroundTasks,
) -> dict:
    full_name = f"{candidate.first_name} {candidate.last_name}"
    formatted_candidate = CandidateInput(
        social_profile=social_profile,
        interaction_profile=interaction_profile,
    )
    final_result = await get_psychologist_agent().run(formatted_candidate)

    if "dashboard_view" in final_result:
        final_result["dashboard_view"]["email"] = candidate.email
        final_result["dashboard_view"]["phone"] = candidate.phone

    validation_errors = output_validator.validate(final_result)
    response_data = {
        "success": True,
        "candidate_name": full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "analysis": final_result,
        "validation_warnings": validation_errors,
    }

    if STORE_CANDIDATES:
        candidates_store.append(response_data)

    if N8N_WEBHOOK_URL:
        await send_to_n8n(final_result)

    background_tasks.add_task(send_email_notification, response_data)
    return response_data


@app.get("/")
def serve_frontend() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "up and running", "system": "Unified Hackathon API v1.0"}


@app.get("/candidates", dependencies=[Depends(require_candidates_admin)])
def get_candidates() -> list[dict]:
    return list(candidates_store)


@app.post("/analyze", dependencies=[Depends(require_analysis_access)])
async def analyze_json(
    candidate: CandidateRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    try:
        full_name = f"{candidate.first_name} {candidate.last_name}"
        web_data = await search_candidate_info(
            candidate.first_name,
            candidate.last_name,
            candidate.email,
        )
        analysis_prompt = prepare_analysis_prompt(full_name, web_data, get_criteria())
        social_profile = await call_gemini_analyzer(analysis_prompt)
        interaction_profile = {
            "status": "skipped",
            "candidate": full_name,
            "analysis_result": {
                "summary": "לא סופק קובץ אודיו",
                "match_percentage": 0,
            },
        }

        return await finalize_analysis(
            candidate,
            social_profile,
            interaction_profile,
            background_tasks,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Candidate analysis failed.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Candidate analysis could not be completed.",
        ) from exc


@app.post("/analyze_complete", dependencies=[Depends(require_analysis_access)])
async def analyze_complete_candidate(
    background_tasks: BackgroundTasks,
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    email: Annotated[str, Form()] = "",
    phone: Annotated[str, Form()] = "",
    audio_file: UploadFile = File(...),
) -> dict:
    try:
        candidate = validate_candidate_form(first_name, last_name, email, phone)

        if audio_file.content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Upload a supported audio file.",
            )

        file_content = await audio_file.read(MAX_AUDIO_BYTES + 1)
        if len(file_content) > MAX_AUDIO_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Audio files are limited to 10 MB.",
            )

        full_name = f"{candidate.first_name} {candidate.last_name}"
        criteria = get_criteria()

        async def run_web_agent():
            web_data = await search_candidate_info(
                candidate.first_name,
                candidate.last_name,
                candidate.email,
            )
            prompt = prepare_analysis_prompt(full_name, web_data, criteria)
            return await call_gemini_analyzer(prompt)

        async def run_audio_agent():
            return await analyze_audio_file(
                file_content,
                audio_file.filename or "audio-upload",
                full_name,
            )

        social_profile, interaction_profile = await asyncio.gather(
            run_web_agent(),
            run_audio_agent(),
        )

        return await finalize_analysis(
            candidate,
            social_profile,
            interaction_profile,
            background_tasks,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Complete candidate analysis failed.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Candidate analysis could not be completed.",
        ) from exc
    finally:
        await audio_file.close()


async def send_to_n8n(data: dict) -> None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(N8N_WEBHOOK_URL, json=data)
            response.raise_for_status()
    except Exception:
        logger.exception("Unable to deliver the analysis webhook.")


def send_email_notification(data: dict) -> None:
    if not EMAIL_FROM or not EMAIL_PASSWORD or not EMAIL_TO:
        return

    try:
        analysis = data.get("analysis", {})
        dashboard = analysis.get("dashboard_view", {})
        details = analysis.get("interview_details", {})

        name = dashboard.get("full_name", data.get("candidate_name", ""))
        score = dashboard.get("match_percent", 0)
        candidate_status = dashboard.get("status", "")
        strengths = "\n".join(f"  - {item}" for item in details.get("strengths", []))
        weaknesses = "\n".join(f"  - {item}" for item in details.get("weaker_points", []))
        reasons = "\n".join(f"  - {item}" for item in details.get("score_reasons", []))

        body = (
            "שלום,\n\n"
            "התקבלה תוצאת ניתוח עבור מועמד חדש:\n\n"
            f"שם: {name}\n"
            f"אימייל: {data.get('email', '')}\n"
            f"טלפון: {data.get('phone', '')}\n"
            f"ציון התאמה: {score}/10 ({int(score * 10)}%)\n"
            f"סטטוס: {candidate_status}\n\n"
            f"נקודות חוזק:\n{strengths}\n\n"
            f"נקודות לשיפור:\n{weaknesses}\n\n"
            f"נימוקי ציון:\n{reasons}\n"
        )

        message = MIMEMultipart()
        message["From"] = EMAIL_FROM
        message["To"] = EMAIL_TO
        message["Subject"] = (
            f"מועמד חדש: {name} - ציון {int(score * 10)}% - {candidate_status}"
        )
        message.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(message)
    except Exception:
        logger.exception("Unable to send the candidate notification email.")


@app.get("/{full_path:path}")
async def spa_catchall(full_path: str) -> FileResponse:
    requested_file = (STATIC_DIR / full_path).resolve()
    if requested_file.is_relative_to(STATIC_DIR) and requested_file.is_file():
        return FileResponse(requested_file)
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
