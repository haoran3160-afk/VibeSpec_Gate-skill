from pathlib import Path

from vibesec.core.project_intake import detect_profile
from vibesec.scanners.auth_data_scanner import AuthDataScanner


def test_auth_data_scanner_detects_missing_auth_and_rls():
    root = Path("tests/fixtures/vulnerable_next_supabase_app")
    findings = AuthDataScanner().scan(root, detect_profile(str(root)))
    titles = {f.title for f in findings}
    assert "API route may mutate data without server-side authentication" in titles
    assert "Supabase/Postgres table migration may be missing RLS" in titles
    assert "Firebase rules allow broad public read/write" in titles
