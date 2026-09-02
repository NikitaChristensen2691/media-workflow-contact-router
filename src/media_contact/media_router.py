"""Business routing for questions about a media asset's journey."""

from __future__ import annotations

from enum import Enum
from html import escape
from typing import Protocol

from pydantic import BaseModel, EmailStr, Field


class WorkflowStage(str, Enum):
    INGESTION = "ingestion"
    PROCESSING = "processing"
    CREATOR_DELIVERY = "creator_delivery"


class MediaContact(BaseModel):
    submission_id: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    asset_id: str = Field(min_length=1, max_length=120)
    stage: WorkflowStage
    summary: str = Field(min_length=1, max_length=2000)


class RoutedContact(BaseModel):
    message_id: str
    routed_to: EmailStr
    stage: WorkflowStage


class EmailSender(Protocol):
    def send(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        idempotency_key: str,
    ) -> dict[str, object]:
        raise AssertionError("Protocol methods are supplied by the email sender")


STAGE_LABELS = {
    WorkflowStage.INGESTION: "Asset ingestion",
    WorkflowStage.PROCESSING: "Processing job",
    WorkflowStage.CREATOR_DELIVERY: "Creator delivery",
}


def route_contact(
    contact: MediaContact,
    *,
    team_inbox: str,
    sender: EmailSender,
) -> RoutedContact:
    """Turn one workflow contact into one traceable team notification."""
    label = STAGE_LABELS[contact.stage]
    subject = f"[{label}] {contact.asset_id} - contact from {contact.name}"
    html = (
        f"<h1>{escape(label)} question</h1>"
        f"<p><strong>Asset:</strong> {escape(contact.asset_id)}</p>"
        f"<p><strong>From:</strong> {escape(contact.name)} "
        f"&lt;{escape(str(contact.email))}&gt;</p>"
        f"<p>{escape(contact.summary)}</p>"
    )
    result = sender.send(
        to=team_inbox,
        subject=subject,
        html=html,
        idempotency_key=contact.submission_id,
    )
    return RoutedContact(
        message_id=str(result["message_id"]),
        routed_to=team_inbox,
        stage=contact.stage,
    )
