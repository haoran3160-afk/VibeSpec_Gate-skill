# Lite Login Security Optimization Plan

Date: 2026-07-09

## 1. Decision

VibeSpec Gate Lite should add a focused login-security review lane for vibe-coded products.

The goal is not to become a full dynamic attack scanner. The goal is to catch common launch-blocking authentication and account-safety mistakes that non-technical builders are likely to miss.

Target user question:

```text
Can hackers abuse my login, signup, verification-code, password-reset, or session flow to access user accounts or private data?
```

This lane should be part of the Lite launch gate because account takeover and weak login controls are directly tied to user-data exposure.

## 2. First-Principles Job

For a vibe coding user, login security is not an abstract security category. It answers four practical launch questions:

1. Can an attacker create or abuse accounts at scale?
2. Can an attacker guess, brute-force, intercept, replay, or reuse verification codes or reset tokens?
3. Can an attacker enumerate users or discover whether an email or phone number exists?
4. Can an attacker steal or misuse a session, token, cookie, or authorization state to access another user's data?

The Skill should translate these into plain launch decisions, bounded Agent fix tasks, and concrete retest steps.

## 3. Scope

### In Scope

Review these surfaces when present:

- login routes;
- signup routes;
- password reset routes;
- email-code, SMS-code, OTP, magic-link, and verification-code flows;
- CAPTCHA or bot-protection checks;
- rate limits and abuse controls;
- session cookies, JWTs, refresh tokens, and token storage;
- account enumeration behavior;
- admin login or privileged account flows;
- auth-provider integration configuration visible in project files;
- server-side authorization checks immediately after login.

### Out of Scope

Do not turn Lite into a live attack tool.

Out of scope unless explicitly authorized and safely scoped:

- brute-force testing against a real service;
- credential stuffing;
- CAPTCHA bypass instructions;
- phishing or social-engineering flows;
- exploit payloads;
- live OTP interception attempts;
- production account lockout testing;
- professional penetration-test, legal, or compliance claims.

## 4. Risk Taxonomy

The login-security lane should classify findings into these categories.

| Category | Common Evidence | Default Decision |
| --- | --- | --- |
| Missing server-side auth on private route | API route reads or writes user data without verified session | `BLOCK` |
| Broken ownership after login | Route accepts `user_id`, `email`, tenant id, or object id from request without checking owner | `BLOCK` |
| No OTP or reset-token expiry | Code or token has no TTL or expiry enforcement | `BLOCK` or `REVIEW` |
| No OTP or password-reset rate limit | Repeated code send or verify attempts are not throttled | `BLOCK` for production launch |
| Account enumeration | Login/reset/signup reveals whether an email or phone exists | `REVIEW` or `BLOCK` if paired with weak reset/OTP |
| Weak session cookie settings | Missing `HttpOnly`, unsafe storage, unclear `SameSite`, insecure token exposure | `REVIEW` or `BLOCK` depending on data sensitivity |
| Token leakage | JWT, session, reset token, OTP, or auth header is logged or exposed to frontend unnecessarily | `BLOCK` |
| CAPTCHA missing on high-abuse flows | Public signup, OTP-send, reset, invite, or contact flow has no abuse control | `REVIEW`; `BLOCK` when paired with no rate limit |
| Password policy absent or misleading | No minimum controls for password-based auth | `REVIEW` |
| Admin auth weak or shared with public flow | Admin routes lack separate protection, MFA note, or role checks | `BLOCK` |

## 5. Evidence To Gather

The Skill should ask the host Agent to inspect files and evidence such as:

- route handlers for login, signup, password reset, OTP send, OTP verify, magic link, and logout;
- middleware that attaches auth state;
- server components or API handlers that read private data;
- auth-provider configuration;
- database tables for users, sessions, verification tokens, reset tokens, and audit logs;
- Supabase, Firebase, NextAuth/Auth.js, Clerk, custom JWT, or custom session code;
- rate-limit middleware or storage;
- CAPTCHA provider calls or abuse-protection checks;
- logs, analytics, error-reporting, and debug output that may include tokens or codes;
- cookie configuration and frontend token storage.

If evidence is missing, the Skill should use `REVIEW`, not `PASS`.

## 6. Output Behavior

