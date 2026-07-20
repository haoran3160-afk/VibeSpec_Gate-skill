# Current Candidate Activation Audit

This audit used fresh Codex desktop subagents with the current VibeSpec Gate Skill attached and isolated read-only fixture copies. The raw case prompt and a transport-level fixture-path attachment were supplied separately. Expected decisions and scorer rules were withheld.

The audit did not establish reliable Skill activation. Two tasks explicitly reported that `$vibespec-gate` was unavailable despite the attachment, and one task returned the non-canonical decision `BLOCKED` without the required output sections. These failures are retained under `attempts/` and keep behavior and release readiness at `FAIL`.

Parent-observed fixture hashes were unchanged. The host still exposed no operation-level write telemetry, so write safety remains `PENDING`. This is simulated-user evidence, not independent user validation or trusted host provenance.
