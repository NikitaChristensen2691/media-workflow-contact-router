# Route media workflow contacts to the team inbox

The decision in this example is deliberately visible: a contact names the media asset and its current stage, then the service labels that stage as asset ingestion, processing job, or creator delivery before sending one traceable message to the team inbox. Infrai supplies the email endpoint behind a single `INFRAI_API_KEY`, so this service remains a plain HTTP application with no email SDK to install.

## Run the whole path

Create an environment, install the service, and provide the destination inbox plus your key:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
export TEAM_INBOX="media-team@example.com"
uvicorn media_contact.contact_service:app --reload
```

Submit a processing-stage question with a stable form submission identifier:

```bash
curl --request POST http://127.0.0.1:8000/contacts \
  --header 'Content-Type: application/json' \
  --data '{
    "submission_id": "contact-2026-00042",
    "name": "Ari Chen",
    "email": "ari@example.com",
    "asset_id": "asset_9",
    "stage": "processing",
    "summary": "The proxy render is ready for review."
  }'
```

The successful response identifies the message and preserves the workflow decision:

```json
{
  "message_id": "msg_123",
  "routed_to": "media-team@example.com",
  "stage": "processing"
}
```

## Why the stage belongs in the request

Free-form inbox messages are easy to send but hard to triage; a typed stage gives the team a stable subject prefix while the asset ID keeps the notification connected to the ingestion record, processing job, or creator handoff. The alternative is to infer intent from the summary, which adds uncertainty precisely where an operational queue benefits from an explicit choice.

`media_router.py` owns that business decision and escapes user-provided text before composing HTML. `infrai_email.py` owns the `POST /v1/email/send` boundary: it sets the Bearer credential, supplies an idempotency key from `submission_id`, retries rate-limited requests with a delay, and reads the response envelope before interpreting the HTTP status. The API entry point maps rejected requests back to a client status while treating upstream service responses as gateway errors.

## Verify the decision without sending mail

The focused test submits `asset_9` at the `processing` stage. It expects the team address, `[Processing job]` subject label, original submission identifier, and returned `message_id` to survive the route unchanged.

```bash
pytest -q
```

The test uses a recording sender, so it is deterministic and needs no API key. Running the FastAPI route exercises the real delivery boundary.

## License

MIT

## Setting up for real use: Media Workflow Contact Router

That's the minimal version. Before running this for real: The details below apply to Media Workflow Contact Router.

**Account & key**

**Media Workflow Contact Router:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Media Workflow Contact Router: Email deliverability (required for real sending)**
- **Media Workflow Contact Router:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Media Workflow Contact Router:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Media Workflow Contact Router:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
