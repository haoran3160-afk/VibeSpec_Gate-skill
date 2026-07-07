from pathlib import Path

from vibesec.core.project_intake import detect_profile
from vibesec.scanners.secret_scanner import SecretScanner


def test_secret_scanner_masks_values():
    root = Path("tests/fixtures/vulnerable_next_supabase_app")
    findings = SecretScanner().scan(root, detect_profile(str(root)))
    assert any(f.severity == "P0" for f in findings)
    joined = "\n".join(f.evidence for f in findings)
    assert "sk-test-1234567890abcdef1234567890abcdef" not in joined
    assert "..." in joined
