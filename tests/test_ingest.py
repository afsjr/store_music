from __future__ import annotations

from pathlib import Path

from scripts.ingest import clean_frames, counts_of, load_frames, validate_data, write_report

DATA_DIR = Path(__file__).resolve().parents[1] / "emporio_musica" / "data"


def test_counts_match_source_files():
    frames = clean_frames(load_frames(DATA_DIR))
    counts = counts_of(frames)
    assert counts == {
        "categories": 9,
        "products": 65,
        "customers": 50,
        "orders": 20,
        "order_items": 22,
        "promotions": 25,
    }


def test_no_critical_validation_issues():
    frames = clean_frames(load_frames(DATA_DIR))
    issues = validate_data(frames)
    critical = [issue for issue in issues if issue["severity"] == "critico"]
    assert critical == []


def test_known_data_quality_warnings():
    frames = clean_frames(load_frames(DATA_DIR))
    issues = validate_data(frames)
    categories = {issue["category"] for issue in issues}
    assert "duplicidade" in categories
    assert "total" in categories
    assert "estoque" in categories


def test_report_is_written(tmp_path):
    frames = clean_frames(load_frames(DATA_DIR))
    issues = validate_data(frames)
    report = tmp_path / "report.md"
    write_report(counts_of(frames), issues, report, DATA_DIR)
    content = report.read_text(encoding="utf-8")
    assert "# Relatório de Qualidade dos Dados" in content
    assert "| products | 65 |" in content
