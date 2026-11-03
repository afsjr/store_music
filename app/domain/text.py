from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def digits_only(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))
