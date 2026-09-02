from media_contact.media_router import MediaContact, WorkflowStage, route_contact


class RecordingSender:
    def __init__(self) -> None:
        self.sent: dict[str, str] = {}

    def send(self, **message: str) -> dict[str, object]:
        self.sent = message
        return {"message_id": "msg_123"}


def test_processing_question_is_labeled_and_routed_to_team_inbox() -> None:
    sender = RecordingSender()
    contact = MediaContact(
        submission_id="form-42-unique",
        name="Ari Chen",
        email="ari@example.com",
        asset_id="asset_9",
        stage=WorkflowStage.PROCESSING,
        summary="The proxy render is ready for review.",
    )

    result = route_contact(contact, team_inbox="media-team@example.com", sender=sender)

    assert result.message_id == "msg_123"
    assert result.routed_to == "media-team@example.com"
    assert sender.sent["to"] == "media-team@example.com"
    assert sender.sent["subject"] == "[Processing job] asset_9 - contact from Ari Chen"
    assert sender.sent["idempotency_key"] == "form-42-unique"
    assert "proxy render is ready" in sender.sent["html"]

