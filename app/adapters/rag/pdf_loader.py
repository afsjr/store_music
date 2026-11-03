from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pdfplumber

from app.domain.models import PolicyChunk

HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$")
NOISE_PREFIXES = (
    "Empório da Música Manual de Políticas",
    "Empório da Música — Sua música começa aqui.",
)


def normalize_text(value: str) -> str:
    text = (value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Página ") or line.startswith("Page "):
            continue
        if any(line.startswith(prefix) for prefix in NOISE_PREFIXES):
            continue
        lines.append(line)
    return lines


def _split_long_chunk(
    section: str, title: str, page: int, content: str, max_chars: int = 1600
) -> list[PolicyChunk]:
    content = re.sub(r"\s+", " ", content).strip()
    if not content:
        return []
    if len(content) <= max_chars:
        return [
            PolicyChunk(
                chunk_id=f"{section}-{page}-1",
                section=section,
                page=page,
                content=content,
                title=title,
            )
        ]
    paragraphs = re.split(r"(?<=[.!?])\s+", content)
    chunks: list[PolicyChunk] = []
    buffer = ""
    index = 1
    for paragraph in paragraphs:
        candidate = f"{buffer} {paragraph}".strip()
        if buffer and len(candidate) > max_chars:
            chunks.append(
                PolicyChunk(
                    chunk_id=f"{section}-{page}-{index}",
                    section=section,
                    page=page,
                    content=buffer.strip(),
                    title=title,
                )
            )
            index += 1
            buffer = paragraph
        else:
            buffer = candidate
    if buffer:
        chunks.append(
            PolicyChunk(
                chunk_id=f"{section}-{page}-{index}",
                section=section,
                page=page,
                content=buffer.strip(),
                title=title,
            )
        )
    return chunks


def load_policy_chunks(
    pdf_path: str | Path,
    cache_path: str | Path | None = None,
    use_cache: bool = True,
) -> list[PolicyChunk]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Manual de políticas não encontrado: {path}")

    cache = Path(cache_path) if cache_path else None
    if cache and use_cache and cache.exists():
        try:
            raw = json.loads(cache.read_text(encoding="utf-8"))
            return [PolicyChunk(**item) for item in raw]
        except (ValueError, TypeError, json.JSONDecodeError):
            pass

    chunks: list[PolicyChunk] = []
    current_section = "0"
    current_title = "Capa e dados da empresa"
    current_page = 1
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        if buffer:
            chunks.extend(
                _split_long_chunk(
                    current_section,
                    current_title,
                    current_page,
                    " ".join(buffer),
                )
            )
        buffer = []

    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            lines = _clean_lines(text)
            if not lines:
                continue
            for line in lines:
                match = HEADING_RE.match(line)
                if match and len(line) < 140:
                    flush()
                    current_section = match.group(1)
                    current_title = match.group(2).strip()
                    current_page = page_number
                    buffer.append(line)
                else:
                    buffer.append(line)
        flush()
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(
                [chunk.model_dump(mode="json") for chunk in chunks],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return chunks


def sections_summary(chunks: list[PolicyChunk]) -> dict[str, dict]:
    summary: dict[str, dict] = {}
    for chunk in chunks:
        item = summary.setdefault(
            chunk.section,
            {"title": chunk.title, "page": chunk.page, "chunks": 0, "chars": 0},
        )
        item["chunks"] += 1
        item["chars"] += len(chunk.content)
    return summary
