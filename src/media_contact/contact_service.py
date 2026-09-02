"""Runnable HTTP entry point for the media contact workflow."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from .infrai_email import InfraiEmail, InfraiError
from .media_router import MediaContact, RoutedContact, route_contact

app = FastAPI(title="Media workflow contact router")


@app.post("/contacts", response_model=RoutedContact, status_code=202)
def submit_contact(contact: MediaContact) -> RoutedContact:
    team_inbox = os.environ.get("TEAM_INBOX")
    if not team_inbox:
        raise HTTPException(status_code=503, detail="TEAM_INBOX is not configured")

    try:
        return route_contact(
            contact,
            team_inbox=team_inbox,
            sender=InfraiEmail(),
        )
    except InfraiError as exc:
        status_code = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "message": str(exc.details.get("message", "Email rejected"))},
        ) from exc

