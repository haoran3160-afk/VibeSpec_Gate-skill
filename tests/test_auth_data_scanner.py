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


def test_auth_data_scanner_detects_login_security_lane_cases(tmp_path):
    root = tmp_path / "login_app"
    (root / "app" / "api" / "otp").mkdir(parents=True)
    (root / "app" / "api" / "reset").mkdir(parents=True)
    (root / "app" / "api" / "login").mkdir(parents=True)
    (root / "app" / "api" / "admin").mkdir(parents=True)
    (root / "app" / "api" / "otp" / "route.ts").write_text(
        """
export async function POST(req) {
  const body = await req.json()
  return sendOtp(body.email)
}
""",
        encoding="utf-8",
    )
    (root / "app" / "api" / "reset" / "route.ts").write_text(
        """
export async function POST(req) {
  const token = await createPasswordResetToken(req.email)
  console.log("reset token", token)
  return Response.json({ ok: true })
}
""",
        encoding="utf-8",
    )
    (root / "app" / "api" / "login" / "route.ts").write_text(
        """
export async function POST(req) {
  if (!user) return Response.json({ error: "user not found" }, { status: 404 })
  return Response.json({ ok: true })
}
""",
        encoding="utf-8",
    )
    (root / "app" / "api" / "admin" / "route.ts").write_text(
        """
export async function POST(req) {
  const session = await auth()
  return deleteUser(req.query.id)
}
""",
        encoding="utf-8",
    )

    findings = AuthDataScanner().scan(root, detect_profile(str(root)))
    titles = {f.title for f in findings}

    assert "OTP or reset flow may lack rate limiting" in titles
    assert "Password reset token may lack expiry enforcement" in titles
    assert "Authentication token or verification code may be logged" in titles
    assert "Public auth response may enumerate accounts" in titles
    assert "Admin route may lack role enforcement" in titles
