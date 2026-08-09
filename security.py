import hmac
import os
from typing import Annotated

from fastapi import Header, HTTPException, status


ANALYSIS_ACCESS_KEY = os.getenv("ANALYSIS_ACCESS_KEY", "")
CANDIDATES_ADMIN_KEY = os.getenv("CANDIDATES_ADMIN_KEY", "")


def require_analysis_access(
    x_analysis_key: Annotated[str | None, Header()] = None,
) -> None:
    """Protect analysis endpoints when a deployment access key is configured."""
    if not ANALYSIS_ACCESS_KEY:
        return

    if not x_analysis_key or not hmac.compare_digest(
        x_analysis_key,
        ANALYSIS_ACCESS_KEY,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid analysis access key.",
        )


def require_candidates_admin(
    x_admin_key: Annotated[str | None, Header()] = None,
) -> None:
    """Require an explicit admin key before returning candidate records."""
    if not CANDIDATES_ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The candidate dashboard is not configured.",
        )

    if not x_admin_key or not hmac.compare_digest(
        x_admin_key,
        CANDIDATES_ADMIN_KEY,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid dashboard access key.",
        )
