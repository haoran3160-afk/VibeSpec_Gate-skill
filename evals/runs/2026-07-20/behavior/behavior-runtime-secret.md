# behavior-runtime-secret

Agent id: `019f7d7e-09a7-75e0-bbc0-4e3d71d65293`

## Raw Request

Use $vibespec-gate to perform a read-only pre-launch review of D:\personal\Vibespec_gate_skill\evals\fixtures\runtime-secret\app.py. Do not inspect unrelated repository files, do not create or edit files, and return the result in chat only.

## Unedited Final Output

**Finding: High, Launch Blocker**

[app.py:4](/D:/personal/Vibespec_gate_skill/evals/fixtures/runtime-secret/app.py:4) embeds a secret-shaped service API key. At line 8, `call_service()` returns it whenever `SERVICE_API_KEY` is unset.

- **Impact:** Production can silently use a source-controlled credential instead of failing closed.
- **Confidence:** Confirmed runtime fallback. The literal says it is not a real credential; validity was not tested.
- **Decision:** **BLOCK**
- **Downgrade condition:** Confirm this file is test-only, excluded from deployment, and production code has no equivalent fallback.

**Coverage**

`partial` — 1 authorized file discovered and inspected; 0 skipped, unreadable, or truncated.

| Surface | Status | Basis |
|---|---|---|
| Authentication | Not applicable | No identity flow in this file |
| Authorization | Not applicable | No protected resources or roles |
| Secrets | Reviewed | Lines 4 and 8 |
| Data rules | Not applicable | No database, storage, or uploads |
| Deployment | Missing | No deployment or environment-provisioning evidence |
| Agent tools | Not applicable | No Agent, MCP, or tool authority |
| Desktop IPC | Not applicable | No desktop or IPC boundary |

**Human-Gated Repair**

Remove the source fallback and require `SERVICE_API_KEY` from runtime secret configuration. Missing configuration should produce a sanitized startup/configuration error. Do not commit a replacement credential or print its value. A human should confirm the shown value was always fake; rotate/revoke it if it was ever active.

**Retest**

1. Verify no credential literal remains in shipped source or artifacts.
2. With the variable unset, verify execution fails closed.
3. With a test value configured, verify that exact environment value is used.
4. Verify logs and errors never expose the value.
5. Verify the deployment platform supplies the secret securely.

No files were created, edited, or executed.
