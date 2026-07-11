# Synthetic Lite Review Example

> **SYNTHETIC EXAMPLE - NOT A REAL SECURITY REVIEW**
>
> This document demonstrates the output contract only. Do not use it as a launch decision, audit result, compliance evidence, or proof that a project is secure. Generated evidence may contain sensitive context and must be manually inspected before sharing.

## Output Shape

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

## `launch_decision.md`

```text
Decision: BLOCK

Do not launch yet. A private orders route reads records by id without proving
that the caller is authenticated or owns the requested order.
```

## `top_security_risks.md`

```text
Risk: Missing server-side authentication and ownership enforcement
Evidence: app/api/orders/route.ts
Launch impact: An unauthenticated or cross-account caller may access private data.
Confidence: High for the reviewed route; deployment middleware was not present.
```

## `agent_fix_plan.md`

```text
Human confirmation: Confirm the intended user and admin ownership model.
Allowed scope: app/api/orders/route.ts and its focused tests.
Task: Require trusted server-side auth, derive user_id from the session, and
constrain reads and writes to that owner.
Prohibited: Do not trust user_id from request JSON or broaden admin access.
```

## `retest_checklist.md`

```text
- Unauthenticated requests are rejected.
- User A cannot read or mutate user B's order.
- Approved admin behavior is covered separately.
- Rerun the review and update the launch decision from new evidence.
```

The complete decision vocabulary is `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, and `PASS`. `PASS` means no material blocker was identified in reviewed evidence; it is not a security guarantee.