### `launch_decision.md`

Login-security findings should affect the launch gate like this:

- `BLOCK`: user-data access can be abused, OTP/reset/token can be brute-forced or replayed, secrets or auth tokens leak, admin access is unprotected, or private routes lack server-side auth.
- `REVIEW`: key auth-provider, rate-limit, CAPTCHA, cookie, or reset-token evidence is missing or ambiguous.
- `PASS_WITH_WARNINGS`: controls appear present, but production provider settings or abuse thresholds need confirmation.
- `PASS`: no material login-security launch risk was found in reviewed evidence.

`PASS` must always mean "in reviewed evidence", not "the auth system is secure".

### `top_security_risks.md`

For each login-security risk, include:

- beginner explanation;
- attacker impact;
- affected files or missing evidence;
- launch impact;
- human confirmation needed;
- false-positive or downgrade notes.

### `agent_fix_plan.md`

Agent tasks must stay narrow.

Allowed Agent tasks:

- add server-side auth checks to specific routes;
- add ownership checks using authenticated user id;
- add rate-limit middleware to named public auth endpoints;
- add OTP or reset-token expiry checks;
- stop logging OTPs, reset tokens, JWTs, cookies, or auth headers;
- set safer cookie options when compatible with the deployment;
- make error messages less enumerable;
- add tests for auth-required and owner-only behavior.

Human-confirmed tasks:

- choosing CAPTCHA provider;
- selecting rate-limit thresholds;
- changing identity provider;
- enabling MFA requirements;
- rotating leaked production secrets;
- changing account recovery policy;
- changing legal, retention, or user-notification policy.

Prohibited Agent tasks:

- disabling login checks to make tests pass;
- broadening database policies;
- printing full OTPs, reset tokens, sessions, JWTs, or secrets;
- adding insecure bypass flags;
- locking out production users without approval;
- testing brute-force behavior against a live service without explicit scope.

### `retest_checklist.md`

Retest steps should be concrete and safe:

- unauthenticated request to private route is rejected;
- user A cannot read or mutate user B's data;
- OTP verify rejects expired codes;
- OTP verify rejects repeated failed attempts;
- reset token cannot be reused after successful reset;
- public reset/signup response does not reveal account existence;
- sensitive tokens or codes are absent from logs;
- session cookie is not readable by client-side JavaScript when cookie sessions are used;
- rate limit returns a safe error after repeated requests;
- admin route rejects non-admin users.

## 7. Rule Additions

Add a small rule set rather than a broad auth rewrite.

Recommended first implementation cases:

1. `login_private_route_missing_auth`
   - Detect private data route without server-side auth.
   - Expected decision: `BLOCK`.

2. `login_ownership_check_missing`
   - Detect request-controlled `user_id`, `email`, tenant id, or account id used for private reads/writes.
   - Expected decision: `BLOCK`.

3. `otp_no_rate_limit`
   - Detect OTP send or verify route without rate-limit evidence.
   - Expected decision: `BLOCK` for production launch, `REVIEW` for prototype with no real users.

4. `password_reset_token_no_expiry`
   - Detect reset-token table or verification logic without expiry.
   - Expected decision: `BLOCK` or `REVIEW`.

5. `auth_token_logged`
   - Detect logging of OTP, reset token, JWT, cookie, authorization header, or session id.
   - Expected decision: `BLOCK`.

6. `account_enumeration`
   - Detect different public responses for existing versus non-existing account on login/reset/signup.
   - Expected decision: `REVIEW`; escalate to `BLOCK` when paired with weak OTP/reset controls.

7. `captcha_or_abuse_control_missing`
   - Detect high-abuse public auth flow with no CAPTCHA, rate limit, invite gate, or provider-level protection evidence.
   - Expected decision: `REVIEW`.

8. `admin_route_weak_auth`
   - Detect admin route without role check, separate guard, or provider-side role evidence.
   - Expected decision: `BLOCK`.

## 8. Validation Matrix Expansion

Add at least these fixtures or synthetic cases:

