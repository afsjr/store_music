from __future__ import annotations

import logging
import re
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level.upper())
        return
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def mask_phone(phone: str | None) -> str:
    if not phone:
        return "não informado"
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 4:
        return "****"
    return f"****{digits[-4:]}"


def mask_email(email: str | None) -> str:
    if not email:
        return "não informado"
    if "@" not in email:
        return "****"
    local, domain = email.split("@", 1)
    prefix = local[:1] if local else "*"
    return f"{prefix}***@{domain}"


def mask_pii(text: str) -> str:
    if not text:
        return text
    masked = re.sub(
        r"[\w.+-]+@[\w-]+\.[\w.-]+",
        lambda m: mask_email(m.group(0)),
        text,
    )
    masked = re.sub(
        r"\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}",
        lambda m: mask_phone(m.group(0)),
        masked,
    )
    return masked
