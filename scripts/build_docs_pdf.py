from __future__ import annotations

import html as html_lib
import logging
import re
import subprocess
from datetime import date
from pathlib import Path

import markdown
import pdfplumber
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

BASE_DIR = Path(__file__).resolve().parents[1]
PDF_DIR = BASE_DIR / "docs" / "pdf"
CSS_PATH = PDF_DIR / "style.css"
PDF_PATH = PDF_DIR / "emporio-musica-documentation-bilingual.pdf"
TEMP_HTML = Path("/tmp/emporio-musica-documentation-bilingual.html")
CHROME = Path(
    "/Users/itouch/Library/Caches/ms-playwright/chromium-1208/"
    "chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
)
REPO_URL = "https://github.com/afsjr/store_music"
MAX_BYTES = 100 * 1024 * 1024

logging.getLogger("pypdf").setLevel(logging.ERROR)
logging.getLogger("pdfminer").setLevel(logging.ERROR)

LANGUAGES = [
    {
        "code": "pt",
        "part": "Parte I — Português",
        "label": "Português",
        "README": BASE_DIR / "README.md",
        "docs": [
            ("Relatório de Qualidade dos Dados", BASE_DIR / "docs/data_quality_report.md"),
            ("Benchmark de Latência — DeepSeek vs OpenAI", BASE_DIR / "docs/llm_benchmark.md"),
            ("Resumo do Índice de Políticas", BASE_DIR / "docs/policy_index_summary.md"),
        ],
        "examples": sorted((BASE_DIR / "examples").glob("*.md")),
        "appendix": "Apêndice A — Exemplos de interação",
        "diagram": BASE_DIR / "docs/diagrams/architecture-pt.svg",
    },
    {
        "code": "en",
        "part": "Part II — English",
        "label": "English",
        "README": BASE_DIR / "docs/i18n/en/README.md",
        "docs": [
            (
                "Data Quality Report",
                BASE_DIR / "docs/i18n/en/data_quality_report.md",
            ),
            (
                "Latency Benchmark — DeepSeek vs OpenAI",
                BASE_DIR / "docs/i18n/en/llm_benchmark.md",
            ),
            (
                "Policy Index Summary",
                BASE_DIR / "docs/i18n/en/policy_index_summary.md",
            ),
        ],
        "examples": sorted((BASE_DIR / "docs/i18n/en/examples").glob("*.md")),
        "appendix": "Appendix B — Interaction examples",
        "diagram": BASE_DIR / "docs/diagrams/architecture-en.svg",
    },
]


def markdown_to_html(text: str, prefix: str) -> str:
    text = re.sub(r"(?m)^(?![-*]\s)(\S[^\n]*)\n(?=[-*]\s)", r"\1\n\n", text)
    converter = markdown.Markdown(extensions=["extra", "sane_lists", "toc"])
    body = converter.convert(text)
    body = re.sub(
        r'(<h[1-6] id=")([^"]+)(")',
        lambda match: f"{match.group(1)}{prefix}-{match.group(2)}{match.group(3)}",
        body,
    )
    body = re.sub(
        r'href="#([^"]+)"',
        lambda match: f'href="#{prefix}-{match.group(1)}"',
        body,
    )
    return body


def rewrite_links(body: str, language: str) -> str:
    def replace(match: re.Match[str]) -> str:
        href = match.group(1)
        if href.startswith(("http://", "https://", "#", "mailto:", "file:")):
            return match.group(0)
        target = href
        if language == "en":
            if target.startswith("docs/"):
                target = "docs/i18n/en/" + target[len("docs/") :]
            elif target.startswith("examples/"):
                target = "docs/i18n/en/" + target
        return f'href="{REPO_URL}/blob/main/{target}"'

    return re.sub(r'href="([^"]+)"', replace, body)


def replace_mermaid(body: str, diagram: Path, language: str) -> str:
    pattern = re.compile(r"<pre><code class=\"language-mermaid\">.*?</code></pre>", re.S)
    figure = (
        f'<figure class="diagram"><img src="{diagram.as_uri()}" '
        f'alt="Architecture diagram ({language})"></figure>'
    )
    return pattern.sub(figure, body)


def heading_links(body: str) -> list[tuple[str, str, str]]:
    links: list[tuple[str, str, str]] = []
    for level, anchor, title in re.findall(r'<h([12]) id="([^"]+)">(.*?)</h\1>', body, flags=re.S):
        text = html_lib.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        links.append((level, anchor, text))
    return links


def build_toc(entries: list[tuple[str, str, str]]) -> str:
    items = []
    for level, anchor, title in entries:
        css = "level-2" if level == "2" else "level-1"
        items.append(f'<li class="{css}"><a href="#{anchor}">{html_lib.escape(title)}</a></li>')
    return '<ul class="toc">' + "".join(items) + "</ul>"