| Case | Expected Decision | Purpose |
| --- | --- | --- |
| Login private API without auth | `BLOCK` | Confirms missing auth blocks launch |
| Password reset token without expiry | `BLOCK` or `REVIEW` | Confirms token lifecycle reasoning |
| OTP verify without rate limit | `BLOCK` | Confirms abuse-control reasoning |
| Reset endpoint enumerates accounts | `REVIEW` | Confirms enumeration warning |
| JWT logged in server logs | `BLOCK` | Confirms token-leak handling |
| Admin route lacks role check | `BLOCK` | Confirms privileged-flow judgment |
| Auth provider used but config missing | `REVIEW` | Confirms missing-evidence behavior |
| Clean provider-backed auth with ownership checks | `PASS_WITH_WARNINGS` or `PASS` | Confirms no unsupported block |

## 9. User-Facing Wording

Use plain language:

```text
Your login flow may let attackers keep trying codes until one works.
This can lead to account takeover or user-data access.
Do not launch until the verify endpoint has rate limiting and code expiry.
```

Avoid expert-only wording as the first explanation:

```text
Credential stuffing, OTP brute force, replay, enumeration, and session fixation risks are present.
```

Technical details can appear after the beginner explanation.

## 10. Acceptance Gates

This optimization is ready when:

1. The Skill explicitly asks for login, signup, reset, OTP, CAPTCHA, rate-limit, token, and session evidence.
2. The Lite output can mark weak login flows as `BLOCK` or `REVIEW`.
3. Agent fix tasks are concrete and do not invite blind identity-provider or production-account changes.
4. Retest steps verify the actual auth risk, not just "rerun tests".
5. The validation matrix includes at least six login-security cases.
6. Clean provider-backed auth is not incorrectly blocked when evidence supports auth, ownership, and abuse controls.
7. Documentation still says the result is not certification, penetration testing, legal review, or compliance attestation.

## 11. Implementation Order

Recommended order:

```text
1. Update SKILL.md evidence gathering and risk taxonomy.
2. Add login-security fixtures or synthetic matrix cases.
3. Add rule/output expectations for OTP, reset, session, enumeration, and admin auth.
4. Update Lite output wording and retest templates.
5. Add tests for no blind edits, no secret/token printing, and missing-evidence REVIEW.
6. Run RC hardening evidence again.
7. Re-run simulated and then real usability checks with vibe coding users.
```

Do not start with live dynamic scanning. Static review plus evidence-driven Agent reasoning is safer and enough for the Lite lane.

## 12. Adversarial Review

### Finding 1: CAPTCHA is not the real root control

CAPTCHA can reduce automation, but it is not a substitute for server-side auth, rate limiting, token expiry, ownership checks, or provider-side abuse controls.

Resolution: Treat CAPTCHA as one possible abuse-control signal. Do not require CAPTCHA when an equivalent provider, invite gate, risk engine, or strong rate-limit design is visible.

### Finding 2: OTP guidance can accidentally teach brute-force thinking

Detailed attack steps or payloads would violate the Skill's safety boundary.

Resolution: Explain risk in plain language, but keep retest steps safe and non-destructive. Do not provide brute-force scripts, bypass instructions, or live attack guidance.

### Finding 3: Missing evidence can cause overblocking

Provider-backed auth may be secure even when repository files do not show all production settings.

Resolution: Use `REVIEW` for missing provider evidence unless local code clearly creates a launch blocker. Ask for human confirmation instead of guessing.

### Finding 4: PASS remains dangerous for non-technical users

Users may interpret a login-security `PASS` as an absolute guarantee.

Resolution: Keep `PASS` wording evidence-scoped and include the non-certification boundary in every release note and Lite output.

### Finding 5: Agent fixes can lock out users or weaken auth

Identity-provider, MFA, CAPTCHA, and rate-limit changes can break production flows.

Resolution: Mark provider choices, thresholds, MFA rollout, secret rotation, and account recovery policy as human-confirmed decisions. Agent tasks should only implement bounded code changes after confirmation.

## 13. Final Recommendation

Proceed with this optimization as the next targeted Lite security lane.

This is a high-fit extension because it directly matches the user's product vision: protect vibe-coded products from account takeover, verification-code abuse, token leakage, and user-data exposure before launch.

The implementation should remain narrow, evidence-driven, and safe-by-default. It should improve launch-blocking judgment without turning VibeSpec Gate Lite into a live offensive scanner.
