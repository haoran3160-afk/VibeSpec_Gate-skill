# behavior-empty-project

Agent id: `019f7ee7-bdae-7020-b61c-f791f49e9575`

Invocation: explicit `vibespec-gate` Skill attachment, fresh subagent, `fork_context=false`

Authorized isolated fixture: `test output/skill_eval_isolated/3580a3d/behavior-empty-project/fixture/empty-project.fixture.json`

## Raw Request

Use $vibespec-gate to review the provided empty project for launch readiness. Keep the review read-only and return the result in chat only.

## Unedited Final Output

**Launch Decision: REVIEW**

The supplied fixture confirms an empty project: no runtime code, configuration, deployment settings, or security controls are available to assess. This is insufficient evidence for launch readiness. It does not establish that the project is unsafe, but it cannot receive `PASS` or `PASS_WITH_WARNINGS`.

**Coverage**
```text
coverage_status: insufficient
files_discovered: 0
files_inspected: 0
files_skipped: 0
files_unreadable: 0
files_truncated: 0

surfaces:
  auth: missing
  authorization: missing
  secrets: missing
  data_rules: missing
  deployment: missing
  agent_tools: missing
  desktop_ipc: missing
```

Source: `empty-project.fixture.json:2-5`.

Launch stage, public exposure, sensitive-data handling, identity model, and use of Agents, MCP, tools, IPC, desktop APIs, local files, shell commands, email, payments, or databases are all unknown.

**Finding: Required launch evidence is absent**

- **Severity / impact:** `REVIEW`; launch approval must wait.
- **Evidence:** The authorized fixture reports zero discovered and inspected files.
- **Explanation:** There is nothing to verify for authentication, permissions, secret handling, data protection, deployment hardening, privileged tools, or desktop boundaries.
- **Confidence:** Confirmed that the provided evidence is empty; security posture requires manual review.
- **Recommended task:** Provide a populated, read-only project snapshot containing runtime code, manifests, security policies, deployment configuration, and applicable Agent or desktop boundaries, then rerun the gate.
- **Prohibited changes:** Do not implement controls, select identity or recovery policy, alter deployment settings, or suppress this finding without human approval.
- **Human confirmation required:** Confirm the launch environment, exposure, data sensitivity, identity design, and which privileged capabilities are in scope.
- **Retest:** Re-inventory the supplied project, cover all seven evidence surfaces, then test applicable unauthenticated, cross-user, privilege, secret-exposure, deployment, tool-authority, and IPC rejection paths non-destructively.
- **Downgrade condition:** This finding can be reconsidered only after complete project evidence is supplied. An intentionally empty project is still not independently launch-verifiable.

No files were modified.
