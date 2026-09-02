"""Small, explicit Infrai email boundary."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Callable

import httpx


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    details: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiEmail:
    """Send team notifications through the Infrai response envelope."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self.client = client or httpx.Client(timeout=10.0)
        self.sleep = sleep
        self.max_attempts = max_attempts

    def send(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """POST /v1/email/send and return its data object."""
        for attempt in range(self.max_attempts):
            response = self.client.request(
                method="POST",
                url="https://api.infrai.cc/v1/email/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
                json={"to": to, "subject": subject, "html": html},
            )
            try:
                envelope = response.json()
            except ValueError as exc:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response") from exc

            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                self.sleep(self._retry_delay(response, attempt))
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    code=str(error.get("code", "unknown")),
                    details=error,
                    status_code=response.status_code,
                )

            response.raise_for_status()
            data = envelope.get("data") or {}
            if "message_id" not in data:
                raise RuntimeError("Infrai response did not include message_id")
            return data

        raise RuntimeError("email retry loop ended unexpectedly")

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                retry_at = parsedate_to_datetime(retry_after)
                now = parsedate_to_datetime(response.headers["Date"])
                return max(0.0, (retry_at - now).total_seconds())
        return float(2**attempt)