def build_html() -> str:
    css = CSS_PATH.read_text(encoding="utf-8")
    commit = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], text=True, cwd=BASE_DIR
    ).strip()
    generated = date.today().isoformat()
    cover = f"""
    <section class="cover">
      <div class="eyebrow">Documentação técnica / Technical documentation</div>
      <h1>Empório da Música</h1>
      <h2>Agente de Atendimento · Customer Support Agent</h2>
      <p>Documentação bilíngue do projeto: README, qualidade dos dados, benchmark de LLM,
      índice de políticas, arquitetura e exemplos de interação.</p>
      <p>Bilingual project documentation: README, data quality, LLM benchmark, policy index,
      architecture, and interaction examples.</p>
      <div class="meta">
        <div><strong>Repositório:</strong> {REPO_URL}</div>
        <div><strong>Commit:</strong> {commit}</div>
        <div><strong>Gerado em / Generated on:</strong> {generated}</div>
        <div><strong>Idiomas / Languages:</strong> Português · English</div>
      </div>
    </section>
    """

    toc_entries: list[tuple[str, str, str]] = []
    parts: list[str] = []

    for language in LANGUAGES:
        code = language["code"]
        part_anchor = f"part-{code}"
        toc_entries.append(("1", part_anchor, language["part"]))
        part_chunks: list[str] = [
            f'<section class="part" id="{part_anchor}">',
            f'<div class="part-label">{html_lib.escape(language["part"])}</div>',
        ]

        readme_body = markdown_to_html(language["README"].read_text(encoding="utf-8"), f"{code}-0")
        readme_body = rewrite_links(readme_body, code)
        readme_body = replace_mermaid(readme_body, language["diagram"], code)
        readme_anchor = f"{code}-readme"
        part_chunks.append(
            f'<section class="document" id="{readme_anchor}">{readme_body}</section>'
        )
        toc_entries.append(("1", readme_anchor, language["README"].stem.upper()))
        for level, anchor, title in heading_links(readme_body):
            if level == "2":
                toc_entries.append(("2", anchor, title))

        for doc_index, (title, path) in enumerate(language["docs"], start=1):
            body = markdown_to_html(path.read_text(encoding="utf-8"), f"{code}-{doc_index}")
            body = rewrite_links(body, code)
            anchor = f"{code}-doc-{doc_index}"
            part_chunks.append(f'<section class="document" id="{anchor}">{body}</section>')
            toc_entries.append(("1", anchor, title))

        appendix_anchor = f"{code}-appendix"
        toc_entries.append(("1", appendix_anchor, language["appendix"]))
        appendix_parts = [
            f'<section class="document" id="{appendix_anchor}">',
            f'<h1 class="appendix-title">{html_lib.escape(language["appendix"])}</h1>',
        ]
        for example_index, example_path in enumerate(language["examples"], start=1):
            example_body = markdown_to_html(
                example_path.read_text(encoding="utf-8"), f"{code}-example-{example_index}"
            )
            example_body = re.sub(
                r"<h1([^>]*)>(.*?)</h1>", r"<h2\1>\2</h2>", example_body, count=1, flags=re.S
            )
            appendix_parts.append(f'<section class="example">{example_body}</section>')
        appendix_parts.append("</section>")
        part_chunks.extend(appendix_parts)
        part_chunks.append("</section>")
        parts.append("".join(part_chunks))

    toc = build_toc(toc_entries)
    toc_html = f'<section class="toc-page"><h1>Sumário / Table of contents</h1>{toc}</section>'
    body = cover + toc_html + "".join(parts)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Empório da Música — Bilingual Documentation</title>
  <style>{css}</style>
</head>
<body>{body}</body>
</html>"""


def add_metadata_and_outline(pdf_path: Path, outline: list[tuple[str, str]]) -> None:
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata(
        {
            "/Title": "Empório da Música — Bilingual Documentation",
            "/Author": "Empório da Música project",
            "/Subject": "Bilingual technical documentation",
            "/Creator": "scripts/build_docs_pdf.py",
        }
    )
    text_pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_pages.append(re.sub(r"\s+", " ", page.extract_text() or ""))

    for title, search in outline:
        page_index = next(
            (index for index, text in enumerate(text_pages) if search in text),
            0,
        )
        writer.add_outline_item(title, page_index)

    temp = pdf_path.with_suffix(".tmp.pdf")
    with temp.open("wb") as handle:
        writer.write(handle)
    temp.replace(pdf_path)


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    html = build_html()
    TEMP_HTML.write_text(html, encoding="utf-8")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(CHROME),
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page()
        page.goto(TEMP_HTML.as_uri(), wait_until="load")
        page.wait_for_timeout(500)
        page.pdf(
            path=str(PDF_PATH),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=(
                '<div style="width:100%; padding:0 16mm; color:#5a6876; '
                'font-size:8px; display:flex; justify-content:space-between;">'
                "<span>Empório da Música — Documentation</span>"
                "<span>Bilingual edition</span></div>"
            ),
            footer_template=(
                '<div style="width:100%; padding:0 16mm; color:#5a6876; '
                'font-size:8px; display:flex; justify-content:space-between;">'
                f"<span>{REPO_URL}</span>"
                '<span>Page <span class="pageNumber"></span> of '
                '<span class="totalPages"></span></span></div>'
            ),
            margin={"top": "20mm", "bottom": "20mm", "left": "16mm", "right": "16mm"},
            prefer_css_page_size=True,
        )
        browser.close()

    add_metadata_and_outline(
        PDF_PATH,
        [
            ("Parte I — Português", "Parte I — Português"),
            ("README (PT)", "Empório da Música — Agente de Atendimento"),
            ("Relatório de Qualidade dos Dados", "Relatório de Qualidade dos Dados"),
            ("Benchmark de Latência", "Benchmark de Latência"),
            ("Resumo do Índice de Políticas", "Resumo do Índice de Políticas"),
            ("Apêndice A — Exemplos de interação", "Apêndice A — Exemplos de interação"),
            ("Part II — English", "Part II — English"),
            ("README (EN)", "Empório da Música — Customer Support Agent"),
            ("Data Quality Report", "Data Quality Report"),
            ("Latency Benchmark", "Latency Benchmark"),
            ("Policy Index Summary", "Policy Index Summary"),
            ("Appendix B — Interaction examples", "Appendix B — Interaction examples"),
        ],
    )

    size = PDF_PATH.stat().st_size
    if size > MAX_BYTES:
        raise SystemExit(f"PDF exceeds 100 MB: {size} bytes")
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Generated: {PDF_PATH}")
        print(f"Pages: {len(pdf.pages)}")
        print(f"Size: {size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
